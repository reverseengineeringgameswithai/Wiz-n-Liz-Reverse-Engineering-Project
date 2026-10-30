"""Controlled secondary-tally branches from the preserved movie; no ordinary-hit claim."""
import hashlib,subprocess
from genesis_actor_capture import block,be,require
from genesis_dispatch_capture import validate_dispatch,tracking_fields
from genesis_actions_capture import action_case,shared_fields
from genesis_movie_actor_capture import snapshot_fields
from genesis_transition_capture import transition_fields
from genesis_tally_capture import tally_fields
from genesis_exit_tally_capture import recipe as exit_recipe,exit_fields,ALL_LABELS
from score_cases import decode
from actions_cases import split
from terrain_cases import encode_cases
from rnc import atomic_write

EXTRA=(0x53f2,0x540a,0x5418,0x541a,0x5424,0x5428,0x544e,0x5456,0xadf4,0xae18,0xae1a,0xae20,0xae2c,0xae2e,0xae30,0xae36,0xae4c,0xae70,0xaf28,0xaf44,0xaf48,0xaf50,0xaf5a)
RANGES=(('score_value',0x6fe,4),('score_threshold',0x702,4),('score_increment',0x6c2,4),('score_rewards',0x706,2),('score_scratch',0x443e,4))
LABELS=ALL_LABELS+tuple(l for l,o,n in RANGES)


def recipe():
    r=exit_recipe();r['pcs']=list(dict.fromkeys(r['pcs']+list(EXTRA)))
    r['ranges'] += [dict(label=l,domain='68K RAM',offset=o,length=n) for l,o,n in RANGES]
    return r


def score_fields(e):
    require(all(len(block(e,l))==n for l,o,n in RANGES),'score snapshot extent differs')
    return tuple(be(block(e,l),0,n) for l,o,n in RANGES)


def validate(trace,start,end):
    pairs=validate_dispatch(trace,start,end,sample_returns=(0xaf44,),sample_contract=(0xf25ea,230,0x20e4,0xa5ea,30,36),control_writes=(0x6e,0x6f))
    for p in pairs:
        es=[e for e in trace['events'] if e['frame']==p['start']['frame'] and e['registers']['M68K A6']==0xffff1ab4]
        def one(pc):
            found=[e for e in es if e['pc']==pc];require(len(found)==1,'score boundary count differs: '+hex(pc));return found[0]
        def same(a,b,labels=LABELS):require(all(block(a,l)==block(b,l) for l in labels),'uncontracted score write')
        def stack(e,sp,ret):require(e['registers']['M68K A7']==sp and be(block(e,'stack'),0,4)==ret,'score pending return differs')
        require([h['pc'] for h in p['handlers']]==[0x5132] and not p['callbacks'],'unexpected score handler/callback')
        entry=p['handlers'][0];sp=entry['registers']['M68K A7'];after=one(0x513c)
        coast=one(0xa148);stack(coast,sp-4,0x513c)
        require(entry['sequence']<coast['sequence']<after['sequence'],'score coast order differs')
        secondary=[e for e in es if e['pc']==0x53f2]
        if secondary:
            require(len(secondary)==1 and tally_fields(entry)[1]==0 and all(exit_fields(entry)[:2]),'secondary gate differs')
            same(after,secondary[0]);stack(secondary[0],sp,0xf906)
            consumed=[e for e in es if e['pc']==0x541a]
            if consumed:
                before,call,score,add,add_rts,added,score_rts,returned,sound,last=(one(pc) for pc in (0x541a,0x5424,0xae1a,0xadf4,0xae18,0xae20,0xae2e,0x5428,0xfcb32,0x5456))
                require([e['sequence'] for e in (before,call,score,add,add_rts,added,score_rts,returned,sound,last)]==sorted(e['sequence'] for e in (before,call,score,add,add_rts,added,score_rts,returned,sound,last)),'score call order differs')
                stack(score,sp-4,0x5428);stack(score_rts,sp-4,0x5428);stack(add,sp-12,0xae20);stack(add_rts,sp-12,0xae20);stack(returned,sp,0xf906);stack(sound,sp-4,0x544e)
                require(exit_fields(call)[1]==(exit_fields(before)[1]-1)&65535,'secondary decrement differs')
                same(before,call,tuple(l for l in LABELS if l!='secondary_remaining'))
                same(score,add);same(add_rts,added);same(score_rts,returned)
                rewards=[e for e in es if e['pc']==0xaf28];advances=[e for e in es if e['pc']==0xae4c];advance_returns=[e for e in es if e['pc']==0xae70]
                crosses=score_fields(added)[0]>score_fields(added)[1]
                require(len(rewards)==len(p['samples'])==int(crosses),'one reward per score call differs')
                require(len(advances)==len(advance_returns) and bool(advances)==crosses,'threshold loop differs')
                if crosses:
                    stack(rewards[0],sp-12,0xae36);reward_rts=one(0xaf5a);stack(reward_rts,sp-12,0xae36)
                    require(added['sequence']<rewards[0]['sequence']<reward_rts['sequence']<advances[0]['sequence'],'reward/threshold ordering differs')
                    old=score_fields(rewards[0])[3];require(score_fields(reward_rts)[3]==(old if old==9 else (old+1)&65535),'reward equality cap differs')
                for a,b in zip(advances,advance_returns):
                    stack(a,sp-12,0xae40);stack(b,sp-12,0xae40);require(a['sequence']<b['sequence']<score_rts['sequence'],'threshold return order differs')
                require(p['sounds']==((140,6,192,1),) and tally_fields(last)[3]==3,'secondary sound/countdown differs')
            else:
                last=one(0x5418);require(not p['sounds'] and not p['samples'],'countdown emitted requests')
                require(tally_fields(last)[3]==(tally_fields(secondary[0])[3]-1)&65535,'secondary countdown differs')
                same(secondary[0],last,tuple(l for l in LABELS if l!='tally_countdown'))
        else:
            require(exit_fields(entry)[1]==0 and not p['samples'] and not p['sounds'],'unexpected secondary bypass');last=one(0x4f8c);same(after,last)
        stack(last,sp,0xf906);same(last,p['end']);require(last['sequence']<p['end']['sequence'],'score tail differs')
        same(p['end'],p['return'],tuple(l for l in LABELS if l!='control'))
        same(entry,p['return'],('secondary_gate','exit_marker','exit_selection','exit_target','score_increment','remaining','credit','transition','palette_flags','requested_position','saved_position'))
        p['score_advances']=sum(e['pc']==0xae4c for e in es)
    return pairs


def compare_window(trace,directory,native,scene,bank,start,end):
    pairs=validate(trace,start,end)
    cases=[(*action_case(p['wrapper']),*tracking_fields(p['wrapper']),*transition_fields(p['wrapper']),*tally_fields(p['wrapper']),block(p['wrapper'],'control')[0x21],*exit_fields(p['wrapper']),*score_fields(p['wrapper'])) for p in pairs]
    for name,data in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/name,data)
    command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),'--score-sequence']
    proc=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60);atomic_write(directory/'native.stdout',proc.stdout);atomic_write(directory/'native.stderr',proc.stderr)
    require(proc.returncode==0,'native score sequence failed: '+proc.stderr.decode())
    for row,p in zip(decode(proc.stdout,len(cases)),pairs):
        a,b=p['wrapper'],p['return'];require(row[-6:]==(*score_fields(b),p['score_advances']),'score diverged');row=row[:-6]
        require(row[-5:]==exit_fields(b),'exit fields diverged');row=row[:-5];require(row[-6:]==tally_fields(b),'tally diverged');row=row[:-6]
        require(row[-13:]==transition_fields(b,a) and row[-17:-13]==tracking_fields(b),'transition/tracking diverged')
        core,shared,samples=split(row[:-17]);require(core[:18]==snapshot_fields(b,be(block(a,'actor'),0x1a,4)),'actor/scratch diverged')
        require(shared==shared_fields(b) and samples==tuple((1,230,0x20e4) for _ in p['samples']),'shared/sample diverged')
        require(tuple(tuple(core[j:j+4]) for j in range(23,len(core),4))==p['sounds'],'sound requests diverged')
    return dict(ok=True,continuous_wrapper_calls=len(pairs),sample_requests=sum(len(p['samples']) for p in pairs),sound_requests=sum(len(p['sounds']) for p in pairs),threshold_advances=sum(p['score_advances'] for p in pairs),command=command,output_sha256=hashlib.sha256(proc.stdout).hexdigest())


def main(argv=None):
    import argparse,json,sys,tempfile
    from pathlib import Path
    from rom import ROOT,inspect_file,verify_expected
    from rnc import approved_directory
    from native_build import verify_executable
    from genesis_actor_capture import save,terrain_fixture
    from genesis_actions_capture import check_worker
    from genesis_movie_actor_capture import INPUT_SHA256,MOVIE_SHA256
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('recording',type=Path)
    parser.add_argument('--preset',choices=('debug','release','sanitize'),default='debug')
    parser.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug');args=parser.parse_args(argv)
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity);native=verify_executable(args.preset,'wiznliz-actor')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[] and source['instrumentation']=={},'movie baseline differs')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256 and source['rom']['sha256']==identity['sha256'],'source identity differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/score-experiments')))
    names=('tools/genesis_score_capture.py','tools/genesis_exit_tally_capture.py','tools/genesis_tally_capture.py','tools/genesis_transition_capture.py','tools/genesis_actions_capture.py','tools/genesis_dispatch_capture.py','tools/genesis_movie_actor_capture.py','tests/actor_cases.py','tests/score_cases.py')
    report=dict(ok=False,classification='controlled RAM edits and neutral input branch from user movie; not ordinary gameplay',
        scope='P1 5132/53F2 wrapper, score arithmetic and ordered reward request/threshold loop; no world/frame parity',recipe=recipe(),
        recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(),movie_sha256=MOVIE_SHA256,input_sha256=INPUT_SHA256,
        contract_sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},native_build=__import__('json').loads((native.parent/'provenance.json').read_text()),experiments=[])
    try:
        for name,value,threshold,increment,rewards,frames,expected in (
            ('cross-many',0x80000,0x10000,0x20000,8,8,(2,5)),
            ('equal',0,0x10000,0x10000,8,1,(0,0)),
            ('score-wrap',0x99999999,0x10000,0x10000,8,1,(0,0)),
            ('reward-wrap',0x10000,0x10000,0x10000,65535,1,(1,1))):
            directory=out/name;directory.mkdir();start,end=4934,4934+frames;snapshots=[]
            experiment=dict(name=name,start=start,end=end,inputs=[[] for _ in range(frames)])
            for hooked in (True,False):
                label='hooked' if hooked else 'unhooked'
                with WorkerClient([str(external/'run-worker.sh'),'--storage',str(directory/(label+'-worker'))]) as w:
                    session=ReplaySession.from_recording(w,source);report['identity']=session.opened['identity'];report['capabilities']=check_worker(w,session,external);session.seek(start)
                    require(report['capabilities']['capabilities']['ramEdits'],'RAM edits unavailable')
                    before=w.read_bytes('68K RAM',0,65536);require(before[0x1aca:0x1ace]==bytes.fromhex('00005132'),'experiment handler differs')
                    writes=[(0x714,2,0),(0xefe,2,1),(0x70e,2,2),(0x340a,2,65535),(0xf0e,2,0),
                            (0x6b1,1,0),(0x6fe,4,value),(0x702,4,threshold),(0x6c2,4,increment),(0x706,2,rewards),(0x443e,4,0xdeadbeef)]
                    edit=dict(expectedFrame=start,writes=[dict(domain='68K RAM',offset=o,expectedHex=before[o:o+n].hex(),hex=v.to_bytes(n,'big').hex()) for o,n,v in writes])
                    save(directory/(label+'-edit.json'),w.request('experiment.edit',edit));experiment[label+'_edits']=edit
                    if hooked:
                        atomic_write(directory/'before.ram',before);scene,bank,experiment['terrain']=terrain_fixture(before);w.request('trace.configure',recipe())
                    advanced=w.request('advance',dict(rows=experiment['inputs'],render=False,audio=False,timeoutMs=120000));save(directory/(label+'-advance.json'),advanced)
                    require(advanced.get('frame',advanced.get('endFrame'))==end,'incomplete experiment advance')
                    if hooked:
                        trace=w.request('trace.drain');save(directory/'trace.json',trace);require(trace['identity']==session.opened['identity'],'trace identity differs')
                        after=w.read_bytes('68K RAM',0,65536);atomic_write(directory/'after.ram',after);require(terrain_fixture(after)[:2]==(scene,bank),'terrain endpoints differ')
                        experiment['comparison']=compare_window(trace,directory,native,scene,bank,start,end)
                        c=experiment['comparison'];require((c['sample_requests'],c['threshold_advances'])==expected,'expected score branch not reached')
                    snapshot=w.request('snapshot');save(directory/(label+'-snapshot.json'),snapshot);snapshots.append(snapshot)
            require(experiment['hooked_edits']==experiment['unhooked_edits'],'independent edit baseline differs')
            require(snapshots[0]['canonicalSha256']==snapshots[1]['canonicalSha256'] and snapshots[0]['hashScope']==snapshots[1]['hashScope'],'hooked/unhooked experiment differs')
            experiment.update(hooked_unhooked_equal=True,final_hash=snapshots[0]['canonicalSha256'],hash_scope=snapshots[0]['hashScope'])
            experiment['artifacts']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in directory.iterdir() if f.is_file()};report['experiments'].append(experiment)
        report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps(dict(ok=report['ok'],experiments=len(report['experiments']),error=report.get('error'),report=str(out/'report.json')),indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
