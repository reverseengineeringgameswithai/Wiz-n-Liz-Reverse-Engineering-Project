"""Owned ordinary-movie evidence for retained 6D8C, E918 and spawned particles."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from rom import ROOT,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import PRESETS,verify_executable
from genesis_actor_capture import save,require,block,be
from genesis_actions_capture import check_worker
from genesis_movie_actor_capture import MOVIE_SHA256,INPUT_SHA256
from terrain_cases import encode_cases
START,END=1066,1100
EMITTER=0xffff2b76
SOURCES=('tools/genesis_trail_capture.py','tools/genesis_actor_capture.py','tools/genesis_actions_capture.py','tools/genesis_movie_actor_capture.py')


def recipe():
    return dict(pcs=[0x6986,0x69a4,0x69aa,0x69b6,0x69bc,0x69c0,0x69c2,0x69ce,0x6d8c,0x6dde,0x6e30,
        0x6db4,0x6dc2,0x6dd0,0x6ddc,0x5a9a,0x5aa0,0x5ae2,0xf994,0xf9a8,0xf9ce,0xf76c,0xfaa4,0xfaba,0x12646,0xe918,0xe946],
        registers=True,returns=False,maxEvents=20000,
        ranges=[dict(label=l,domain='68K RAM',offset=o,length=n) for l,o,n in [('emitter',0x2b76,78),('owner',0x1ab4,78),('owner_link',0x690,4),('random',0xbac,8),('free',0x3008,280)]]+
        [dict(label=l,domain='68K RAM',register=reg,offset=0,length=n) for l,reg,n in [('object','M68K A6',78),('allocated','M68K A5',78),('stack','M68K A7',16)]])


def emitter_fields(b):
    require(len(b)==78 and be(b,0x16,4)==0x6d8c and be(b,0x46,4)==0x12646 and be(b,0x4a,4)==0xffff0690 and be(b,0x14)==0,'emitter layout/owner differs')
    return (be(b,2),be(b,4),be(b,0x36),*(be(b,i) for i in range(0x22,0x36,2)),b[0],be(b,6),be(b,8),be(b,10),b[12],b[13],be(b,14),be(b,18),1)


def particle_fields(b):
    require(len(b)==78 and be(b,0x16,4)==0x5ae2 and be(b,0x1a,4)==0xfaa4 and be(b,0x46,4)==0x12646 and be(b,0x14)==0,'particle selectors differ')
    return (be(b,2),be(b,4),be(b,18),b[0],be(b,6),be(b,8),be(b,10),b[12],b[13],be(b,14))


def random_fields(e):return (be(block(e,'random'),0,4),be(block(e,'random'),4,4))


def validate_chunks(chunks,writes,identity):
    require(len(chunks)==END-START and len(writes)==END-START,'trail capture frame extent differs')
    events=[];native=[]
    for frame,t,w in zip(range(START,END),chunks,writes):
        require(t['identity']==identity and t['dropped']==0 and t['overflow'] is False and t['error'] is None,'incomplete trail routine evidence')
        require(w['identity']==identity and w['dropped']==0 and len(w['events'])<=w['capacity'],'incomplete trail write evidence')
        for stream in (t['events'],w['events']):
            require(all(e['frame']==frame for e in stream) and all(a['sequence']<b['sequence'] for a,b in zip(stream,stream[1:])),'trail chunk order/frame differs')
        require(all(e['kind']=='entry' for e in t['events']) and all(e['type'] in (4,65536) for e in w['events']),'trail hook types differ')
        require(sum(e['type']==65536 for e in w['events'])==4,'trail poll cadence differs')
        events.extend(t['events']);native.extend(e for e in w['events'] if e['type']==4)
    require(all(a['sequence']<b['sequence'] for a,b in zip(events,events[1:])),'trail global order differs')
    return events,native


def phase_tail(es,begin,end):
    selected=[e for e in es if begin['sequence']<=e['sequence']<=end['sequence'] and e['registers']['M68K A6']==begin['registers']['M68K A6']]
    require([e['pc'] for e in selected[-4:]]==[0x69bc,0x69c0,0x12646,0x69c2],'trail service order differs')
    done,call,service,ret=selected[-4:];sp=begin['registers']['M68K A7']
    require(all(e['registers']['M68K A7']==sp for e in (done,call,ret)) and service['registers']['M68K A7']==sp-4 and be(block(service,'stack'),0,4)==0x69c2,'trail service stack differs')
    require(call['registers']['M68K A0']==0x12646 and all(block(e,k)==block(done,k) for e in (call,service,ret) for k in ('object','random','owner','free')),'trail service changes state')
    return selected


def validate(events,native):
    pairs=[];births=[];previous=None;random_previous=None
    for frame in range(START,END):
        es=[e for e in events if e['frame']==frame];own=[e for e in es if e['registers']['M68K A6']==EMITTER]
        start,=[e for e in own if e['pc']==0x69aa];handler,=[e for e in own if e['pc']==0x6d8c];done,=[e for e in own if e['pc']==0x69c2]
        require(start['sequence']<handler['sequence']<done['sequence'],'emitter phase order differs')
        require(be(block(start,'owner_link'),0,4)==0xffff1ab4 and block(start,'owner')==block(done,'owner'),'resolved owner differs/changes')
        if previous is not None:require(emitter_fields(block(start,'emitter'))==previous and random_fields(start)==random_previous,'external retained-state mutation')
        require(handler['registers']['M68K A7']==start['registers']['M68K A7']-4 and be(block(handler,'stack'),0,4)==0x69bc,'emitter entry stack differs')
        tail=phase_tail(es,start,done);require(any(e['pc']==0x6e30 and e['registers']['M68K A5']==0xffff0690 for e in tail),'emitter owner link not restored')
        born=[e for e in own if e['pc']==0x6ddc];require(len(born)<=1,'multiple emitter allocations');births+=born
        allocations=[e for e in own if e['pc']==0xf994];require(len(allocations)==len(born),'missing emitter allocator')
        calls=[e for e in own if e['pc']==0xe918];returns=[e for e in own if e['pc']==0xe946]
        require(len(calls)==len(returns)==2*len(born),'random call count differs')
        for i,(a,b) in enumerate(zip(calls,returns)):
            require(a['sequence']<b['sequence'] and be(block(a,'stack'),0,4)==(0x6db8,0x6dc6)[i] and block(a,'stack')==block(b,'stack') and a['registers']['M68K A7']==b['registers']['M68K A7']==handler['registers']['M68K A7']-8,'RNG caller/return differs')
        if born:
            a=allocations[0];init,=[e for e in own if e['pc']==0xf9ce];particle=born[0];address=particle['registers']['M68K A5']
            require(be(block(a,'stack'),0,4)==0x5aa0 and a['registers']['M68K A7']==handler['registers']['M68K A7']-12,'allocator caller differs')
            free=block(a,'free');head=be(free,276,4);require(0xffff3010<=head<=0xffff311c and head%4==0,'allocator free stack differs')
            require(address==be(free,(head&65535)-0x300c,4) and be(block(init,'free'),276,4)==head-4,'allocator pop/slot differs')
            require(0xffff1b50<=address<0xffff3008 and (address-0xffff1b50)%78==0,'allocated address not a world slot')
            require(particle_fields(block(particle,'allocated'))[3:]==(133,227,227,234,2,2,234),'particle initialization differs')
        previous=emitter_fields(block(done,'emitter'));random_previous=random_fields(done)
        pairs.append(dict(start=start,end=done,birth=born[0] if born else None))
    require(len(births)==8,'ordinary emitter cadence changed')
    # Only this client owns RNG writes in this selected interval; no global RNG
    # isolation outside the interval is inferred. Native callbacks report next PC.
    rng_writes=[e for e in native if e['address']<0xff0bb4 and 0xff0bac<e['address']+e['width']]
    require(len(rng_writes)==64 and all(e['cpu']=='M68K' and e['registers']['M68K A6']==EMITTER and (e['pc'],e['address'],e['width']) in
            ((0xe928,0xff0bac,2),(0xe930,0xff0bae,2),(0xe938,0xff0bae,2),(0xe944,0xff0bb0,2),(0xe944,0xff0bb2,2),(0xe944,0xff0bb0,4)) for e in rng_writes),'unmodeled random writer')
    require(all(e['registers']['M68K A6']==EMITTER for e in events if e['pc']==0xe918),'foreign RNG invocation')
    emitter_writes=[e for e in native if e['address']<0xff2bc4 and 0xff2b76<e['address']+e['width']]
    for e in emitter_writes:
        offset=e['address']-0xff2b76;pc=e['pc']
        own=(0x6d90<=pc<=0x6e30 and e['width']==2 and offset in (2,4,*range(0x22,0x38,2)))
        present=(0xf76c<=pc<0xf850 and (offset,e['width']) in ((0,1),(6,2),(12,1)))
        clear=(pc==0xb12a and offset==0x14 and e['width']==2 and e['value']==0)
        require(e['cpu']=='M68K' and e['registers']['M68K A6']==EMITTER and (own or present or clear),'unmodeled emitter writer')
    lives=[]
    for birth in births:
        address=birth['registers']['M68K A5'];b=particle_fields(block(birth,'allocated'));updates=[];last=b
        for begin in [e for e in events if e['pc']==0x69aa and e['registers']['M68K A6']==address and e['sequence']>birth['sequence']]:
            require(particle_fields(block(begin,'object'))==last,'particle changed outside its phase')
            es=[e for e in events if e['frame']==begin['frame']];end,=[e for e in es if e['pc']==0x69c2 and e['registers']['M68K A6']==address]
            tail=phase_tail(es,begin,end);require(sum(e['pc']==0x5ae2 for e in tail)==1,'particle return-only handler skipped')
            released=any(e['pc']==0xfaa4 for e in tail);last=particle_fields(block(end,'object'))
            require((last[3]==0)==released,'particle release mode differs');updates.append((begin,end,released))
            if released:break
        require(updates and updates[0][0]['frame']==birth['frame']+int(address<EMITTER),'birth slot ordering differs')
        require([e['frame'] for e,_,_ in updates]==list(range(updates[0][0]['frame'],updates[-1][0]['frame']+1)),'particle update cadence differs')
        require(len(updates)<=16 and (len(updates)==16)==updates[-1][2],'particle lifetime differs')
        lives.append(dict(birth=birth,address=address,updates=updates))
    return pairs,lives,dict(emitter_calls=len(pairs),spawns=len(births),random_calls=16,random_writes=len(rng_writes),emitter_writes=len(emitter_writes),
        particle_calls=sum(len(l['updates']) for l in lives),complete_lifetimes=sum(l['updates'][-1][2] for l in lives),
        partial_lifetimes=sum(not l['updates'][-1][2] for l in lives),same_frame_births=sum(l['updates'][0][0]['frame']==l['birth']['frame'] for l in lives))


def compare(pairs,lives,native,out):
    rows=[]
    for pair in pairs:
        e=pair['start'];b=block(e,'owner');rows.append((*emitter_fields(block(e,'emitter')),1,be(b,2),be(b,4),1,*random_fields(e),1))
    def run(mode,rows,name):
        data=encode_cases(rows);atomic_write(out/(name+'.in'),data);cmd=[str(native),mode]
        p=subprocess.run(cmd,input=data,capture_output=True,timeout=30);atomic_write(out/(name+'.stdout'),p.stdout);atomic_write(out/(name+'.stderr'),p.stderr)
        require(p.returncode==0,'native trail replay failed: '+p.stderr.decode());result=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
        require(len(result)==len(rows),'native trail replay extent differs');return result,dict(command=cmd,output_sha256=hashlib.sha256(p.stdout).hexdigest())
    results,emitter=run('--sequence',rows,'emitter');spawned={}
    for pair,r in zip(pairs,results):
        e=pair['end'];born=pair['birth'];expected=(*emitter_fields(block(e,'emitter')),*random_fields(e),int(born is None),int(born is not None))
        if born:expected+=particle_fields(block(born,'allocated'));spawned[born['sequence']]=r[26:]
        require(r==expected,'retained native emitter/random/spawn mismatch at '+str(e['frame']))
    particles=[]
    for i,life in enumerate(lives):
        birth=spawned[life['birth']['sequence']];results,process=run('--particle-sequence',[(*birth,1)]*len(life['updates']),f'particle-{i}')
        for r,(_,end,released) in zip(results,life['updates']):require(r==(*particle_fields(block(end,'object')),int(released)),'native particle lifetime mismatch')
        particles.append(process|dict(birth_frame=life['birth']['frame'],first_frame=life['updates'][0][0]['frame'],last_frame=life['updates'][-1][0]['frame'],calls=len(results),released=life['updates'][-1][2]))
    return dict(emitter=emitter,particles=particles,scope='Retained emitter and RNG; owner position and allocation availability supplied per call. New particle state comes from native spawn output; lifetime state retained. No shared pool/order simulation.')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path);p.add_argument('--preset',choices=PRESETS,default='debug');p.add_argument('--fixture',type=Path);args=p.parse_args(argv)
    ext=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug';sys.path.insert(0,str(ext/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);rom=inspect_file();verify_expected(rom);native=verify_executable(args.preset,'wiznliz-trail')
    require(source['rom']['sha256']==rom['sha256'] and source['input_sha256']==INPUT_SHA256 and source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256 and not source['experimental_edits'] and not source['instrumentation'],'trail recording identity/edits differ')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/trail-movie')))
    report=dict(ok=False,preset=args.preset,start=START,end=END,recipe=recipe(),input_sha256=INPUT_SHA256,movie_sha256=MOVIE_SHA256,
        recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(),sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES},
        classification='fresh native comparison of captured ordinary movie' if args.fixture else 'fresh ordinary unchanged movie; no edits; owned workers',native_build=json.loads((native.parent/'provenance.json').read_text()))
    try:
        chunks=[];writes=[]
        if args.fixture:
            parent=json.loads(args.fixture.read_text());require(parent['ok'] is True and parent['rom_unchanged'] is True and parent['recipe']==recipe(),'failed/incompatible trail fixture')
            require(parent['recording_sha256']==report['recording_sha256'] and parent['sources']==report['sources'],'trail fixture inputs/validation sources differ')
            for name,h in parent['artifacts'].items():require(Path(name).name==name and hashlib.sha256((args.fixture.parent/name).read_bytes()).hexdigest()==h,'trail fixture artifact changed')
            def read(name):
                require(name in parent['artifacts'],'unhashed trail fixture input');return (args.fixture.parent/name).read_bytes()
            report['identity']=parent['identity'];require(report['identity']==source['start']['worker_open']['identity'],'trail fixture identity differs')
            for frame in range(START,END):chunks.append(json.loads(read(f'routines-{frame}.json')));writes.append(json.loads(read(f'writes-{frame}.json')))
            snap=json.loads(read('hooked.json'));snap2=json.loads(read('unhooked.json'));before=read('before.ram')
            require(json.loads(read('inputs.json'))==source['inputs'][START:END],'trail fixture physical rows differ')
            report['reference_report']=str(args.fixture);report['reference_report_sha256']=hashlib.sha256(args.fixture.read_bytes()).hexdigest()
        else:
            save(out/'inputs.json',source['inputs'][START:END])
            with WorkerClient([str(ext/'run-worker.sh'),'--storage',str(out/'hooked-worker')]) as w:
                s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];save(out/'capabilities.json',check_worker(w,s,ext))
                require(report['identity']==source['start']['worker_open']['identity'],'loaded trail identity differs');s.seek(START)
                before=w.read_bytes('68K RAM',0,65536);atomic_write(out/'before.ram',before)
                w.request('trace.configure',recipe());w.request('debug.trace.configure',{'mask':4|65536})
                for frame in range(START,END):
                    s.seek(frame+1);t=w.request('trace.drain');wr=w.request('debug.trace.drain')
                    save(out/f'routines-{frame}.json',t);save(out/f'writes-{frame}.json',wr);chunks.append(t);writes.append(wr)
                    require(t['dropped']==0 and t['overflow'] is False and t['error'] is None and wr['dropped']==0,'incomplete trail capture')
                snap=w.request('snapshot');save(out/'hooked.json',snap);atomic_write(out/'after.ram',w.read_bytes('68K RAM',0,65536))
            with WorkerClient([str(ext/'run-worker.sh'),'--storage',str(out/'unhooked-worker')]) as w:
                s=ReplaySession.from_recording(w,source);check_worker(w,s,ext);s.seek(END);snap2=w.request('snapshot');save(out/'unhooked.json',snap2)
        require(all(s['frame']==END and s['identity']==report['identity'] and not s['experimentalEdits'] for s in (snap,snap2)),'trail endpoint identity/frame differs')
        require(snap['canonicalSha256']==snap2['canonicalSha256'] and snap['hashScope']==snap2['hashScope'],'trail hooked/unhooked endpoint differs')
        report['endpoint']=dict(hooked=snap['canonicalSha256'],unhooked=snap2['canonicalSha256'],scope=snap['hashScope'])
        events,native_writes=validate_chunks(chunks,writes,report['identity']);pairs,lives,report['observation']=validate(events,native_writes)
        require(emitter_fields(before[0x2b76:0x2bc4])==emitter_fields(block(pairs[0]['start'],'emitter')) and before[0xbac:0xbb4]==block(pairs[0]['start'],'random'),'initial retained state changed before first phase')
        report['comparison']=compare(pairs,lives,native,out);report['observation'].update(routine_events=len(events),native_events=sum(len(w['events']) for w in writes));report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;report['artifacts']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()};save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','observation','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
