"""Compare bounded user-movie windows with continuous native scheduled actor state.

Uses an already verified GenesisDebug recording, exact binary identity and held
inputs. No ROM edits, controller edits, GUI connection or external source writes.
Every contracted actor field persists between calls; shared terrain scratch and input/control
parameters are explicit environment inputs. This is not whole-frame emulation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import verify_executable
from genesis_actor_capture import BUILD_ID,COMPARE_FIELDS,be,block,actor_fields,terrain_fixture,save,require
from actor_cases import HANDLERS,CALLBACKS,case,decode_results
from terrain_cases import encode_cases

# Half-open completed-frame input-row intervals in the preserved 5298-frame
# user movie. Discovery used a separate, overflow-checked selected-PC survey.
WINDOWS=((700,1067),(3100,3200),(4360,4400))
MOVIE_SHA256='c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd'
INPUT_SHA256='34434f0aa0b1ebc7dbf4e464cd044ac52436b944bf6a01cdc24c811e1f6c3a88'


def recipe():
    return {'pcs':[0xf8fc,0xf900,0xf904,0xf906,0xfcb32]+CALLBACKS[1:]+HANDLERS[1:],
            'returns':False,'registers':True,'maxEvents':20000,
            'ranges':[{'label':l,'domain':'68K RAM','offset':o,'length':n}
                      for l,o,n in [('actor',0x1ab4,78),('control',0x690,112),('scratch',0x4442,4),('gate',0xf16,2),('sound',0xa9e,8)]]+
                     [{'label':'stack','domain':'68K RAM','register':'M68K A7','offset':0,'length':4}]}


def snapshot_fields(event,original_callback=None):
    a=block(event,'actor');scratch=block(event,'scratch')
    return (*actor_fields(a,original_callback),be(scratch,0),be(scratch,2))


def input_case(event):
    f=actor_fields(block(event,'actor'));control=block(event,'control');scratch=block(event,'scratch')
    values=dict(zip(COMPARE_FIELDS[:16],f))
    values.update(positive=be(control,0x5a),negative=be(control,0x5c),damping=be(control,0x66),
                  air_acc=be(control,0x60),contact=be(control,0x6a),gravity=be(control,0x6c),
                  ground_acc=be(control,0x5e),impulse=be(control,0x62),jump_delay=be(control,0x64),
                  jump=control[0x16],drop=control[0x17],up=control[0x1a],down=control[0x1b],
                  left=control[0x1c],right=control[0x1d],gate=be(block(event,'gate'),0),sx=be(scratch,0),sy=be(scratch,2))
    return case(**values)


def validate_trace(trace,start_frame,end_frame,*,action_callbacks=False,control_writes=()):
    require(trace['schemaVersion']==1 and trace['boundary']=='instruction-pre-execute','trace boundary/schema mismatch')
    require(type(trace['dropped']) is int and trace['dropped']==0 and trace['overflow'] is False and trace['error'] is None,'incomplete trace')
    events=trace['events'];require(0<len(events)<=20000,'trace extent invalid')
    require(all(a['sequence']<b['sequence'] for a,b in zip(events,events[1:])),'event order invalid')
    pairs=[];entry=present=dispatch=None;callbacks=[];handlers=[];sounds=[];callback_handlers=[];callback_sounds=[]
    for e in events:
        require(e['kind']=='entry','inferred returns not part of contract')
        require(start_frame<=e['frame']<end_frame,'event outside requested window')
        regs=e['registers'];pc=e['pc']
        # Hooks can also fire for other actors/sound clients. Preserve their
        # events in the artifact, but bind this comparison to the verified P1.
        if regs['M68K A6']!=0xffff1ab4:continue
        if pc==0xf8fc:
            require(entry is None,'nested scheduled actor entry');entry=e
            require(regs['M68K A5']==0xffff0690,'wrong control record')
            require(block(e,'actor')[0]&0x80,'inactive object reached active call')
            callbacks=[];handlers=[];sounds=[];callback_handlers=[];callback_sounds=[];present=dispatch=None
        elif entry is not None:
            require(e['frame']==entry['frame'],'pair/frame changed')
            # A7EC/A9B2 reload +4A themselves; on their allocation fallthrough
            # entry A5 still names the new object. All later phases restore it.
            if pc in (0xa7ec,0xa9b2):
                require(be(block(e,'actor'),0x4a,4)==entry['registers']['M68K A5'],'reversal control owner differs')
            else:require(regs['M68K A5']==entry['registers']['M68K A5'],'pair/frame changed')
            if pc in (0xf900,0xf904,0xf906):
                require(regs['M68K A7']==entry['registers']['M68K A7'],'dispatcher stack mismatch')
            # AA50 is both a callback and a movement initializer. Its later
            # handler/internal-callback hits are not a second presentation callback.
            if pc in CALLBACKS and not (pc==0xaa50 and (present is not None or callbacks)):
                require(present is None and not callbacks,'callback outside presentation phase')
                require(pc==be(block(entry,'actor'),0x1a,4),'callback selector mismatch')
                require(regs['M68K A7']==entry['registers']['M68K A7']-4 and be(block(e,'stack'),0,4)==0xf900,'callback tail-return mismatch')
                callbacks.append(e)
            elif pc==0xf900:
                require(present is None,'duplicate presentation return');present=e
                a=block(entry,'actor')
                fires=(a[0]&5)==5 and a[12]==1 and be(a,6)==be(a,14)
                require(len(callbacks)==int(fires),'missing or unexpected callback event')
            elif pc==0xf904:
                require(present is not None and dispatch is None,'handler before presentation return')
                require(all(block(e,l)==block(present,l) for l in ('actor','control','scratch','gate')),'state changed during handler selection')
                require(regs['M68K A0']==be(block(e,'actor'),0x16,4),'selected handler register mismatch');dispatch=e
            elif pc in HANDLERS:
                if dispatch is None:
                    require(action_callbacks and present is None and len(callbacks)==1 and callbacks[0]['pc']==0xa196,
                            'handler during unsupported presentation callback')
                    if not callback_handlers:
                        require(pc in (0xa1be,0xa246),'action callback did not enter idle')
                        require(regs['M68K A7']==entry['registers']['M68K A7']-4 and be(block(e,'stack'),0,4)==0xf900,'idle callback return differs')
                    callback_handlers.append(e);continue
                if not handlers:
                    require(pc==be(block(dispatch,'actor'),0x16,4),'wrong first handler')
                    require(regs['M68K A7']==entry['registers']['M68K A7']-4 and be(block(e,'stack'),0,4)==0xf906,'handler return mismatch')
                handlers.append(e)
            elif pc==0xfcb32:
                request=tuple(be(block(e,'sound'),2*i) for i in range(4))
                if dispatch is None:
                    require(action_callbacks and present is None and callback_handlers,'sound during unsupported presentation callback')
                    callback_sounds.append(request)
                sounds.append(request)
            elif pc==0xf906:
                require(present is not None and dispatch is not None and handlers,'incomplete scheduled call')
                a=block(entry,'actor');after=block(e,'actor')
                changed={0,*range(2,20),*range(22,30),34,35,38,39,42,43}
                require(all(a[i]==after[i] for i in range(78) if i not in changed),'uncontracted actor write')
                require(len(block(entry,'control'))==len(block(e,'control')) and block(entry,'gate')==block(e,'gate') and all(a==b for i,(a,b) in enumerate(zip(block(entry,'control'),block(e,'control'))) if i not in control_writes),'environment inputs changed during invocation')
                if pairs:
                    previous=block(pairs[-1]['end'],'actor')
                    require(actor_fields(a)==actor_fields(previous) and be(a,0x1a,4)==be(previous,0x1a,4),'external actor change breaks continuous window')
                if callbacks and callbacks[0]['pc']==0xa196:
                    require(callback_handlers,'missing action callback continuation')
                pairs.append(dict(start=entry,presentation=present,end=e,callbacks=callbacks,handlers=handlers,sounds=tuple(sounds),
                                  callback_handlers=callback_handlers,callback_sounds=tuple(callback_sounds)))
                entry=None
        elif pc in (0xf900,0xf904,0xf906):raise ValueError('unmatched scheduled boundary')
    require(entry is None and pairs,'empty/incomplete scheduled trace')
    require(len(pairs)==end_frame-start_frame,'expected one P1 call per recorded frame in this window')
    require([p['start']['frame'] for p in pairs]==list(range(start_frame,end_frame)),'non-contiguous recorded calls')
    return pairs


def compare_window(trace,directory,native,scene,bank,start,end):
    pairs=validate_trace(trace,start,end);cases=[input_case(p['start']) for p in pairs]
    for name,data in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/name,data)
    comparisons={}
    for mode,label,key in (('--presentation','presentation','presentation'),('--sequence','continuous-actor','end')):
        command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),mode]
        proc=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60)
        atomic_write(directory/f'{label}.stdout',proc.stdout);atomic_write(directory/f'{label}.stderr',proc.stderr)
        require(proc.returncode==0,label+' failed: '+proc.stderr.decode())
        rows=decode_results(proc.stdout,len(cases))
        for i,(row,pair) in enumerate(zip(rows,pairs)):
            expected=snapshot_fields(pair[key],be(block(pair['start'],'actor'),0x1a,4))
            require(row[:18]==expected,f'{label} divergence at {start+i}: {row[:18]} != {expected}')
            requests=tuple(tuple(row[j:j+4]) for j in range(23,len(row),4))
            require(requests==(pair['sounds'] if key=='end' else ()),f'{label} sound request divergence at {start+i}')
        comparisons[label]={'calls':len(rows),'command':command,'output_sha256':hashlib.sha256(proc.stdout).hexdigest()}
    return {'ok':True,'start':start,'end':end,'calls':len(pairs),'comparisons':comparisons,
            'callback_hits':dict(Counter(hex(e['pc']) for p in pairs for e in p['callbacks'])),
            'handler_hits':dict(Counter(hex(e['pc']) for p in pairs for e in p['handlers'])),
            'sound_requests':sum(len(p['sounds']) for p in pairs),
            'pairs':[{'frame':p['start']['frame'],'start':p['start']['sequence'],'presentation_return':p['presentation']['sequence'],
                      'end':p['end']['sequence'],'callbacks':[hex(e['pc']) for e in p['callbacks']],
                      'handlers':[hex(e['pc']) for e in p['handlers']]} for p in pairs]}


def run(args,out):
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    recording=load_recording(args.recording);native=verify_executable(args.preset,'wiznliz-actor')
    identity=inspect_file();verify_expected(identity)
    # Pin this route deliberately; another movie needs its own researched windows.
    imported=recording['start']['imported_movie']
    require(imported['source']['sha256']==MOVIE_SHA256,'not the verified user movie')
    require(len(recording['inputs'])==5298 and recording['input_sha256']==INPUT_SHA256,'movie inputs differ')
    require(recording['experimental_edits']==[],'edited recording is not ordinary gameplay')
    require(recording['instrumentation']=={},'source recording must have an unhooked baseline')
    require(recording['rom']['sha256']==identity['sha256'],'recorded ROM differs')
    # load_recording validates the input digest; ReplaySession validates the
    # complete settings and exact recorded worker identity when opening.
    report={'ok':False,'scope':'continuous P1 actor state F8FC -> F906 with separately compared F76C return; external input/parameter/scratch feeds; no later +46/full-frame parity',
            'recording':str(args.recording.resolve()),'recording_sha256':hashlib.sha256(args.recording.read_bytes()).hexdigest(),
            'movie_sha256':MOVIE_SHA256,'recipe':recipe(),'windows':[],
            'native_build':json.loads((native.parent/'provenance.json').read_text()),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'hooked-worker')]) as w:
            s=ReplaySession.from_recording(w,recording);report['identity']=s.opened['identity']
            report['capabilities']=w.request('capabilities');caps=report['capabilities']['capabilities']
            require(all(caps[k] for k in ('frameAdvance','saveLoad','routineTrace','memoryInspection')),'worker capabilities missing')
            manifest=json.loads((external/'local/runtime/genesis-build.json').read_text())
            require(manifest['buildId']==BUILD_ID and s.opened['identity']['build']==manifest,'runtime generation differs')
            expected={Path(k).name:v for k,v in manifest['binaries'].items()}|{'GenesisWorker.exe':manifest['workerSha256']}
            require(all(expected.get(k)==v for k,v in s.opened['identity']['binaries'].items()),'loaded binary hashes differ')
            for start,end in WINDOWS:
                directory=out/f'{start}-{end}';directory.mkdir();s.seek(start)
                before=w.read_bytes('68K RAM',0,65536);scene,bank,terrain=terrain_fixture(before)
                atomic_write(directory/'before.ram',before)
                w.request('trace.configure',recipe());s.seek(end);trace=w.request('trace.drain')
                require(trace['identity']==s.opened['identity'],'trace identity differs');save(directory/'trace.json',trace)
                after=w.read_bytes('68K RAM',0,65536);atomic_write(directory/'after.ram',after)
                require(terrain_fixture(after)[:2]==(scene,bank),'terrain changed in selected window')
                comparison=compare_window(trace,directory,native,scene,bank,start,end);save(directory/'comparison.json',comparison)
                snapshot=w.request('snapshot');save(directory/'snapshot.json',snapshot)
                report['windows'].append({'start':start,'end':end,'classification':'ordinary recorded gameplay; no state edits',
                    'terrain':terrain,'comparison':comparison,'hooked_hash':snapshot['canonicalSha256'],'hash_scope':snapshot['hashScope'],
                    'artifacts':{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}})
                w.request('trace.configure',{})
        # A second fresh worker replays the exact same source inputs without any
        # hooks, matching each window end (not just the final movie boundary).
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'unhooked-worker')]) as w:
            s=ReplaySession.from_recording(w,recording)
            for window in report['windows']:
                s.seek(window['end']);snapshot=w.request('snapshot')
                require(snapshot['canonicalSha256']==window['hooked_hash'] and snapshot['hashScope']==window['hash_scope'],'hooked/unhooked replay differs')
                window['unhooked_hash']=snapshot['canonicalSha256']
        report['calls']=sum(w['comparison']['calls'] for w in report['windows']);report['ok']=True
    except Exception as e:
        report['error']=str(e)
        raise
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path,help='Verified adapted user movie recording.json')
    p.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug')
    p.add_argument('--preset',choices=('debug','release','sanitize'),default='debug');args=p.parse_args(argv)
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/movie-actor')))
    try:
        r=run(args,out);print(json.dumps({'ok':r['ok'],'calls':r['calls'],'report':str(out/'report.json')},indent=2));return 0
    except Exception as e:
        save(out/'failure.json',{'error':str(e)});print(json.dumps({'ok':False,'error':str(e),'report':str(out/'report.json')}));return 1
