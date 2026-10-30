"""Continuous 5132/5188 movie wrappers and exact nested tally/transition returns."""
import hashlib
import subprocess
from collections import Counter
from genesis_actor_capture import block,be,require
from genesis_dispatch_capture import validate_dispatch,tracking_fields
from genesis_actions_capture import action_case,shared_fields
from genesis_movie_actor_capture import snapshot_fields
from genesis_transition_capture import transition_fields,main as capture_main
from genesis_tally_capture import recipe as tally_recipe,tally_fields,LABELS
from exit_tally_cases import decode
from actions_cases import split
from terrain_cases import encode_cases
from rnc import atomic_write

START,END=4807,5038
EXTRA=(0x513c,0x5146,0x514e,0x5156,0x5158,0x517a,0x5182,0x5192,0x519c,0x51ac,0x51ba,0x51be,0x51c6,0x53f2)
RANGES=(('secondary_gate',0xefe),('secondary_remaining',0x70e),('exit_marker',0x70c),('exit_selection',0x33c8),('exit_target',0x33cc))
ALL_LABELS=LABELS+tuple(l for l,o in RANGES)


def recipe():
    r=tally_recipe();r['pcs']=list(dict.fromkeys(r['pcs']+list(EXTRA)))
    r['ranges'] += [dict(label=l,domain='68K RAM',offset=o,length=2) for l,o in RANGES]
    return r


def exit_fields(e):
    require(all(len(block(e,l))==2 for l,o in RANGES),'exit snapshot extent differs')
    return tuple(be(block(e,l),0) for l,o in RANGES)


def validate(trace,start,end):
    pairs=validate_dispatch(trace,start,end,completion_modes=(1,))
    for p in pairs:
        es=[e for e in trace['events'] if e['frame']==p['start']['frame'] and e['registers']['M68K A6']==0xffff1ab4]
        def one(pc):
            selected=[e for e in es if e['pc']==pc];require(len(selected)==1,'exit boundary count differs: '+hex(pc));return selected[0]
        def same(a,b,labels=ALL_LABELS):require(all(block(a,l)==block(b,l) for l in labels),'uncontracted exit state change')
        def stack(e,sp,ret):require(e['registers']['M68K A7']==sp and be(block(e,'stack'),0,4)==ret,'exit pending return differs')
        require(not any(e['pc']==0x53f2 for e in es),'unsupported secondary score observed')
        require(len(p['handlers'])==1 and p['handlers'][0]['pc'] in (0x5132,0x5188) and not p['callbacks'] and not p['samples'],'unexpected exit continuation/effect')
        entry=p['handlers'][0];sp=entry['registers']['M68K A7'];h=entry['pc']
        coast,after=one(0xa148),one(0x513c if h==0x5132 else 0x5192)
        rts=[e for e in es if e['pc'] in (0xa15c,0xa168)];require(len(rts)==1,'coasting RTS count differs')
        require(entry['sequence']<coast['sequence']<rts[0]['sequence']<after['sequence'],'coasting order differs')
        stack(coast,sp-4,after['pc']);stack(rts[0],sp-4,after['pc']);stack(after,sp,0xf906);same(rts[0],after)
        tally=tally_fields(entry);exit_state=exit_fields(entry)
        if h==0x5132 and tally[1]:
            counter,returned=one(0x537c),one(0x5146)
            tails=[e for e in es if e['pc'] in (0x53a2,0x53dc)];require(len(tails)==1,'nested tally return count differs');tail=tails[0]
            require(after['sequence']<counter['sequence']<tail['sequence']<returned['sequence'],'nested tally order differs')
            stack(counter,sp-4,0x5146);stack(tail,sp-4,0x5146);stack(returned,sp,0xf906);same(tail,returned)
            if p['sounds']:
                credit,credit_rts=one(0xaf98),one(0xafae);sound=one(0xfcb32)
                require(counter['sequence']<credit['sequence']<credit_rts['sequence']<sound['sequence']<tail['sequence'],'nested request order differs')
                stack(credit,sp-8,0x53ae);stack(credit_rts,sp-8,0x53ae);stack(sound,sp-8,0x53d4)
                require(p['sounds']==((140,6,192,1),),'exit sound request differs')
            if tally_fields(returned)[1]==0:
                reset,last=one(0x514e),one(0x5156);same(returned,reset)
                require(returned['sequence']<reset['sequence']<last['sequence'] and tally_fields(last)[3]==60,'last-unit countdown reset differs')
                same(reset,last,tuple(l for l in ALL_LABELS if l!='tally_countdown'))
            else:last=one(0x4f8c);same(returned,last)
        elif h==0x5132:
            require(not(exit_state[0] and exit_state[1]),'unsupported secondary trigger')
            require(not p['sounds'],'unexpected sound outside tally')
            if tally[2] or block(entry,'control')[0x21]:
                before,assigned,init,last=one(0x517a),one(0x5182),one(0x13208),one(0x1324c)
                require(after['sequence']<before['sequence']<assigned['sequence']<init['sequence']<last['sequence'],'transition tail order differs')
                same(after,before);same(assigned,init);stack(init,sp,0xf906)
                require(be(block(assigned,'actor'),0x16,4)==0x5188,'deferred selector differs')
                same(before,assigned,tuple(l for l in ALL_LABELS if l!='actor'))
                a=bytearray(block(before,'actor'));a[0x16:0x1a]=(0x5188).to_bytes(4,'big');require(bytes(a)==block(assigned,'actor'),'unexpected assignment write')
                same(init,last,tuple(l for l in ALL_LABELS if l not in ('transition','palette_flags')))
            else:last=one(0x4f8c);same(after,last)
        else:
            require(not p['sounds'],'wait emitted sound')
            if transition_fields(entry)[0]:last=one(0x4f8c);same(after,last)
            else:
                saved,cmp,mode,last=one(0x519c),one(0x51ac),one(0x51be),one(0x51c6)
                require(after['sequence']<saved['sequence']<cmp['sequence']<mode['sequence']<last['sequence'],'completion order differs')
                same(after,saved);same(saved,cmp,tuple(l for l in ALL_LABELS if l!='saved_position'))
                require(block(cmp,'saved_position')==block(saved,'requested_position'),'saved position differs')
                clear=[e for e in es if e['pc']==0x51ba];require(len(clear)==int(exit_state[3]==exit_state[4]),'conditional marker clear differs')
                if clear:require(cmp['sequence']<clear[0]['sequence']<mode['sequence'],'clear order differs');same(cmp,clear[0])
                require(exit_fields(mode)[2]==(0 if clear else exit_state[2]),'marker write differs')
                same(cmp,mode,tuple(l for l in ALL_LABELS if l!='exit_marker'))
                same(mode,last,tuple(l for l in ALL_LABELS if l!='action_globals'));require(shared_fields(last)[0]==1,'completion mode differs')
        stack(last,sp,0xf906);require(after['sequence']<last['sequence']<p['end']['sequence'],'final exit return order differs');same(last,p['end'])
        same(p['end'],p['return'],tuple(l for l in ALL_LABELS if l!='control'))
        same(entry,p['return'],('secondary_gate','secondary_remaining','exit_selection','exit_target','tally_gate','special_gate','mailbox','requested_position'))
    return pairs


def compare_window(trace,directory,native,scene,bank,start,end):
    pairs=validate(trace,start,end)
    cases=[(*action_case(p['wrapper']),*tracking_fields(p['wrapper']),*transition_fields(p['wrapper']),*tally_fields(p['wrapper']),block(p['wrapper'],'control')[0x21],*exit_fields(p['wrapper'])) for p in pairs]
    for name,data in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/name,data)
    command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),'--exit-tally-sequence']
    proc=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60)
    atomic_write(directory/'native.stdout',proc.stdout);atomic_write(directory/'native.stderr',proc.stderr);require(proc.returncode==0,'native exit sequence failed: '+proc.stderr.decode())
    for row,p in zip(decode(proc.stdout,len(cases)),pairs):
        a,b=p['wrapper'],p['return'];require(row[-5:]==exit_fields(b),'exit fields diverged');row=row[:-5]
        require(row[-6:]==tally_fields(b),'tally diverged');row=row[:-6]
        require(row[-13:]==transition_fields(b,a) and row[-17:-13]==tracking_fields(b),'transition/tracking diverged')
        core,shared,samples=split(row[:-17]);require(core[:18]==snapshot_fields(b,be(block(a,'actor'),0x1a,4)),'actor/scratch diverged')
        require(shared==shared_fields(b) and not samples,'global/mailbox diverged')
        require(tuple(tuple(core[j:j+4]) for j in range(23,len(core),4))==p['sounds'],'sound requests diverged')
    return dict(ok=True,continuous_wrapper_calls=len(pairs),handlers=dict(Counter(hex(p['handlers'][0]['pc']) for p in pairs)),sound_requests=sum(len(p['sounds']) for p in pairs),
        transition_frames=[p['return']['frame'] for p in pairs if p['handlers'][0]['pc']==0x5132 and be(block(p['return'],'actor'),0x16,4)==0x5188],
        completion_frames=[p['return']['frame'] for p in pairs if shared_fields(p['return'])[0]==1],command=command,output_sha256=hashlib.sha256(proc.stdout).hexdigest())


def controlled(argv):
    import argparse,json,sys,tempfile
    from pathlib import Path
    from rom import ROOT,inspect_file,verify_expected
    from rnc import approved_directory
    from native_build import verify_executable
    from genesis_actor_capture import save,terrain_fixture
    from genesis_actions_capture import check_worker
    from genesis_movie_actor_capture import INPUT_SHA256,MOVIE_SHA256
    parser=argparse.ArgumentParser(description='Controlled 5188 equality/marker-clear experiment from movie boundary 5037')
    parser.add_argument('recording',type=Path);parser.add_argument('--preset',choices=('debug','release','sanitize'),default='debug')
    parser.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug');args=parser.parse_args(argv)
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity);native=verify_executable(args.preset,'wiznliz-actor')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[] and source['instrumentation']=={},'movie baseline differs')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256 and source['rom']['sha256']==identity['sha256'],'source identity differs')
    start,end=5037,5038;out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/exit-tally-experiment')))
    names=('tools/genesis_exit_tally_capture.py','tools/genesis_tally_capture.py','tools/genesis_transition_capture.py','tools/genesis_actions_capture.py','tools/genesis_dispatch_capture.py','tools/genesis_movie_actor_capture.py','tests/actor_cases.py','tests/exit_tally_cases.py')
    report=dict(ok=False,start=start,end=end,classification='controlled RAM equality/marker edits from user movie; not ordinary gameplay',
        scope='one P1 5188 wrapper, conditional marker clear and mode-1 completion; no world/frame parity',recipe=recipe(),
        recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(),movie_sha256=MOVIE_SHA256,input_sha256=INPUT_SHA256,
        contract_sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},native_build=json.loads((native.parent/'provenance.json').read_text()))
    snapshots=[]
    try:
        for hooked in (True,False):
            label='hooked' if hooked else 'unhooked'
            with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/(label+'-worker'))]) as w:
                session=ReplaySession.from_recording(w,source);report['identity']=session.opened['identity'];report['capabilities']=check_worker(w,session,external);session.seek(start)
                require(report['capabilities']['capabilities']['ramEdits'],'RAM edits unavailable')
                before=w.read_bytes('68K RAM',0,65536)
                require(before[0x1aca:0x1ace]==bytes.fromhex('00005188'),'experiment handler differs')
                edit=dict(expectedFrame=start,writes=[dict(domain='68K RAM',offset=o,expectedHex=before[o:o+2].hex(),hex=v.hex()) for o,v in ((0x70c,b'\xff\xff'),(0x33cc,before[0x33c8:0x33ca]))])
                save(out/(label+'-edit.json'),w.request('experiment.edit',edit));report['edits']=edit
                if hooked:
                    atomic_write(out/'before.ram',before);scene,bank,report['terrain']=terrain_fixture(before);w.request('trace.configure',recipe())
                rows=source['inputs'][start:end];report['inputs']=rows
                advanced=w.request('advance',dict(rows=rows,render=False,audio=False,timeoutMs=120000));save(out/(label+'-advance.json'),advanced)
                require(advanced.get('frame',advanced.get('endFrame'))==end,'incomplete experiment advance')
                if hooked:
                    trace=w.request('trace.drain');save(out/'trace.json',trace);require(trace['identity']==session.opened['identity'],'trace identity differs')
                    after=w.read_bytes('68K RAM',0,65536);atomic_write(out/'after.ram',after);require(terrain_fixture(after)[:2]==(scene,bank),'terrain endpoints differ')
                    report['comparison']=compare_window(trace,out,native,scene,bank,start,end)
                    require(after[0x70c:0x70e]==b'\0\0' and any(e['pc']==0x51ba for e in trace['events']),'marker clear not observed')
                snapshot=w.request('snapshot');save(out/(label+'-snapshot.json'),snapshot);snapshots.append(snapshot)
        require(snapshots[0]['canonicalSha256']==snapshots[1]['canonicalSha256'] and snapshots[0]['hashScope']==snapshots[1]['hashScope'],'hooked/unhooked experiment differs')
        report.update(hooked_unhooked_equal=True,final_hash=snapshots[0]['canonicalSha256'],hash_scope=snapshots[0]['hashScope'],ok=True)
        report['artifacts']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}
    except Exception as e:report['error']=str(e)
    finally:verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','comparison','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])


def main(argv=None):
    import sys
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--equal-marker-experiment' in argv:
        argv.remove('--equal-marker-experiment');return controlled(argv)
    return capture_main(argv,capture_recipe=recipe,comparator=compare_window,start=START,end=END,output_name='exit-tally-movie',
        scope='continuous P1 actor/service/tracking/tally/marker through bounded 5132 and 5188; explicit world/control/transition feeds; 53F2 score path, palette consumer and frame scheduling excluded')

if __name__=='__main__':raise SystemExit(main())
