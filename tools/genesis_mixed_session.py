"""Retained P1/trail/reversal session and ordered shared allocation projection."""
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
from native_build import PRESETS,verify_executable
from genesis_actor_capture import save,require,block,be,terrain_fixture
from genesis_actions_capture import check_worker
from genesis_effect_session import recipe as effect_recipe,fixture_reader
from genesis_session_capture import recipe as session_recipe,validate_session,session_seed,physical_fields,control_fields
from genesis_dispatch_capture import tracking_fields
from genesis_reversal_capture import effect_fields,validate_effects
from genesis_movie_actor_capture import snapshot_fields,MOVIE_SHA256,INPUT_SHA256
from genesis_trail_capture import recipe as trail_recipe,emitter_fields,particle_fields,validate_chunks,validate as validate_trails,phase_tail
from terrain_cases import encode_cases
from genesis_return_only_evidence import return_only_fields,validate_phase as validate_return_only_phase,validate_write as validate_return_only_write
from genesis_collision_evidence import collision_fields,validate_inputs as validate_collision_inputs,validate_phase as validate_collision_phase
START,END=1066,1100
BASE,LIMIT,STRIDE=0xffff1b50,0xffff3008,78
SLOTS=(LIMIT-BASE)//STRIDE
OWNER,EMITTER=0xffff1ab4,0xffff2b76
SOURCES=('tools/genesis_mixed_session.py','tools/genesis_return_only_evidence.py','tools/genesis_collision_evidence.py','tools/genesis_effect_session.py','tools/genesis_trail_capture.py','tools/genesis_session_capture.py',
 'tools/genesis_reversal_capture.py','tools/genesis_dispatch_capture.py','tools/genesis_actions_capture.py','tools/genesis_movie_actor_capture.py','tools/genesis_actor_capture.py')


def recipe():
    r=effect_recipe();t=trail_recipe()
    r['pcs']=list(dict.fromkeys(r['pcs']+t['pcs']+[0x7808,0x7838,0x78ee,0x790e,0x7910,0x7a88,0x7ad4,0x7ca4,0x7cc6,0xf9e2,0x79b6,0x7cc8,0x7cea,0x7a4e,0xac5e,0xac78,0xac8e,0xac94,0xac9a,0x78f8,0x790c]))
    labels={x['label'] for x in r['ranges']};r['ranges'] += [x for x in t['ranges'] if x['label'] not in labels]
    r['ranges'] += [dict(label='private_gates',domain='68K RAM',offset=0x31a4,length=4),
                     dict(label='rise_gate',domain='68K RAM',offset=0x31b0,length=4),
                     dict(label='table_input',domain='68K RAM',offset=0x31bc,length=4),
                     dict(label='collision_mask',domain='68K RAM',offset=0x13ae,length=2),
                     dict(label='anchor',domain='68K RAM',offset=0x31c0,length=4)]
    return r


def slot(address):
    require(BASE<=address<LIMIT and (address-BASE)%STRIDE==0,'pointer is not a pool slot')
    return (address-BASE)//STRIDE


def free_fields(b):
    require(len(b)==280 and be(b,0,4)==0,'free stack extent/sentinel differs')
    head=be(b,276,4);require(0xffff300c<=head<=0xffff311c and head%4==0,'free stack head differs')
    values=[slot(be(b,i,4)) for i in range(4,(head&65535)-0x3008,4)]
    require(len(set(values))==len(values),'duplicate free slot');return values


def private_fields(b):
    require(len(b)==78 and be(b,0x16,4) in (0x7808,0x7ca4) and be(b,0x1a,4)==0 and be(b,0x46,4)==0x12646 and be(b,0x14)==0,'private selectors/service differ')
    # Unrepresented bytes are verified zero, not silently discarded private state.
    require(b[1]==0 and b[0x1e:0x46]==bytes(40),'unmodeled private object fields')
    links={0:0,0xffff0690:1,0xffff0838:2};link=be(b,0x4a,4)
    require(link in links,'unmapped private control identity')
    return (int(be(b,0x16,4)==0x7ca4),be(b,2),be(b,4),be(b,18),b[0],be(b,6),be(b,8),be(b,10),b[12],b[13],be(b,14),be(b,16),links[link])


def private_globals(ram):return (be(ram,0x31b0,4),be(ram,0x31a6),be(ram,0x31a4))


def validate_private_globals(events,writes,before,after):
    gates=private_globals(before)
    require(gates==(0,0,0) and private_globals(after)==gates,'ordinary private globals differ')
    for e in events:
        require((be(block(e,'rise_gate'),0,4),be(block(e,'private_gates'),2),be(block(e,'private_gates'),0))==gates,'private globals changed between hooks')
    for e in writes:
        require(not any(e['address']<hi and lo<e['address']+e['width'] for lo,hi in ((0xff31a4,0xff31a8),(0xff31b0,0xff31b4))),'unmodeled private global writer')
    return dict(rise_gate=gates[0],flags_gate=gates[1],hide_gate=gates[2],writes=0,
        scope='Seeded once. No writes in this ordinary window; producers remain outside the native session.')


def table_fields(b):
    require(len(b)==78 and be(b,0x16,4)==0x7a88 and be(b,0x1a,4)==0x79b6 and be(b,0x46,4)==0x12646 and be(b,0x14)==0,'table selectors/service differ')
    links={0:0,0xffff0690:1,0xffff0838:2};link=be(b,0x4a,4);cursor=be(b,0x2e,4)
    require(link in links,'unmapped table control identity')
    require(0x7a58<=cursor<0x7a88 and cursor%2==0,'unsupported table pointer')
    return (be(b,2),be(b,4),be(b,18),b[0],be(b,6),be(b,8),be(b,10),b[12],b[13],be(b,14),be(b,16),links[link],(cursor-0x7a58)//2,be(b,0x32),be(b,0x36))


def validate_table_input(events,writes,before,after):
    initial=before[0x31bc:0x31c0]
    require(initial==bytes.fromhex('00000050') and after[0x31bc:0x31c0]==initial,'ordinary table input differs')
    for e in events:
        require(block(e,'table_input')==initial,'table input changed between hooks')
        require(e['pc']!=0x7a4e,'unsupported callback writer executed')
    for e in writes:
        require(not (e['address']<0xff31c0 and 0xff31bc<e['address']+e['width']),'unmodeled table input writer')
    return dict(loop_count=be(initial,0),producer_countdown=be(initial,2),writes=0,
        producer_entries=sum(e['pc']==0x7cc8 for e in events),producer_prefix_exits=sum(e['pc']==0x7cea for e in events),
        scope='One retained loop-count seed; producer not scheduled natively. No writes, including transients, in this window.')


def validate_anchor(objects,events,writes,before,after):
    """FF31C0 names the retained 7B9C second member; no writer in this window."""
    value=be(before,0x31c0,4);i=slot(value)
    require(objects[i][0]==8,'FF31C0 does not name a retained return-only object')
    require(be(after,0x31c0,4)==value and all(be(block(e,'anchor'),0,4)==value for e in events),'FF31C0 changed in mixed window')
    for e in writes:require(not (e['address']<0xff31c4 and 0xff31c0<e['address']+e['width']),'FF31C0 writer in mixed window')
    return i


def object_fields(b):
    handler=be(b,0x16,4)
    if be(b,0x46,4)==0x78ee:return (7,*collision_fields(b))
    if handler==0x12646:return (8,*return_only_fields(b))
    if handler==0x7a88:return (6,*table_fields(b))
    if handler in (0x7808,0x7ca4):return (5,*private_fields(b))
    if handler==0x6d8c:return (4,*emitter_fields(b))
    if handler==0x5ae2:return (3,*particle_fields(b))
    if handler in (0xa87c,0xaa40):return (2,*effect_fields(b))
    raise ValueError('unknown managed pool object')


def initial(ram):
    require(len(ram)==65536,'initial pool RAM extent differs')
    free=free_fields(ram[0x3008:0x3120]);objects=[]
    for i in range(SLOTS):
        o=(BASE&65535)+i*STRIDE;b=ram[o:o+STRIDE]
        if i in free:require(not b[0]&128,'active slot on initial free list');objects.append((0,))
        else:
            obj=object_fields(b)
            require(b[0]&128 or obj[0]==8,'inactive managed initial slot')
            objects.append(obj)
    require(sum(o[0]==4 for o in objects)==1 and objects[slot(EMITTER)][0]==4,'unexpected initial emitter')
    return objects,free


def validate_pool(events,writes,before,after,pairs):
    globals_observed=validate_private_globals(events,writes,before,after)
    table_observed=validate_table_input(events,writes,before,after)
    collision_observed=validate_collision_inputs(events,writes,before,after,pairs)
    objects,free=initial(before);seed_free=list(free);generation=[0 if i in free else 1 for i in range(SLOTS)]
    anchor=validate_anchor(objects,events,writes,before,after)
    passive={i:bool(o[4]&128) for i,o in enumerate(objects) if o[0]==8}
    require(set(passive)=={52,58,59,60,61,62,66} and {i for i,a in passive.items() if not a}=={52,66},'ordinary return-only occupancy differs')
    expected=[];allocation=None;releasing=None;pending={};calls=Counter();begins=Counter();free_after={};rng_after={}
    for e in events:
        pc=e['pc'];a6=e['registers']['M68K A6'];a5=e['registers']['M68K A5'];frame=e['frame']
        if pc==0xf994:
            require(allocation is None and a6 in (OWNER,EMITTER) and free,'unmodeled allocation client/exhaustion')
            require(be(block(e,'stack'),0,4)==(0xa9e2 if a6==OWNER else 0x5aa0),'allocation caller differs')
            allocation=(e,free[-1]);calls['allocations']+=1
        elif pc==0xf9a8:
            require(allocation is not None and slot(a5)==free[-1]==allocation[1],'allocation order differs')
            free.pop();generation[slot(a5)]+=1
        elif pc==0xf9ce:
            require(allocation is not None and slot(a5)==allocation[1],'allocator return differs')
            require(e['registers']['M68K A7']==allocation[0]['registers']['M68K A7'] and block(e,'stack')==block(allocation[0],'stack'),'allocator return stack differs')
            allocation=None
        elif pc in (0xaa3e,0xa87a,0x6ddc):
            i=slot(a5);obj=object_fields(block(e,'allocated'));objects[i]=obj
            require((a6==OWNER and obj[0]==2) or (a6==EMITTER and obj[0]==3),'unknown pool birth')
            expected.append((frame,(0,i,generation[i],*obj)))
        elif pc==0xfaa4:
            i=slot(a6);require(releasing is None and i not in free and objects[i][0] in (2,3),'unmodeled release')
            releasing=(e,i);calls['releases']+=1
        elif pc==0xfaba:
            require(releasing is not None and slot(a6)==releasing[1],'release return differs')
            require(e['registers']['M68K A7']==releasing[0]['registers']['M68K A7'] and block(e,'stack')==block(releasing[0],'stack'),'release return stack differs')
            free.append(slot(a6));releasing=None
        require(free_fields(block(e,'free'))==free,'free list changed outside audited allocation/release')
        if pc==0x69aa:
            i=slot(a6);begins[frame]+=1;b=block(e,'object')
            if b[0]&128 or (i not in free and objects[i][0]==8):
                require(i not in free and object_fields(b)==objects[i],'managed continuity/occupancy differs')
                pending[i]=e
            else:require(i in free,'unaccounted inactive occupied slot')
        elif pc==0x69c2 and BASE<=a6<LIMIT:
            i=slot(a6)
            if i in pending:
                begin=pending.pop(i);obj=object_fields(block(e,'object'));released=i in free
                require(begin['frame']==frame,'managed phase crossed frame');objects[i]=obj
                inactive=obj[0]==8 and not block(begin,'object')[0]&128
                expected.append((frame,(3 if inactive else 2 if released else 1,i,generation[i],*obj)))
                calls['inactive_observations' if inactive else {2:'reversal_updates',3:'particle_updates',4:'emitter_updates',5:'private_updates',6:'table_updates',7:'collision_updates',8:'return_only_updates'}[obj[0]]]+=1
                if obj[0]==8:
                    require(i not in free and validate_return_only_phase(events,begin,e)==passive[i],'return-only activity/occupancy changed')
                if obj[0]==7:validate_collision_phase(events,begin,e,pairs[frame-START])
                if obj[0] in (5,6):
                    tail=phase_tail(events,begin,e);handler=0x7a88 if obj[0]==6 else 0x7ca4 if obj[1] else 0x7808
                    entries=[x for x in tail if x['pc']==handler]
                    require(len(entries)==1 and entries[0]['registers']['M68K A7']==begin['registers']['M68K A7']-4,'private scheduled handler differs')
                    require(sum(x['pc']==0xf76c for x in tail)==1,'private presentation missing')
        elif pc==0x69ce:
            require(not pending and a6==LIMIT,'world phase did not finish')
            free_after[frame]=tuple(free);rng_after[frame]=(be(block(e,'random'),0,4),be(block(e,'random'),4,4))
            p=pairs[frame-START]['return']
            require(block(e,'actor')==block(p,'actor') and block(e,'scratch')==block(p,'scratch'),'world phase changes owner/scratch')
        require(pc not in (0xf9e2,0x7910,0x79b6),'reservation left its audited private path')
    require(allocation is None and releasing is None and not pending,'unfinished pool operation')
    require(list(begins.values())==[SLOTS]*(END-START) and len(free_after)==END-START,'slot-loop cadence differs')
    for frame in range(START,END):
        gates=[e['registers']['M68K A6'] for e in events if e['frame']==frame and e['pc']==0x69aa]
        require(gates==list(range(BASE,LIMIT,STRIDE)),'slot order differs')
        phase,=[e for e in events if e['frame']==frame and e['pc']==0x69a4]
        require(pairs[frame-START]['return']['sequence']<phase['sequence'],'object walk precedes P1')
        for entry,ret,count in ((0x7808,0x7838,2),(0x7ca4,0x7cc6,2),(0x7a88,0x7ad4,1),(0x78ee,0x790e,1)):
            a=[e for e in events if e['frame']==frame and e['pc']==entry];b=[e for e in events if e['frame']==frame and e['pc']==ret]
            require(len(a)==len(b)==count,'reservation path cadence differs')
            for x,y in zip(a,b):
                require(x['sequence']<y['sequence'] and x['registers']['M68K A6']==y['registers']['M68K A6'] and x['registers']['M68K A7']==y['registers']['M68K A7'] and block(x,'stack')==block(y,'stack'),'reservation return differs')
                require(be(block(x,'stack'),0,4)==(0x69c2 if entry==0x78ee else 0x69bc),'reservation caller differs')
    # Audit all pool/free writes, including outside the object walk and transient
    # changes invisible to boundaries. Native write PCs report the next PC here.
    write_counts=Counter()
    for e in writes:
        address=e['address'];pc=e['pc'];owner=e['registers'].get('M68K A6');width=e['width']
        if address<0xff3120 and 0xff3008<address+width:
            require(e['cpu']=='M68K' and width==4 and ((pc==0xf9a6 and address==0xff311c and owner in (OWNER,EMITTER)) or
                (pc==0xfab8 and address==0xff311c and BASE<=owner<LIMIT and objects[slot(owner)][0] in (2,3)) or
                (pc==0xfab2 and 0xff300c<=address<0xff311c and address%4==0 and BASE<=owner<LIMIT and objects[slot(owner)][0] in (2,3))), 'unmodeled free-stack writer')
            write_counts['free_writes']+=1
        if not (address<0xff3008 and 0xff1b50<address+width):continue
        i=(address-0xff1b50)//STRIDE;offset=(address-0xff1b50)%STRIDE
        require(e['cpu']=='M68K' and 0<=i<SLOTS and offset+width<=STRIDE,'pool write crosses slot')
        own=owner==BASE+STRIDE*i
        render=own and (pc,offset,width,e['value'])==(0xb12a,20,2,0)
        presentation=own and 0xf76c<=pc<0xf850 and (offset,width) in ((0,1),(6,2),(12,1))
        if i in passive:
            validate_return_only_write(e,0xff1b50+STRIDE*i,passive[i]);write_counts['return_only_writes']+=1
            write_counts['managed_writes']+=1
        else:
            spawn=owner in (OWNER,EMITTER) and e['registers']['M68K A5']==BASE+STRIDE*i and (0xf994<=pc<=0xf9ce or 0x5a9a<=pc<=0x5ae2 or 0xa818<=pc<=0xa87a or 0xa9de<=pc<=0xaa3e or 0x6dbe<=pc<=0x6ddc)
            managed=own and ((pc==0xfaaa and offset==0 and width==1) or (pc in (0xa886,0xa88a,0xaa4a,0xaa4e) and offset==2 and width==2) or
                (owner==EMITTER and 0x6d90<=pc<=0x6e30 and width==2 and offset in (2,4,*range(0x22,0x38,2))))
            private=own and objects[i][0]==5 and ((objects[i][1]==0 and (pc,offset,width) in ((0x7824,16,2),(0x782a,4,2),(0x7832,4,2),(0x7838,16,2))) or
                (objects[i][1]==1 and (pc,offset,width) in ((0x7cb2,18,2),(0x7cc0,2,2),(0x7cc6,4,2))))
            table=own and objects[i][0]==6 and (pc,offset,width) in ((0x7a98,54,2),(0x7aa4,4,2),(0x7ab6,46,4),(0x7abe,2,2),(0x7ac2,16,2),(0x7aca,50,2),(0x7ad0,16,2))
            require(render or presentation or spawn or managed or private or table,'unmodeled managed slot writer');write_counts['managed_writes']+=1
    require(free_fields(after[0x3008:0x3120])==free,'final free list differs')
    for i,obj in enumerate(objects):
        o=(BASE&65535)+i*STRIDE;b=after[o:o+STRIDE]
        if obj[0]>=2:require(object_fields(b)==obj,'managed state changed after world loop')
    require(after[0xbac:0xbb4]==block(events[-1],'random'),'RNG changed after observed loop')
    return expected,free_after,rng_after,dict(calls)|dict(write_counts)|dict(slots=SLOTS,initial_free=len(seed_free),reservations=0,initial_return_only=len(passive),inactive_occupied=sum(not a for a in passive.values()),initial_particles=sum(o[0]==3 for o in initial(before)[0]),
        collision_input=collision_observed,initial_collision=sum(o[0]==7 for o in initial(before)[0]),table_input=table_observed,initial_table=sum(o[0]==6 for o in initial(before)[0]),private_globals=globals_observed,initial_private=sum(o[0]==5 for o in initial(before)[0]),
        anchor=dict(slot=anchor,generation=1,writes=0,scope='Logical FF31C0 identity seeded once and printed each call; no FF31C0 write here. Its readers (7AD6 activation via callback79B6, five overlap-hit +16 resets) are not reconstructed.'),
        initial_state_scope='Native P1, emitter/RNG, live trail/reversal and 7808/7CA4/7A88 objects and 78EE miss-only probe, ordered shared free stack; all seven return-only objects retained, including two dormant occupied slots, plus the FF31C0 pair anchor; no external reservations.')


def validate(chunks,writes,identity,before,after,inputs):
    events,native=validate_chunks(chunks,writes,identity);scene,bank,terrain=terrain_fixture(before)
    require(terrain_fixture(after)[:2]==(scene,bank),'terrain changed');pcs=set(session_recipe(True)['pcs'])
    trace=dict(chunks[0],events=events);core=dict(trace,events=[e for e in events if e['pc'] in pcs])
    pairs,scratch=validate_session(core,writes,inputs,START,END,terrain,True)
    validate_effects(trace);_,_,trail=validate_trails(events,native)
    expected,free,rng,observed=validate_pool(events,native,before,after,pairs)
    observed.update(actor_calls=len(pairs),scratch_writes=scratch,routine_events=len(events),native_events=sum(len(w['events']) for w in writes),
        producer_calls=3*len(pairs),input_polls=4*len(pairs),inactive_timers=len(pairs),newborn_particle_updates=trail['particle_calls'])
    return pairs,expected,free,rng,observed,scene,bank


def compare(pairs,expected,free,rng,before,inputs,out,native,scene,bank):
    for n,b in (('scene.bin',scene),('bank.bin',bank)):atomic_write(out/n,b)
    seed=session_seed(pairs[0]['wrapper']);scratch=block(pairs[0]['banner_before'],'scratch');seed=(*seed[:26],be(scratch,0),be(scratch,2),*seed[28:],0,0,6)
    objects,initial_free=initial(before)
    anchor=slot(be(before,0x31c0,4))
    rows=[seed,(SLOTS,len(initial_free),be(before,0xbac,4),be(before,0xbb0,4),*private_globals(before),be(before,0x31bc),be(before,0x13ae),be(before,0x33e2),0,0,0,anchor+1),tuple(initial_free),*objects,*[(physical_fields(r)[0],) for r in inputs]]
    data=encode_cases(rows);atomic_write(out/'mixed.in',data);cmd=[str(native),'movie.scene',str(out/'scene.bin'),'movie.bank',str(out/'bank.bin'),'--mixed-session']
    p=subprocess.run(cmd,input=data,capture_output=True,timeout=30);atomic_write(out/'native.stdout',p.stdout);atomic_write(out/'native.stderr',p.stderr)
    require(p.returncode==0,'native mixed session failed: '+p.stderr.decode());results=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
    require(len(results)==len(pairs),'mixed output row count differs')
    for frame,r,pair in zip(range(START,END),results,pairs):
        require(len(r)>=49 and r[0]==frame-START+1,'mixed ordinal/extent differs');event=pair['return']
        require(r[1:19]==snapshot_fields(event,be(block(pair['wrapper'],'actor'),0x1a,4)),f'mixed P1/scratch mismatch at {frame}')
        require(r[19:23]==tracking_fields(event) and r[23:35]==control_fields(event),'mixed tracking/input differs')
        n=r[39];off=40+4*n;require(n>=0 and tuple(tuple(r[j:j+4]) for j in range(40,off,4))==pair['sounds'] and not pair['samples'],'mixed requests differ')
        require(r[off:off+5]==pair['banner_request'],'mixed banner differs');off+=5
        count=r[off];off+=1;require(r[off:off+count]==free[frame],f'mixed ordered free stack differs at {frame}');off+=count
        require(r[off:off+2]==rng[frame],f'mixed retained RNG differs at {frame}');off+=2
        require(r[off:off+3]==(1,anchor,1),f'mixed FF31C0 identity differs at {frame}');off+=3
        ev=[values for f,values in expected if f==frame];require(r[off]==len(ev) and r[off+1:]==tuple(v for row in ev for v in row),f'mixed events/state/identities differ at {frame}')
    return dict(calls=len(results),physical_rows=len(inputs),per_call_environment_feeds=0,initial_slots=SLOTS,pool_events=len(expected),anchor_slot=anchor,
        sound_requests=sum(len(p['sounds']) for p in pairs),banner_requests=len(pairs),command=cmd,output_sha256=hashlib.sha256(p.stdout).hexdigest())


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path);p.add_argument('--preset',choices=PRESETS,default='debug');p.add_argument('--fixture',type=Path);args=p.parse_args(argv)
    ext=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug';sys.path.insert(0,str(ext/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);rom=inspect_file();verify_expected(rom);native=verify_executable(args.preset,'wiznliz-session')
    require(source['rom']['sha256']==rom['sha256'] and source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and not source['experimental_edits'] and not source['instrumentation'],'mixed recording differs')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256,'mixed movie identity differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/mixed-session')))
    report=dict(ok=False,preset=args.preset,start=START,end=END,recipe=recipe(),sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES},
        movie_sha256=MOVIE_SHA256,input_sha256=INPUT_SHA256,recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(),native_build=json.loads((native.parent/'provenance.json').read_text()),
        classification='fresh native comparison of captured ordinary movie' if args.fixture else 'fresh ordinary unchanged movie; no edits; owned workers',
        scope='Retained P1, trail emitter/RNG, all live/new trail and reversal effects, 7808/7CA4/7A88 private objects, 78EE miss-only probe, all return-only objects including dormant occupied slots, the FF31C0 pair anchor and shared ordered allocation. No external reservations in this window; no whole-world/render/audio parity.')
    try:
        inputs=source['inputs'][START:END];chunks=[];writes=[]
        if args.fixture:
            parent=json.loads(args.fixture.read_text());require(parent['recipe']==recipe() and parent['sources']==report['sources'] and parent['recording_sha256']==report['recording_sha256'],'mixed fixture validation/input contract changed')
            read=fixture_reader(parent,args.fixture.parent);report['identity']=parent['identity'];require(report['identity']==source['start']['worker_open']['identity'],'mixed fixture loaded identity differs')
            before=read('before.ram');after=read('after.ram');require(json.loads(read('inputs.json'))==inputs,'mixed fixture input rows differ')
            for f in range(START,END):chunks.append(json.loads(read(f'routines-{f}.json')));writes.append(json.loads(read(f'writes-{f}.json')))
            snap=json.loads(read('hooked.json'));snap2=json.loads(read('unhooked.json'));report['reference_report']=str(args.fixture);report['reference_report_sha256']=hashlib.sha256(args.fixture.read_bytes()).hexdigest()
        else:
            save(out/'inputs.json',inputs)
            with WorkerClient([str(ext/'run-worker.sh'),'--storage',str(out/'hooked-worker')]) as w:
                s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];save(out/'capabilities.json',check_worker(w,s,ext));require(report['identity']==source['start']['worker_open']['identity'],'mixed loaded identity differs');s.seek(START)
                before=w.read_bytes('68K RAM',0,65536);atomic_write(out/'before.ram',before);w.request('trace.configure',recipe());w.request('debug.trace.configure',{'mask':4|65536})
                for f in range(START,END):
                    s.seek(f+1);t=w.request('trace.drain');wr=w.request('debug.trace.drain');save(out/f'routines-{f}.json',t);save(out/f'writes-{f}.json',wr);chunks.append(t);writes.append(wr)
                    require(t['dropped']==0 and t['overflow'] is False and t['error'] is None and wr['dropped']==0,'mixed trace loss')
                snap=w.request('snapshot');save(out/'hooked.json',snap);after=w.read_bytes('68K RAM',0,65536);atomic_write(out/'after.ram',after)
            with WorkerClient([str(ext/'run-worker.sh'),'--storage',str(out/'unhooked-worker')]) as w:
                s=ReplaySession.from_recording(w,source);check_worker(w,s,ext);s.seek(END);snap2=w.request('snapshot');save(out/'unhooked.json',snap2)
        require(all(s['identity']==report['identity'] and s['frame']==END and not s['experimentalEdits'] for s in (snap,snap2)),'mixed endpoint provenance differs')
        require(snap['canonicalSha256']==snap2['canonicalSha256'] and snap['hashScope']==snap2['hashScope'],'mixed hooked/unhooked endpoint differs')
        report['endpoint']=dict(hooked=snap['canonicalSha256'],unhooked=snap2['canonicalSha256'],scope=snap['hashScope'])
        pairs,expected,free,rng,report['observation'],scene,bank=validate(chunks,writes,report['identity'],before,after,inputs)
        report['comparison']=compare(pairs,expected,free,rng,before,inputs,out,native,scene,bank);report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;report['artifacts']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()};save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','observation','comparison','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
