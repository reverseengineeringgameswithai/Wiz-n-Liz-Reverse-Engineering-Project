"""Retained P1 reversal session with an owned effect phase; shared world allocation remains observational."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from rom import ROOT, inspect_file, verify_expected
from rnc import approved_directory, atomic_write
from native_build import PRESETS, verify_executable
from genesis_actor_capture import save, require, block, be, terrain_fixture
from genesis_actions_capture import check_worker
from genesis_session_capture import recipe as session_recipe, validate_session, validate_writes, session_seed, physical_fields, control_fields
from genesis_reversal_capture import recipe as reversal_recipe, validate_effects, effect_fields
from genesis_movie_actor_capture import MOVIE_SHA256, INPUT_SHA256, snapshot_fields
from genesis_dispatch_capture import tracking_fields
from terrain_cases import encode_cases

START,END=700,1090
SOURCES=('tools/genesis_effect_session.py','tools/genesis_session_capture.py','tools/genesis_reversal_capture.py',
         'tools/genesis_dispatch_capture.py','tools/genesis_actions_capture.py','tools/genesis_movie_actor_capture.py')


def recipe():
    r=session_recipe(True);extra=reversal_recipe()
    r['pcs']=list(dict.fromkeys(r['pcs']+extra['pcs']+[0x69a4,0x69aa,0x69c0,0x69c2,0x69ce]))
    r['ranges'] += [d for d in extra['ranges'] if d['label'] in ('object','allocated','free')]
    return r


def validate_owned(trace,writes,pairs):
    events=trace['events'];allocations,births,lives=validate_effects(trace)
    require(len(lives)==1,'one owned reversal lifetime required')
    address,life=next(iter(lives.items()));birth=life['birth'];release=life['pairs'][-1][1]
    require((birth['frame'],release['frame'])==(1067,1078),'owned lifetime changed')
    updates={};services=0;owned_writes=0
    for begin,done,released in life['pairs']:
        frame=begin['frame'];p=pairs[frame-START];es=[e for e in events if e['frame']==frame]
        phase,=[e for e in es if e['pc']==0x69a4];end,=[e for e in es if e['pc']==0x69ce]
        require(p['return']['sequence']<phase['sequence']<begin['sequence']<done['sequence']<end['sequence'],'P1/effect phase order differs')
        gates=[e for e in es if e['pc']==0x69aa]
        require([e['registers']['M68K A6'] for e in gates]==list(range(0xffff1b50,0xffff3008,78)),'world slot walk differs')
        require(end['registers']['M68K A6']==0xffff3008,'world loop endpoint differs')
        tail=[e for e in es if e['registers']['M68K A6']==address and done['sequence']<=e['sequence']<=end['sequence']]
        require([e['pc'] for e in tail]==[0x69bc,0x69c0,0x12646,0x69c2],'effect service tail differs')
        selected,call,service,returned=tail;sp=phase['registers']['M68K A7']
        require(call['registers']['M68K A0']==0x12646 and be(block(selected,'object'),0x46,4)==0x12646,'unsupported effect service')
        require(all(e['registers']['M68K A7']==sp for e in (done,call,returned,end)) and service['registers']['M68K A7']==sp-4
                and be(block(service,'stack'),0,4)==0x69c2,'effect service return differs')
        require(all(block(e,l)==block(done,l) for e in tail for l in ('object','actor','control','scratch','free')),'effect service changed state')
        require(block(p['return'],'actor')==block(begin,'actor')==block(end,'actor') and block(p['return'],'scratch')==block(end,'scratch'),'world phase changes P1/scratch')
        updates[frame]=(effect_fields(block(returned,'object')),released);services+=1
    # Audit every write to the physical object only while P1 owns its lifetime.
    # Unrelated clients may own that physical slot before/after; no whole-pool claim.
    for frame in range(birth['frame'],release['frame']+1):
        for e in writes[frame-START]['events']:
            if e['type']!=4 or not (e['address']<(address&0xffffff)+78 and (address&0xffffff)<e['address']+e['width']):continue
            offset=e['address']-(address&0xffffff);pc=e['pc'];owner=e['registers']['M68K A6'];owned_writes+=1
            spawn=(frame==birth['frame'] and owner==0xffff1ab4 and (0xf994<=pc<=0xf9ce or 0xa9de<=pc<=0xaa3e))
            own=(owner==address and ((0xf76c<=pc<0xf850 and (offset,e['width']) in ((0,1),(6,2),(12,1)))
                  or (pc==0xfaaa and offset==0 and e['width']==1)
                  or (pc in (0xaa4a,0xaa4e) and offset==2 and e['width']==2)))
            render_clear=(owner==address and pc==0xb12a and offset==0x14 and e['width']==2 and e['value']==0)
            require(spawn or own or render_clear,'foreign/unmodeled owned-effect writer')
    foreign_allocations=[e for e in events if e['pc']==0xf994 and e['registers']['M68K A6']!=0xffff1ab4]
    foreign_releases=[e for e in events if e['pc']==0xfaa4 and e['registers']['M68K A6']!=address]
    heads=[be(block(e,'free'),276,4) for e in events]
    require(all(0xffff300c<=h<=0xffff311c and h%4==0 for h in heads)
            and all(be(block(e,'free'),0,4)==0 for e in events),'shared free stack/sentinel outside observed bounds')
    return updates,dict(owned_address=hex(address),birth_frame=birth['frame'],release_frame=release['frame'],
        allocations=len(allocations),effect_calls=len(updates),return_only_services=services,owned_writes=owned_writes,
        foreign_allocations=len(foreign_allocations),foreign_releases=len(foreign_releases),
        observed_free_min=(min(heads)-0xffff300c)//4,observed_free_max=(max(heads)-0xffff300c)//4,
        allocation_scope='One dedicated native P1 slot. Foreign shared-pool activity observed, not reproduced; no global capacity/order parity.')


def validate(trace,writes,inputs,terrain):
    require(trace['dropped']==0 and trace['overflow'] is False and trace['error'] is None,'incomplete effect trace')
    require(all(e['kind']=='entry' and START<=e['frame']<END for e in trace['events']),'effect trace boundary differs')
    require(all(a['sequence']<b['sequence'] for a,b in zip(trace['events'],trace['events'][1:])),'effect trace order differs')
    pcs=set(session_recipe(True)['pcs']);core=dict(trace,events=[e for e in trace['events'] if e['pc'] in pcs])
    pairs,scratch=validate_session(core,writes,inputs,START,END,terrain,True)
    updates,observed=validate_owned(trace,writes,pairs)
    return pairs,updates,observed,scratch


def validate_initial(ram):
    require(len(ram)==65536,'initial RAM extent differs')
    # A dedicated empty native pool is valid only if no P1 reversal is already
    # alive at this boundary. Other object types/owners stay outside the model.
    for offset in range(0x1b50,0x3008,78):
        obj=ram[offset:offset+78]
        require(not (obj[0]&128 and be(obj,0x16,4) in (0xa87c,0xaa40) and be(obj,0x22,4)==0xffff1ab4),
                'pre-existing P1 reversal needs an explicit initial-state contract')


def fixture_reader(parent,directory):
    require(parent['ok'] is True and parent['rom_unchanged'] is True,'reference capture did not pass')
    for name,digest in parent['artifacts'].items():
        require(Path(name).name==name and hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest,'fixture artifact changed')
    def read(name):
        require(name in parent['artifacts'],'unhashed fixture input: '+name)
        return (directory/name).read_bytes()
    return read


def validate_endpoint(hooked,unhooked,identity):
    for s in (hooked,unhooked):
        require(s['identity']==identity and s['frame']==END and not s['experimentalEdits'],'endpoint identity/frame/edits differ')
    require(hooked['canonicalSha256']==unhooked['canonicalSha256'] and hooked['hashScope']==unhooked['hashScope'],'hooked/unhooked endpoint differs')
    return dict(hooked=hooked['canonicalSha256'],unhooked=unhooked['canonicalSha256'],scope=hooked['hashScope'])


def compare(pairs,updates,inputs,directory,native,scene,bank):
    for name,data in [('scene.bin',scene),('bank.bin',bank)]:atomic_write(directory/name,data)
    before=pairs[0]['banner_before'];seed=session_seed(pairs[0]['wrapper'])
    seed=(*seed[:26],be(block(before,'scratch'),0),be(block(before,'scratch'),2),*seed[28:],0,0,6,1)
    data=encode_cases([seed,*[(physical_fields(row)[0],) for row in inputs]]);atomic_write(directory/'session.in',data)
    cmd=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),'--reversal-session']
    p=subprocess.run(cmd,input=data,capture_output=True,timeout=30);atomic_write(directory/'native.stdout',p.stdout);atomic_write(directory/'native.stderr',p.stderr)
    require(p.returncode==0,'native reversal session failed: '+p.stderr.decode())
    rows=[tuple(map(int,l.split())) for l in p.stdout.splitlines()];require(len(rows)==len(pairs),'native session row count differs')
    calls=spawns=releases=0
    for i,(r,pair) in enumerate(zip(rows,pairs)):
        frame=START+i;event=pair['return'];require(len(r)>=48,'short effect session row')
        require(r[0]==i+1 and r[1:19]==snapshot_fields(event,be(block(pair['wrapper'],'actor'),0x1a,4)),f'actor/scratch divergence at {frame}')
        require(r[19:23]==tracking_fields(event) and r[23:35]==control_fields(event),f'tracking/control divergence at {frame}')
        n=r[39];require(n>=0,'negative sound count');offset=40+4*n
        require(tuple(tuple(r[j:j+4]) for j in range(40,offset,4))==pair['sounds'] and not pair['samples'],'session requests differ')
        require(r[offset:offset+5]==pair['banner_request'],'banner differs');offset+=5
        free,spawn=r[offset:offset+2];offset+=2;require(spawn==int(frame==1067),'spawn cadence differs')
        if spawn:require(r[offset:offset+2]==(0,1),'owned identity differs');offset+=2
        count=r[offset];offset+=1;require(count==int(frame in updates) and len(r)==offset+15*count,'effect phase extent differs')
        require(free==int(not 1067<=frame<1078),'owned capacity differs')
        if count:
            fields,released=updates[frame]
            require(r[offset:]==(0,1,*fields,int(released)),f'effect result differs at {frame}')
            calls+=1;releases+=released
        spawns+=spawn
    return dict(calls=len(rows),seed_fields=len(seed),physical_rows=len(inputs),per_call_environment_feeds=0,
                effect_calls=calls,spawns=spawns,releases=releases,native_capacity=1,
                sound_requests=sum(len(p['sounds']) for p in pairs),banner_requests=len(pairs),command=cmd,
                output_sha256=hashlib.sha256(p.stdout).hexdigest())


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path);p.add_argument('--preset',choices=PRESETS,default='debug')
    p.add_argument('--fixture',type=Path,help='Reuse a passed capture report; no new original replay');args=p.parse_args(argv)
    external=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug';sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);rom=inspect_file();verify_expected(rom);native=verify_executable(args.preset,'wiznliz-session')
    require(source['rom']['sha256']==rom['sha256'],'recording ROM differs')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and not source['experimental_edits'] and source['instrumentation']=={},'movie baseline differs')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256,'movie identity differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/effect-session')))
    report=dict(ok=False,preset=args.preset,start=START,end=END,scope='One-seed banner/input/P1/owned reversal effect session; shared world allocation observational, no general world/render/audio/frame parity.',
                classification='fresh native comparison of saved capture' if args.fixture else 'ordinary unchanged movie, no edits; fresh owned worker capture',
                movie_sha256=MOVIE_SHA256,input_sha256=INPUT_SHA256,recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(),recipe=recipe(),
                sources={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in SOURCES},native_build=json.loads((native.parent/'provenance.json').read_text()))
    try:
        inputs=source['inputs'][START:END];save(out/'inputs.json',inputs);writes=[];events=[]
        if args.fixture:
            parent=json.loads(args.fixture.read_text());require(parent['ok'] is True and parent['recipe']==recipe(),'incompatible/failed fixture')
            require(set(parent['sources'])==set(SOURCES) and all(parent['sources'][n]==report['sources'][n] for n in SOURCES[1:]),'fixture dependencies changed')
            # This tool revalidates the raw chunks with its current checks. Keep
            # the capture's earlier validator identity, including any corrections.
            report['reference_sources']=parent['sources']
            require(parent['movie_sha256']==MOVIE_SHA256 and parent['input_sha256']==INPUT_SHA256 and parent['recording_sha256']==report['recording_sha256'],'fixture input differs')
            identity=parent['identity'];report['identity']=identity
            require(identity==source['start']['worker_open']['identity'],'fixture loaded identity differs')
            directory=args.fixture.parent
            read=fixture_reader(parent,directory)
            before=read('before.ram');after=read('after.ram')
            require(json.loads(read('inputs.json'))==inputs,'fixture physical rows differ')
            for frame in range(START,END):
                t=json.loads(read(f'routines-{frame}.json'));require(t['identity']==identity and t['dropped']==0 and t['overflow'] is False and t['error'] is None,'incomplete fixture')
                require(all(e['frame']==frame for e in t['events']),'fixture chunk frame differs')
                wr=json.loads(read(f'writes-{frame}.json'));require(wr['identity']==identity,'fixture write identity differs')
                events.extend(t['events']);writes.append(wr)
            trace=dict(t,events=events);report['endpoint']=validate_endpoint(json.loads(read('hooked.json')),json.loads(read('unhooked.json')),identity)
            require(report['endpoint']==parent['endpoint'],'fixture endpoint summary differs')
            report['reference_report']=str(args.fixture);report['reference_report_sha256']=hashlib.sha256(args.fixture.read_bytes()).hexdigest()
        else:
            with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'hooked-worker')]) as w:
                s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];report['capabilities']=check_worker(w,s,external)
                require(report['identity']==source['start']['worker_open']['identity'],'loaded recording identity differs');s.seek(START)
                before=w.read_bytes('68K RAM',0,65536);atomic_write(out/'before.ram',before);_,_,terrain=terrain_fixture(before)
                w.request('trace.configure',recipe());w.request('debug.trace.configure',{'mask':4|65536})
                for frame in range(START,END):
                    s.seek(frame+1);t=w.request('trace.drain');save(out/f'routines-{frame}.json',t)
                    require(t['identity']==s.opened['identity'] and t['dropped']==0 and t['overflow'] is False and t['error'] is None,'incomplete routine trace')
                    require(all(e['frame']==frame for e in t['events']),'routine frame differs');events.extend(t['events'])
                    wr=w.request('debug.trace.drain');save(out/f'writes-{frame}.json',wr);require(wr['identity']==s.opened['identity'],'write identity differs')
                    validate_writes(wr,frame,terrain,True);writes.append(wr)
                trace=dict(t,events=events);save(out/'trace.json',trace);after=w.read_bytes('68K RAM',0,65536);atomic_write(out/'after.ram',after)
                snap=w.request('snapshot');save(out/'hooked.json',snap)
            with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'unhooked-worker')]) as w:
                s=ReplaySession.from_recording(w,source);check_worker(w,s,external);s.seek(END);snap2=w.request('snapshot');save(out/'unhooked.json',snap2)
                report['endpoint']=validate_endpoint(snap,snap2,report['identity'])
        validate_initial(before);scene,bank,terrain=terrain_fixture(before);require(terrain_fixture(after)[:2]==(scene,bank),'terrain changed')
        pairs,updates,observed,scratch=validate(trace,writes,inputs,terrain);report['observation']=observed
        report['comparison']=compare(pairs,updates,inputs,out,native,scene,bank)
        report['cadence']=dict(actor_calls=END-START,producer_calls=3*(END-START),input_polls=4*(END-START),inactive_timers=END-START,scratch_writes=scratch,
                               native_events=sum(len(w['events']) for w in writes),routine_events=len(events))
        report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True
        report['artifacts']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()};save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','comparison','observation','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
