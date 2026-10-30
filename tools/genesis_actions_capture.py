"""Continuous up/down movie windows and reproducible input branches, with no RAM edits."""
import argparse
from collections import Counter
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from rom import ROOT,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import verify_executable
from genesis_actor_capture import save,require,block,be,terrain_fixture,BUILD_ID
from genesis_movie_actor_capture import recipe as actor_recipe,validate_trace,input_case,snapshot_fields,MOVIE_SHA256,INPUT_SHA256
from actions_cases import decode,split
from terrain_cases import encode_cases

# This historical action window begins at 1615. The dispatch comparator extends
# it through the verified 12646/AA50 phase and the later control-record tail.
# Stop before frame 3339's allocating reversal: reversal objects have their
# own complete lifetime comparator; this transport compares action/mailbox effects.
WINDOWS=((1615,1690),(3230,3339))
BRANCHES=(('sample-and-down-jump',3258,[['P1 Up','P1 A']]*16+[[]]*14+[['P1 Down']]*18+[['P1 Down','P1 B']]*4+[[]]*8),
          ('up-jump',3258,[['P1 Up','P1 B']]*4+[[]]*8))
EXTRA_PCS=[0x9c56,0x9d4e,0x9d44,0x9dc4,0xed6e6,0xed714]


def recipe():
    r=actor_recipe();r['pcs']+=EXTRA_PCS
    r['ranges'] += [{'label':'action_globals','domain':'68K RAM','offset':0x33d8,'length':10},
                   {'label':'mailbox','domain':'68K RAM','offset':0xad6,'length':8}]
    return r


def shared_fields(e):
    data=block(e,'action_globals');mailbox=block(e,'mailbox')
    require(len(data)==10 and len(mailbox)==8,'shared snapshot extent differs')
    return (be(data,8),be(data,0),be(data,2),*(be(mailbox,i) for i in range(0,8,2)))


def action_case(e):
    fields=shared_fields(e)
    return (*input_case(e),*fields[:3],block(e,'control')[0x14],*fields[3:])


def validate_actions(trace,start,end,*,completion_modes=(),sample_returns=(0x9ce8,),sample_contract=(0xf0000,200,0xf14,0x8000,30,24),control_writes=()):
    pairs=validate_trace(trace,start,end,action_callbacks=True,control_writes=control_writes)
    for pair in pairs:
        events=[e for e in trace['events'] if pair['start']['sequence']<e['sequence']<pair['end']['sequence'] and e['registers']['M68K A6']==0xffff1ab4]
        samples=[];pending=None
        for e in events:
            if e['pc']==0xed6e6:
                require(pending is None,'nested sample request');pending=e
                regs=e['registers'];require((regs['M68K D0'],regs['M68K D1'],regs['M68K D2'])==sample_contract[:3],'sample request ABI differs')
                require(regs['M68K A7']==pair['start']['registers']['M68K A7']-sample_contract[5] and be(block(e,'stack'),0,4) in sample_returns,'sample caller stack differs')
            elif e['pc']==0xed714:
                require(pending is not None,'unpaired sample mailbox return')
                require(e['registers']['M68K A7']==pending['registers']['M68K A7'] and block(e,'stack')==block(pending,'stack'),'sample service return differs')
                require(shared_fields(e)[3:]==sample_contract[1:5],'sample mailbox write differs')
                require(block(e,'action_globals')==block(pending,'action_globals'),'sample service changed action globals')
                samples.append((pending,e));pending=None
        require(pending is None,'missing sample mailbox return')
        before=block(pair['start'],'action_globals');after=block(pair['end'],'action_globals')
        require(before[4:8]==after[4:8] and (before[8:]==after[8:] or be(after,8) in completion_modes),'uncontracted shared-global write')
        pair['samples']=samples
    return pairs


def compare_window(trace,directory,native,scene,bank,start,end):
    pairs=validate_actions(trace,start,end);cases=[action_case(p['start']) for p in pairs]
    for name,data in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/name,data)
    comparisons={}
    for mode,label,key in (('--actions-presentation','presentation','presentation'),('--actions-sequence','continuous-actor','end')):
        command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),mode]
        proc=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60)
        atomic_write(directory/f'{label}.stdout',proc.stdout);atomic_write(directory/f'{label}.stderr',proc.stderr)
        require(proc.returncode==0,label+' failed: '+proc.stderr.decode())
        for row,pair in zip(decode(proc.stdout,len(cases)),pairs):
            core,shared,samples=split(row);event=pair[key];frame=pair['start']['frame']
            expected=snapshot_fields(event,be(block(pair['start'],'actor'),0x1a,4))
            require(core[:18]==expected,f'{label} actor divergence at {frame}: {core[:18]} != {expected}')
            require(shared==shared_fields(event),f'{label} shared/mailbox divergence at {frame}')
            sounds=tuple(tuple(core[j:j+4]) for j in range(23,len(core),4))
            require(sounds==(pair['sounds'] if key=='end' else pair['callback_sounds']),f'{label} sound mismatch at {frame}')
            selected=[s for s,e in pair['samples'] if e['sequence']<event['sequence']]
            require(samples==tuple((0,s['registers']['M68K D1'],s['registers']['M68K D2']) for s in selected),f'{label} sample request mismatch at {frame}')
        comparisons[label]={'calls':len(cases),'command':command,'output_sha256':hashlib.sha256(proc.stdout).hexdigest()}
    return {'ok':True,'calls':len(pairs),'comparisons':comparisons,
            'callbacks':dict(Counter(hex(e['pc']) for p in pairs for e in p['callbacks'])),
            'callback_handlers':dict(Counter(hex(e['pc']) for p in pairs for e in p['callback_handlers'])),
            'handlers':dict(Counter(hex(e['pc']) for p in pairs for e in p['handlers'])),
            'sound_requests':sum(len(p['sounds']) for p in pairs),'sample_requests':sum(len(p['samples']) for p in pairs),
            'action_boundaries':[{'frame':e['frame'],'pc':hex(e['pc'])} for e in trace['events'] if e['pc'] in EXTRA_PCS and e['registers']['M68K A6']==0xffff1ab4]}


def check_worker(w,s,external):
    caps=w.request('capabilities');require(all(caps['capabilities'][k] for k in ('frameAdvance','routineTrace','memoryInspection')),'worker capabilities missing')
    manifest=json.loads((external/'local/runtime/genesis-build.json').read_text())
    require(manifest['buildId']==BUILD_ID and s.opened['identity']['build']==manifest,'runtime generation differs')
    expected={Path(k).name:v for k,v in manifest['binaries'].items()}|{'GenesisWorker.exe':manifest['workerSha256']}
    require(all(expected.get(k)==v for k,v in s.opened['identity']['binaries'].items()),'loaded binary hashes differ')
    return caps


def main(argv=None,*,capture_recipe=recipe,comparator=compare_window,windows=WINDOWS,output_name="actions-movie",
         scope="continuous native actor plus intermediate contextual presentation; controls/parameters/shared globals/mailbox/terrain scratch fed by external world at each actor call; no full-frame or audio parity"):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path)
    p.add_argument('--preset',choices=('debug','release','sanitize'),default='debug')
    p.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug');args=p.parse_args(argv)
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity);native=verify_executable(args.preset,'wiznliz-actor')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[],'movie inputs/edits differ')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256,'movie identity differs')
    require(source['instrumentation']=={} and source['rom']['sha256']==identity['sha256'],'source baseline/ROM differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/'+output_name)))
    report={'ok':False,'windows':[],'recipe':capture_recipe(),
            'scope':scope,
            'recording_sha256':hashlib.sha256(args.recording.read_bytes()).hexdigest(),'movie_sha256':MOVIE_SHA256,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'contract_sources':{str(Path(inspect.getsourcefile(f)).relative_to(ROOT)):hashlib.sha256(Path(inspect.getsourcefile(f)).read_bytes()).hexdigest() for f in (capture_recipe,comparator,validate_trace,input_case)},'native_build':json.loads((native.parent/'provenance.json').read_text())}
    def capture(w,s,directory,start,end,classification,rows=None):
        directory.mkdir();before=w.read_bytes('68K RAM',0,65536);scene,bank,terrain=terrain_fixture(before);atomic_write(directory/'before.ram',before)
        w.request('trace.configure',capture_recipe());s.seek(end);trace=w.request('trace.drain');save(directory/'trace.json',trace)
        require(trace['identity']==s.opened['identity'],'trace identity differs')
        after=w.read_bytes('68K RAM',0,65536);atomic_write(directory/'after.ram',after)
        require(terrain_fixture(after)[:2]==(scene,bank),'terrain endpoints differ')
        result=comparator(trace,directory,native,scene,bank,start,end);save(directory/'comparison.json',result)
        snap=w.request('snapshot');save(directory/'snapshot.json',snap)
        # Branch export retains parent digest, exact removed/inserted rows, complete
        # settings/build, input history, hook recipe and zero RAM edits.
        if rows is not None:s.export(directory/'recording.json')
        window={'start':start,'end':end,'classification':classification,'branch_rows':rows,'terrain':terrain,'comparison':result,
                'hooked_hash':snap['canonicalSha256'],'hash_scope':snap['hashScope'],
                'artifacts':{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in directory.iterdir() if f.is_file()}}
        report['windows'].append(window);w.request('trace.configure',{})
    try:
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'ordinary-hooked')]) as w:
            s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];report['capabilities']=check_worker(w,s,external)
            for start,end in windows:
                s.seek(start);capture(w,s,out/f'{start}-{end}',start,end,'ordinary unedited user movie')
        for name,start,rows in BRANCHES:
            with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/f'{name}-worker')]) as w:
                s=ReplaySession.from_recording(w,source);check_worker(w,s,external);s.seek(start);s.branch(start,rows)
                capture(w,s,out/name,start,start+len(rows),'ordinary gameplay input branch; explicit replacement inputs, zero RAM/register/ROM edits',rows)
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'ordinary-unhooked')]) as w:
            s=ReplaySession.from_recording(w,source);check_worker(w,s,external)
            for window in report['windows']:
                if window['branch_rows'] is not None:continue
                s.seek(window['end']);snap=w.request('snapshot')
                require(snap['canonicalSha256']==window['hooked_hash'] and snap['hashScope']==window['hash_scope'],'ordinary hooked/unhooked replay differs')
                window['unhooked_hash']=snap['canonicalSha256']
        for i,window in enumerate(report['windows']):
            if window['branch_rows'] is None:continue
            with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/f'branch-unhooked-{i}')]) as w:
                s=ReplaySession.from_recording(w,source);check_worker(w,s,external);s.branch(window['start'],window['branch_rows']);s.seek(window['end']);snap=w.request('snapshot')
                require(snap['canonicalSha256']==window['hooked_hash'] and snap['hashScope']==window['hash_scope'],'branch hooked/unhooked replay differs')
                window['unhooked_hash']=snap['canonicalSha256']
        report['ordinary_calls']=sum(w['comparison']['calls'] for w in report['windows'] if w['branch_rows'] is None)
        report['branch_calls']=sum(w['comparison']['calls'] for w in report['windows'] if w['branch_rows'] is not None)
        boundaries={e['pc'] for w in report['windows'] for e in w['comparison']['action_boundaries']}
        require(all(hex(pc) in boundaries for pc in EXTRA_PCS),'missing requested action branch coverage')
        require(sum(w['comparison']['sample_requests'] for w in report['windows'])==1,'expected one targeted sample request')
        report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','ordinary_calls','branch_calls','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
