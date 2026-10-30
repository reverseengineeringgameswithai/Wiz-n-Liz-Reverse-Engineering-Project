"""Unedited movie transition: continuous actor wrapper plus independently scheduled timer calls."""
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
from genesis_actor_capture import block,be,save,require,terrain_fixture
from genesis_dispatch_capture import recipe as dispatch_recipe,tracking_fields
from genesis_actions_capture import action_case,shared_fields,check_worker
from genesis_movie_actor_capture import validate_trace,snapshot_fields,MOVIE_SHA256,INPUT_SHA256
from transition_cases import decode
from actions_cases import split
from terrain_cases import encode_cases

START,END=1516,1533
EXTRA=(0x710e,0x7126,0xa148,0x7118,0x7130,0x13208,0x1324c,0x1345a,0x134b0,0x134d4,0x6986,0xebf2)


def recipe():
    r=dispatch_recipe();r['pcs']=list(dict.fromkeys(r['pcs']+list(EXTRA)))
    r['ranges'] += [{'label':l,'domain':'68K RAM','offset':o,'length':n} for l,o,n in
        [('transition',0xb90,20),('palette_flags',0xedc,4),('requested_position',0x4446,4),('saved_position',0x732,4)]]
    return r


def transition_fields(e,original=None):
    data=block(e,'transition');require(len(data)==20,'transition extent differs')
    require(all(len(block(e,l))==4 for l in ('palette_flags','requested_position','saved_position')),'transition coordinate/flag extent differs')
    curves=[]
    for i in (8,12,16):
        v=be(data,i,4)
        if v not in (0x1356a,0x135aa,0x135ea):
            require(original is None or v==be(block(original,'transition'),i,4),'unmodeled curve changed')
            curves.append(0)
        else:curves.append({0x1356a:1,0x135aa:2,0x135ea:3}[v])
    return (*(be(data,i) for i in range(0,8,2)),*curves,
        *(be(block(e,label),i) for label in ('palette_flags','requested_position','saved_position') for i in (0,2)))


def validate(trace,start,end):
    pairs=validate_trace(trace,start,end);events=trace['events'];timers=[]
    labels=('actor','control','scratch','gate','action_globals','mailbox','tracking_selector','transition','palette_flags','requested_position','saved_position')
    for p in pairs:
        frame=p['start']['frame'];es=[e for e in events if e['frame']==frame]
        def one(pc):
            selected=[e for e in es if e['pc']==pc];require(len(selected)==1,'boundary count differs at '+hex(pc));return selected[0]
        entry,returned=one(0xf8f6),one(0x6986);p['wrapper']=entry;p['return']=returned
        sp=entry['registers']['M68K A7']
        require(be(block(entry,'stack'),0,4)==returned['pc'] and returned['registers']['M68K A7']==sp+4,'wrapper actual return differs')
        require(all(entry['registers'][r]==returned['registers'][r] for r in ('M68K A5','M68K A6')),'wrapper owner differs')
        require(entry['sequence']<p['start']['sequence']<p['end']['sequence']<returned['sequence'],'wrapper order differs')
        require(all(block(entry,l)==block(p['start'],l)==block(p['presentation'],l) for l in labels),'inactive presentation changed state')
        require(not p['callbacks'] and not p['sounds'] and len(p['handlers'])==1,'unexpected transition handler continuation/effect')
        require(block(entry,'action_globals')[:8]==block(p['end'],'action_globals')[:8] and block(entry,'mailbox')==block(p['end'],'mailbox'),'uncontracted shared-global/mailbox write')
        handler=p['handlers'][0];pc=handler['pc'];require(pc==(0x710e if frame==start else 0x7126),'transition handler sequence differs')
        require(be(block(handler,'actor'),0x4a,4)==0xffff0690,'transition associated control differs')
        coast=one(0xa148);coast_return=one(0x7118 if pc==0x710e else 0x7130)
        require(coast['registers']['M68K A7']==sp-8 and be(block(coast,'stack'),0,4)==coast_return['pc'],'coasting return differs')
        require(handler['sequence']<coast['sequence']<coast_return['sequence']<p['end']['sequence'],'coasting call order differs')
        require(coast_return['registers']['M68K A7']==sp-4 and be(block(coast_return,'stack'),0,4)==0xf906,'coasting caller stack differs')
        if pc==0x710e:
            init,last=one(0x13208),one(0x1324c)
            require(coast_return['sequence']<init['sequence']<last['sequence']<p['end']['sequence'],'initializer tail order differs')
            require(all(e['registers']['M68K A7']==sp-4 and be(block(e,'stack'),0,4)==0xf906 for e in (init,last)),'initializer lost caller return')
        tail=[e for e in es if p['end']['sequence']<e['sequence']<returned['sequence']]
        selector=tracking_fields(entry)[1];rts=0xf936 if selector==65535 else 0xf928
        require([e['pc'] for e in tail]==[0xf90a,0x12646,0xf90c,rts],'wrapper tail differs')
        require(tail[0]['registers']['M68K A0']==be(block(p['end'],'actor'),0x46,4)==0x12646,'selected service differs')
        require(all(e['registers']['M68K A7']==sp for e in (tail[0],tail[2],tail[3])),'wrapper tail stack differs')
        require(all(e['registers']['M68K A5']==entry['registers']['M68K A5'] for e in tail),'wrapper tail owner differs')
        require(tail[1]['registers']['M68K A7']==sp-4 and be(block(tail[1],'stack'),0,4)==0xf90c,'service return differs')
        require(all(block(p['end'],l)==block(e,l) for e in tail[:3] for l in labels),'return-only service changed state')
        require(all(block(p['end'],l)==block(returned,l) for l in labels if l!='control'),'wrapper changed state after handler')
        require(all(block(tail[-1],l)==block(returned,l) for l in labels),'wrapper RTS changed state')
        c=block(returned,'control');before=block(entry,'control')
        require(all(before[i]==c[i] for i in range(len(c)) if i not in range(0x42,0x46)),'uncontracted control write')
        x,y=be(block(returned,'actor'),2),be(block(returned,'actor'),4)
        require(tracking_fields(returned)[2:]==((0xff80,0xff80) if selector==65535 else ((x+4)&65535,(y+6)&65535)),'wrapper tracking differs')
        if p is not pairs[0]:require(tracking_fields(entry)[2:]==tracking_fields(pairs[len(timers)-1]['return'])[2:],'tracking continuity changed')
        # Timer is a separate real call earlier in the frame, never hidden in actor invocation.
        timer,done=one(0x1345a),one(0xebf2);tsp=timer['registers']['M68K A7']
        returns=[e for e in es if e['pc'] in (0x134b0,0x134d4)]
        require(len(returns)==1,'timer RTS count differs');last=returns[0]
        require(timer['sequence']<last['sequence']<done['sequence']<entry['sequence'],'timer/actor ordering differs')
        require(last['registers']['M68K A7']==tsp and be(block(last,'stack'),0,4)==0xebf2,'timer pending return differs')
        require(all(block(last,l)==block(done,l) for l in labels),'timer RTS changed state')
        require(be(block(timer,'stack'),0,4)==done['pc'] and done['registers']['M68K A7']==tsp+4,'timer actual return differs')
        require(all(block(timer,l)==block(done,l) for l in labels if l not in ('transition','palette_flags')),'timer changed unrelated state')
        require(block(timer,'palette_flags')[2:]==block(done,'palette_flags')[2:],'timer changed palette scope')
        require(block(done,'transition')==block(entry,'transition'),'external transition fields changed before actor')
        if timers:require(block(timer,'transition')==block(pairs[len(timers)-1]['return'],'transition'),'external transition fields changed between invocations')
        timers.append((timer,done))
    return pairs,timers


def compare_window(trace,directory,native,scene,bank,start,end):
    pairs,timers=validate(trace,start,end)
    for name,data in [('scene.bin',scene),('bank.bin',bank)]:atomic_write(directory/name,data)
    results={}
    for label,mode,boundaries in (('continuous-wrapper','--transition-sequence',[(p['wrapper'],p['return']) for p in pairs]),
                                  ('timer','--transition-timer',timers)):
        cases=[(*action_case(a),*tracking_fields(a),*transition_fields(a)) for a,b in boundaries]
        command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),mode]
        atomic_write(directory/(label+'.cases'),encode_cases(cases));proc=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60)
        atomic_write(directory/(label+'.stdout'),proc.stdout);atomic_write(directory/(label+'.stderr'),proc.stderr)
        require(proc.returncode==0,label+' failed: '+proc.stderr.decode())
        for row,(a,b) in zip(decode(proc.stdout,len(cases)),boundaries):
            require(row[-13:]==transition_fields(b,a),f'{label} transition divergence at {a["frame"]}')
            require(row[-17:-13]==tracking_fields(b),f'{label} tracking divergence')
            core,shared,samples=split(row[:-17])
            require(core[:18]==snapshot_fields(b,be(block(a,'actor'),0x1a,4)),f'{label} actor divergence at {a["frame"]}')
            require(shared==shared_fields(b) and not samples and core[21]==0,f'{label} shared/effect divergence')
        results[label]={'calls':len(cases),'command':command,'output_sha256':hashlib.sha256(proc.stdout).hexdigest()}
    return {'ok':True,'comparisons':results,'handlers':dict(Counter(hex(p['handlers'][0]['pc']) for p in pairs)),
            'completion_frame':next(p['return']['frame'] for p in pairs if shared_fields(p['return'])[0]==7)}


def main(argv=None,*,capture_recipe=recipe,comparator=compare_window,start=START,end=END,output_name='transition-movie',
         scope='continuous native actor and tracking; separate timer calls; shared globals, saved/requested coordinates and scratch supplied by external world; palette consumer/world/frame scheduling excluded'):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path)
    p.add_argument('--preset',choices=('debug','release','sanitize'),default='debug')
    p.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug');args=p.parse_args(argv)
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity);native=verify_executable(args.preset,'wiznliz-actor')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[],'movie input/edit identity differs')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256,'movie identity differs')
    require(source['instrumentation']=={} and source['rom']['sha256']==identity['sha256'],'source baseline/ROM differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/'+output_name)))
    report={'ok':False,'start':start,'end':end,'recipe':capture_recipe(),'classification':'ordinary unedited user movie; no RAM/register/ROM edits',
            'scope':scope,
            'recording_sha256':hashlib.sha256(args.recording.read_bytes()).hexdigest(),'movie_sha256':MOVIE_SHA256,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'contract_sources':{str(Path(inspect.getsourcefile(f)).relative_to(ROOT)):hashlib.sha256(Path(inspect.getsourcefile(f)).read_bytes()).hexdigest() for f in (capture_recipe,comparator,validate_trace,action_case,transition_fields)},'native_build':json.loads((native.parent/'provenance.json').read_text())}
    try:
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'hooked-worker')]) as w:
            s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];report['capabilities']=check_worker(w,s,external);s.seek(start)
            before=w.read_bytes('68K RAM',0,65536);atomic_write(out/'before.ram',before);scene,bank,report['terrain']=terrain_fixture(before)
            w.request('trace.configure',capture_recipe());s.seek(end);trace=w.request('trace.drain');save(out/'trace.json',trace)
            require(trace['identity']==s.opened['identity'],'trace identity differs')
            after=w.read_bytes('68K RAM',0,65536);atomic_write(out/'after.ram',after)
            require(terrain_fixture(after)[:2]==(scene,bank),'terrain endpoints differ')
            report['comparison']=comparator(trace,out,native,scene,bank,start,end)
            snapshot=w.request('snapshot');save(out/'snapshot.json',snapshot)
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'unhooked-worker')]) as w:
            s=ReplaySession.from_recording(w,source);check_worker(w,s,external);s.seek(end);other=w.request('snapshot');save(out/'unhooked.json',other)
            require(other['canonicalSha256']==snapshot['canonicalSha256'] and other['hashScope']==snapshot['hashScope'],'hooked/unhooked replay differs')
            report['hooked_unhooked_equal']=True;report['hash_scope']=snapshot['hashScope'];report['final_hash']=snapshot['canonicalSha256']
        report['artifacts']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()};report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','comparison','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
