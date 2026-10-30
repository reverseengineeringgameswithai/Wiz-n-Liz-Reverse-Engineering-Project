"""Unedited user movie: continuous actor reversal, allocation, owned effect lifetime."""
import argparse
from collections import Counter
import hashlib
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
from reversal_cases import decode_actor_rows,split_actor
from terrain_cases import encode_cases

WINDOWS=((1048,1090),(2170,2220))


def recipe():
    r=actor_recipe()
    r['pcs']+= [0xa818,0xa9de,0xa87a,0xaa3e,0xf994,0xf9a8,0xf9ce,0xf76c,0xfaa4,0xfaba,0xa87c,0xaa40,0x69b6,0x69bc,0x816,0x81c]
    r['ranges'] += [{'label':label,'domain':'68K RAM','register':reg,'offset':0,'length':78}
                    for label,reg in (('object','M68K A6'),('allocated','M68K A5'))]
    r['ranges'] += [{'label':'free','domain':'68K RAM','offset':0x3008,'length':280}]
    return r


def effect_fields(data):
    handler=be(data,0x16,4)
    require(handler in (0xa87c,0xaa40) and be(data,0x1a,4)==0xfaa4,'unknown dependent handler/callback')
    require(be(data,0x22,4)==0xffff1ab4,'effect owner differs')
    require(be(data,0x46,4)==0x12646 and be(data,0x14)==0,'effect service fields differ')
    return (1,int(handler==0xaa40),be(data,2),be(data,4),be(data,18),data[0],be(data,6),be(data,8),be(data,10),data[12],data[13],be(data,14))


def validate_effects(trace):
    # Caller already validates schema, overflow and monotonic sequence globally.
    allocations=[];births=[];lifetimes={};allocation=selected=None
    for e in trace['events']:
        pc=e['pc'];regs=e['registers'];a6=regs['M68K A6'];a5=regs['M68K A5']
        if a6==0xffff1ab4 and pc==0xf994:
            require(allocation is None,'nested allocation');allocation=e
            require(be(block(e,'stack'),0,4) in (0xa81c,0xa9e2),'allocation caller differs')
        elif a6==0xffff1ab4 and pc==0xf9a8:
            require(allocation is not None and selected is None,'unpaired allocator selection');selected=e
        elif a6==0xffff1ab4 and pc==0xf9ce:
            require(allocation is not None and selected is not None,'unmatched allocation return')
            before=block(allocation,'free');after=block(e,'free');head=be(before,276,4)
            require(0xffff300c<=head<=0xffff311c and head%4==0,'free head outside observed stack')
            require(be(after,276,4)==head-4 and before[:276]==after[:276],'allocation pop differs')
            require(a5==be(before,(head&65535)-0x3008-4,4) and 0xffff1b50<=a5<0xffff3008 and (a5-0xffff1b50)%78==0,'returned object differs')
            require(regs['M68K A7']==allocation['registers']['M68K A7'],'allocator stack imbalance')
            require(block(e,'stack')==block(allocation,'stack'),'allocator return address differs')
            obj=block(e,'allocated')
            require(obj[0]==0x80 and be(obj,0x12)==0 and be(obj,0x14)==0 and be(obj,6)==541 and be(obj,0x16,4)==0x12646 and be(obj,0x46,4)==0x12646,'allocator initializer differs')
            allowed={0,6,7,*range(18,26),*range(70,74)};previous=block(selected,'allocated')
            require(all(obj[i]==previous[i] for i in range(78) if i not in allowed),'uncontracted allocator write')
            require(not (regs['M68K SR']&8),'allocator success negative flag differs')
            allocations.append({'start':allocation,'end':e,'address':a5});allocation=selected=None
        elif a6==0xffff1ab4 and pc in (0xa87a,0xaa3e):
            require(allocations and allocations[-1]['address']==a5 and allocations[-1]['end']['frame']==e['frame'],'spawn without allocation')
            require(a5 not in lifetimes,'object reused during lifetime window')
            f=effect_fields(block(e,'allocated'));births.append(e)
            require(be(block(e,'stack'),0,4)==(0xa7ec if pc==0xa87a else 0xa9b2),'spawn tail return differs')
            lifetimes[a5]={'birth':e,'fields':f,'pairs':[],'pending':None,'present':None,'handler':None,'release':None,'release_return':None,'released':False}
        elif a6 in lifetimes:
            life=lifetimes[a6]
            if life['released']:continue # Later unrelated reuse is outside this lifetime.
            if pc==0xf76c:
                require(life['pending'] is None,'nested effect scheduler');life['pending']=e
                require(effect_fields(block(e,'object'))==life['fields'],'external effect mutation breaks continuity')
                require(block(e,'object')[0]&0x80,'inactive effect scheduled')
                require(be(block(e,'stack'),0,4) in (0x816,0x69b6),'effect scheduler caller differs')
            elif pc in (0x816,0x69b6):
                require(life['pending'] is not None and life['present'] is None,'unpaired effect presentation')
                require(regs['M68K A7']==life['pending']['registers']['M68K A7']+4,'effect presentation return stack differs');life['present']=e
            elif pc==0xfaa4:
                require(life['pending'] is not None and life['release'] is None,'unpaired release');life['release']=e
                require(regs['M68K A7']==life['pending']['registers']['M68K A7'],'release tail stack differs')
                require(block(e,'stack')==block(life['pending'],'stack'),'release caller differs')
            elif pc==0xfaba:
                require(life['release'] is not None and life['release_return'] is None,'unpaired release return');life['release_return']=e
                before=block(life['release'],'free');after=block(e,'free');head=be(before,276,4);index=(head&65535)-0x3008
                require(0<=index<=272 and index%4==0,'release stack bounds')
                expected=bytearray(before);expected[index:index+4]=a6.to_bytes(4,'big');expected[276:280]=(head+4).to_bytes(4,'big')
                require(after==expected and block(e,'object')[0]==0,'release push/mode differs')
            elif pc in (0xa87c,0xaa40):
                require(life['present'] is not None and life['handler'] is None,'effect handler order differs')
                require(pc==be(block(e,'object'),0x16,4),'effect selected handler differs')
                require(regs['M68K A7']==life['pending']['registers']['M68K A7'] and be(block(e,'stack'),0,4) in (0x81c,0x69bc),'effect handler return differs')
                life['handler']=e
            elif pc in (0x81c,0x69bc):
                begin=life['pending'];require(begin is not None and life['present'] is not None and life['handler'] is not None,'incomplete effect call')
                require(e['frame']==begin['frame'] and regs['M68K A7']==begin['registers']['M68K A7']+4,'effect boundary/frame differs')
                before=block(begin,'object');after=block(e,'object');allowed={0,2,3,6,7,12}
                require(all(before[i]==after[i] for i in range(78) if i not in allowed),'uncontracted effect write')
                require(be(block(begin,'actor'),2)==be(block(e,'actor'),2),'owner moved during effect invocation')
                fires=(before[0]&5)==5 and before[12]==1 and be(before,6)==be(before,14)
                require(bool(life['release'])==fires and bool(life['release_return'])==fires,'missing/spurious release')
                life['pairs'].append((begin,e,fires));life['fields']=effect_fields(after);life['released']=fires
                life['pending']=life['present']=life['handler']=life['release']=life['release_return']=None
    require(allocation is None and len(births)==1,'expected one P1 reversal allocation in window')
    require(all(l['released'] and l['pending'] is None and len(l['pairs'])==12 for l in lifetimes.values()),'incomplete effect lifetime')
    return allocations,births,lifetimes


def compare_window(trace,directory,native,scene,bank,start,end):
    actor_trace=trace|{'events':[e for e in trace['events'] if e['pc'] in actor_recipe()['pcs']]}
    pairs=validate_trace(actor_trace,start,end)
    # Validate order/overflow against the full stream as well, including effects.
    require(trace['dropped']==0 and trace['overflow'] is False and trace['error'] is None,'incomplete full trace')
    require(all(a['sequence']<b['sequence'] for a,b in zip(trace['events'],trace['events'][1:])),'full trace order differs')
    require(all(start<=e['frame']<end and e['kind']=='entry' for e in trace['events']),'full event boundary differs')
    allocations,births,lifetimes=validate_effects(trace)
    inputs=[input_case(p['start']) for p in pairs]
    for name,data in [('scene.bin',scene),('bank.bin',bank),('actor-cases.txt',encode_cases(inputs))]:atomic_write(directory/name,data)
    command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),'--reversal-sequence']
    proc=subprocess.run(command,input=encode_cases(inputs),capture_output=True,timeout=60)
    atomic_write(directory/'actor.stdout',proc.stdout);atomic_write(directory/'actor.stderr',proc.stderr)
    require(proc.returncode==0,'native actor failed: '+proc.stderr.decode());rows=decode_actor_rows(proc.stdout,len(pairs));native_actor={}
    for row,pair in zip(rows,pairs):
        core,spawns=split_actor(row);frame=pair['start']['frame'];native_actor[frame]=core
        require(core[:18]==snapshot_fields(pair['end'],be(block(pair['start'],'actor'),0x1a,4)),f'actor divergence at {frame}')
        require(tuple(tuple(core[j:j+4]) for j in range(23,len(core),4))==pair['sounds'],'actor sound mismatch')
        expected=tuple(effect_fields(block(b,'allocated')) for b in births if b['frame']==frame)
        require(spawns==expected,f'spawn mismatch at {frame}')
    total=0;effects=[]
    for address,life in lifetimes.items():
        cases=[];expected=[]
        for begin,end_event,released in life['pairs']:
            owner=block(begin,'actor');core=native_actor[begin['frame']]
            require((be(owner,2),be(owner,4))==core[1:3],'effect owner differs from retained native actor output')
            cases.append((*effect_fields(block(begin,'object')),1,*core[1:3],1))
            expected.append((*effect_fields(block(end_event,'object')),int(released),1))
        effect_command=command[:-1]+['--effect-sequence'];p=subprocess.run(effect_command,input=encode_cases(cases),capture_output=True,timeout=60)
        atomic_write(directory/'effect-cases.txt',encode_cases(cases));atomic_write(directory/'effect.stdout',p.stdout);atomic_write(directory/'effect.stderr',p.stderr)
        require(p.returncode==0,'native effect failed: '+p.stderr.decode())
        observed=[tuple(map(int,l.split())) for l in p.stdout.splitlines()];require(observed==expected,'native effect lifetime divergence')
        total+=len(cases);effects.append({'address':hex(address),'birth_frame':life['birth']['frame'],'release_frame':life['pairs'][-1][1]['frame'],
            'calls':len(cases),'command':effect_command,'output_sha256':hashlib.sha256(p.stdout).hexdigest()})
    return {'ok':True,'actor_calls':len(pairs),'effect_calls':total,'allocations':len(allocations),'effects':effects,
            'actor_command':command,'actor_output_sha256':hashlib.sha256(proc.stdout).hexdigest(),
            'handler_hits':dict(Counter(hex(e['pc']) for p in pairs for e in p['handlers'])),
            'callback_hits':dict(Counter(hex(e['pc']) for p in pairs for e in p['callbacks'])),
            'sound_requests':sum(len(p['sounds']) for p in pairs)}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path);p.add_argument('--preset',choices=('debug','release','sanitize'),default='debug')
    p.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug');args=p.parse_args(argv)
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity);native=verify_executable(args.preset,'wiznliz-actor')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[],'movie inputs/edits differ')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256,'movie identity differs')
    require(source['instrumentation']=={} and source['rom']['sha256']==identity['sha256'],'source baseline/ROM differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/reversal-movie')))
    report={'ok':False,'windows':[],'recipe':recipe(),'scope':'continuous actor and owned reversal effect lifetimes; external world controls/parameters/scratch; no whole-frame parity',
            'recording_sha256':hashlib.sha256(args.recording.read_bytes()).hexdigest(),'movie_sha256':MOVIE_SHA256,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_build':json.loads((native.parent/'provenance.json').read_text())}
    try:
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'hooked-worker')]) as w:
            s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];report['capabilities']=w.request('capabilities')
            require(all(report['capabilities']['capabilities'][k] for k in ('frameAdvance','routineTrace','memoryInspection')),'worker capabilities missing')
            manifest=json.loads((external/'local/runtime/genesis-build.json').read_text())
            require(manifest['buildId']==BUILD_ID and s.opened['identity']['build']==manifest,'runtime generation differs')
            expected={Path(k).name:v for k,v in manifest['binaries'].items()}|{'GenesisWorker.exe':manifest['workerSha256']}
            require(all(expected.get(k)==v for k,v in s.opened['identity']['binaries'].items()),'loaded binary hashes differ')
            for start,end in WINDOWS:
                directory=out/f'{start}-{end}';directory.mkdir();s.seek(start)
                before=w.read_bytes('68K RAM',0,65536);scene,bank,terrain=terrain_fixture(before);atomic_write(directory/'before.ram',before)
                w.request('trace.configure',recipe());s.seek(end);trace=w.request('trace.drain');save(directory/'trace.json',trace)
                require(trace['identity']==s.opened['identity'],'trace identity differs')
                after=w.read_bytes('68K RAM',0,65536);atomic_write(directory/'after.ram',after)
                require(terrain_fixture(after)[:2]==(scene,bank),'terrain endpoint changed')
                result=compare_window(trace,directory,native,scene,bank,start,end);save(directory/'comparison.json',result)
                snap=w.request('snapshot');save(directory/'snapshot.json',snap)
                report['windows'].append({'start':start,'end':end,'classification':'ordinary unedited recorded gameplay','terrain':terrain,'comparison':result,
                    'hooked_hash':snap['canonicalSha256'],'hash_scope':snap['hashScope'],
                    'artifacts':{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in directory.iterdir() if f.is_file()}})
                w.request('trace.configure',{})
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'unhooked-worker')]) as w:
            s=ReplaySession.from_recording(w,source)
            for window in report['windows']:
                s.seek(window['end']);snap=w.request('snapshot')
                require(snap['canonicalSha256']==window['hooked_hash'] and snap['hashScope']==window['hash_scope'],'hooked/unhooked replay differs')
                window['unhooked_hash']=snap['canonicalSha256']
        report['actor_calls']=sum(w['comparison']['actor_calls'] for w in report['windows'])
        report['effect_calls']=sum(w['comparison']['effect_calls'] for w in report['windows']);report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','actor_calls','effect_calls','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
