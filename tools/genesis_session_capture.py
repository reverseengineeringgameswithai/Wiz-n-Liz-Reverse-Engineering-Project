"""One-seed P1 movement session from the unchanged user movie, with writer/cadence evidence."""
import argparse
from collections import Counter
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
from genesis_dispatch_capture import recipe as dispatch_recipe, validate_dispatch, tracking_fields
from genesis_actions_capture import check_worker
from genesis_movie_actor_capture import input_case, snapshot_fields, MOVIE_SHA256, INPUT_SHA256
from terrain_cases import encode_cases

START, END = 3100, 3200
INPUT_OFFSETS=(0x14,0x15,0x16,0x17,0x1a,0x1b,0x1c,0x1d,0x1e,0x1f,0x20,0x21)
CONVERSIONS=((0xffff0690,0x14dee),(0xffff0838,0x14e38),(0xffff0690,0x313a),
             (0xffff0690,0x14dee),(0xffff0838,0x14e38),(0xffff0690,0x7da))
# The second level's loop (754): 30C4's 3126 reads the pads again (return 313A)
# only while FF0B90 is zero after the frame's 1345A; during a fade it does not.
FADE_CONVERSIONS=((0xffff0690,0x14dee),(0xffff0838,0x14e38),(0xffff0690,0x7da))
EARLY_CONVERSIONS=((0xffff0690,0x14dee),(0xffff0838,0x14e38),(0xffff0690,0x6980))
# The scene between levels: 5EEA's loop converts P1 at 5F2E (return 5F34) and
# has no 179F8, so no banner; its wrapper returns at 5F3A.
HUB_CONVERSIONS=((0xffff0690,0x14dee),(0xffff0838,0x14e38),(0xffff0690,0x5f34))
PARAMETERS=(0x5a,0x5c,0x66,0x60,0x6a,0x6c,0x5e,0x62,0x64)
FIXED=('gate','action_globals','mailbox','tracking_selector','transition')


def recipe(early=False):
    r=dispatch_recipe()
    r['pcs']=list(dict.fromkeys(r['pcs']+[0x14e4e,0x14f22,0x14e3c,0x1345a,0x134b0,0x134d4,0xebf2,0x99de,0x99e4,0x99ea,0x13208]))
    r['ranges'] += [dict(label=l,domain='68K RAM',offset=o,length=n) for l,o,n in
                    [('control2',0x838,112),('transition',0xb90,20)]]
    if early:
        r['pcs'] += [0x63e2,0x63e8,0x17532,0x6422,0x175d0,0x17aa0,0x17aa8,0x6986]
        r['ranges'] += [dict(label=l,domain='68K RAM',offset=o,length=n) for l,o,n in
                       [('difficulty',0x13e2,2),('stage',0x33c4,2),('multiplayer',0x33e2,2)]]
    return r


def physical_fields(row,port=1):
    names=('Up','Down','Left','Right','A','B','C','Start')
    require(isinstance(row,list) and len(set(row))==len(row),'invalid held row')
    require(all(b in {f'P{p} {n}' for p in (1,2) for n in names} for b in row),'unknown held button')
    held={b[3:] for b in row if b.startswith(f'P{port} ')}
    mask=sum(1<<i for i,n in enumerate(names) if n in held)
    raw=255 ^ sum(v for n,v in zip(names,(1,2,4,8,64,16,32,128)) if n in held)
    f=lambda n:255 if n in held else 0
    axis=lambda n,o:255 if n in held and o not in held else 0
    return mask,(raw,f('A')|f('B')|f('C'),f('B')|f('C'),f('A'),axis('Up','Down'),axis('Down','Up'),
                 axis('Left','Right'),axis('Right','Left'),f('A'),f('B'),f('C'),f('Start'))


def control_fields(e,label='control'):
    c=block(e,label);require(len(c)==112,'control extent differs')
    return tuple(c[i] for i in INPUT_OFFSETS)


def validate_producers(events,row,conversions=CONVERSIONS):
    es=[e for e in events if e['pc'] in (0x14e4e,0x14f22,0x14e3c)]
    require(len(es)==2*len(conversions),'input conversion cadence differs')
    for i,(a5,caller) in enumerate(conversions):
        before,after=es[2*i:2*i+2]
        require((before['pc'],after['pc'])==(0x14e4e,0x14f22),'input phase order differs')
        for e in (before,after):
            require(e['registers']['M68K A5']==a5 and be(block(e,'stack'),0,4)==caller,'producer owner/caller differs')
        require(before['sequence']<after['sequence'] and before['registers']['M68K A7']==after['registers']['M68K A7'],'producer return boundary differs')
        label='control' if a5==0xffff0690 else 'control2';other='control2' if label=='control' else 'control'
        _,expected=physical_fields(row,1 if label=='control' else 2)
        require(control_fields(after,label)==expected,'physical input conversion differs')
        b,a=block(before,label),block(after,label)
        require(b[0x14]==expected[0] and all(a[j]==b[j] for j in range(112) if j not in INPUT_OFFSETS[1:]),'conversion changed unmodeled fields')
        require(all(block(before,k)==block(after,k) for k in (other,'actor','scratch',*FIXED)),'producer changed unrelated state')
    return es[-1]


# The shared 1345A timer's code; with active_timer its own writes may change the
# FF0B90 transition block (native write PCs report the next PC). With
# exit_transition P1's 710E may also start 13208 (the exit fade) and 7126 may
# end with FF33E0 = 7.
TIMER_CODE=(0x1345a,0x134d6)
EXIT_FADE_CODE,EXIT_WAIT_CODE=(0x13208,0x1324e),(0x7126,0x7154)
# 13208's block: direction 1, countdown 1, reload 1, level 14, curves 1356A/1356A/135AA.
EXIT_FADE=b''.join(v.to_bytes(2,'big') for v in (1,1,1,14))+b''.join(v.to_bytes(4,'big') for v in (0x1356a,0x1356a,0x135aa))


def validate_writes(trace,frame,terrain=None,early=False,active_timer=False,exit_transition=False,hub=False,polled=True):
    require(trace['schemaVersion']==1 and type(trace['dropped']) is int and trace['dropped']==0,'incomplete native write trace')
    events=trace['events'];require(0<len(events)<=trace['capacity'],'native trace extent differs')
    require(all(e['frame']==frame for e in events) and all(a['sequence']<b['sequence'] for a,b in zip(events,events[1:])),'native event order/frame differs')
    polls=[e for e in events if e['type']==65536]
    require(len(polls)==(4 if early or not polled else 8),'input poll cadence differs') # Without 3126's poll, 14DA2 reads each pad once.
    require(all(e['type'] in (4,65536) for e in events),'native event mask differs')
    writes=[e for e in events if e['type']==4]
    # These pinned inputs to the session must have no hidden per-frame writers,
    # including transient writes that endpoint comparison alone would miss.
    fixed=[(0xff0690+i,2) for i in PARAMETERS]+[(0xff0f16,2),(0xff33d8,10),(0xff0ad6,8),(0xff0836,2)]+([] if active_timer else [(0xff0b90,20)])
    if early:fixed += [(0xff13e2,2),(0xff33c4,2),(0xff33e2,2)]
    if terrain is not None:
        fixed += [(terrain['map_bus'],8192),(terrain['record_bus'],terrain['records']*8),
                  (0xff13a4,2),(0xff13ae,2),(0xff140e,2),(0xff444e,8)]
    def overlaps(e,lo,n):return e['address']<lo+n and lo<e['address']+e['width']
    # 655A clears an unused byte in the broad action snapshot. Its observed zero
    # is checked against snapshots below; this is not an integrated world phase.
    def observed_clear(e):
        return early and e['cpu']=='M68K' and (e['pc'],e['address'],e['width'],e['value'])==(0x6560,0xff33de,1,0)
    # 7126's completion writes FF33E0 = 7 inside the fixed action globals.
    def exit_mode(e):
        return exit_transition and e['cpu']=='M68K' and EXIT_WAIT_CODE[0]<e['pc']<=EXIT_WAIT_CODE[1] and (e['address'],e['width'],e['value'])==(0xff33e0,2,7)
    require(not any(overlaps(e,lo,n) for e in writes if not observed_clear(e) and not exit_mode(e) for lo,n in fixed),'external shared-state writer breaks session contract')
    timer_writer=lambda e:e['cpu']=='M68K' and (TIMER_CODE[0]<e['pc']<=TIMER_CODE[1] or (exit_transition and EXIT_FADE_CODE[0]<e['pc']<=EXIT_FADE_CODE[1]))
    require(not active_timer or all(timer_writer(e) for e in writes if overlaps(e,0xff0b90,20)),'transition block writer outside 1345A')
    scratch=[e for e in writes if overlaps(e,0xff4442,4)]
    if early and not hub:
        require(scratch and (scratch[0]['pc'],scratch[0]['address'],scratch[0]['width'],scratch[0]['value'])==(0x63e8,0xff4444,2,6)
                and scratch[0]['cpu']=='M68K','missing/unknown banner scratch writer')
        scratch=scratch[1:]
    require(len(scratch)%2==0,'unpaired terrain scratch writes')
    for i,e in enumerate(scratch):
        require(e['cpu']=='M68K' and e['registers']['M68K A6']==0xffff1ab4,'terrain scratch has another writer')
        # Native access PC is the CPU PC during the write callback (next PC here),
        # not a pre-instruction PC. Managed 99DE/E4/EA hooks corroborate below.
        require((e['pc'],e['address'],e['width'])==((0x99e4,0xff4442,2) if i%2==0 else (0x99ea,0xff4444,2)),'unknown scratch writer')
    return scratch


def validate_banner(events):
    before,=[e for e in events if e['pc']==0x63e2]
    after,=[e for e in events if e['pc']==0x17aa8]
    selected=[e for e in events if before['sequence']<=e['sequence']<=after['sequence']]
    require([e['pc'] for e in selected]==[0x63e2,0x63e8,0x17532,0x6422,0x175d0,0x17aa8],'banner boundaries differ')
    entry,stored,text,continued,number,returned=selected;sp=entry['registers']['M68K A7']
    intro,=[e for e in events if e['pc']==0x17aa0]
    require(intro['sequence']<entry['sequence'] and intro['registers']['M68K A7']==sp+4,'banner row setup differs')
    require(be(block(entry,'stack'),0,4)==0x17aa8 and returned['registers']['M68K A7']==sp+4,'banner caller return differs')
    require(entry['registers']['M68K D1']&65535==6 and be(block(entry,'difficulty'),0)==0 and be(block(entry,'stage'),0)==0,'unobserved banner configuration')
    require(all(e['registers'][reg]==entry['registers'][reg] for e in selected for reg in ('M68K A5','M68K A6')),'banner owner registers changed')
    require(text['registers']['M68K A7']==sp-4 and be(block(text,'stack'),0,4)==0x6422,'banner text continuation differs')
    require(all(e['registers']['M68K A7']==sp for e in (stored,continued,number)) and be(block(number,'stack'),0,4)==0x17aa8,'banner tail return differs')
    require(text['registers']['M68K A0']==0x647c and text['registers']['M68K A1']==0xe300,'banner text request differs')
    require(number['registers']['M68K A1']==0xe338 and number['registers']['M68K D0']&65535==1,'banner number request differs')
    scratch=block(entry,'scratch')[:2]+bytes.fromhex('0006')
    require(all(block(e,'scratch')==scratch for e in selected[1:]),'banner scratch effects differ')
    require(all(block(e,k)==block(entry,k) for e in selected for k in ('actor','control',*FIXED)),'banner changed simulation state')
    return before,after,(0,text['registers']['M68K A1']&65535,1,number['registers']['M68K D0']&65535,number['registers']['M68K A1']&65535)


def validate_session(trace,native_traces,inputs,start=START,end=END,terrain=None,early=False,active_timer=False,exit_transition=False,hub=False):
    """With hub (which needs early) the frames are the scene between levels':
    HUB_CONVERSIONS, the wrapper returning at 5F3A and no banner, with the early
    window's pinned difficulty, stage and multiplayer words. Otherwise (the
    second level's loop) the cadence is CONVERSIONS while FF0B90 is zero after
    the frame's 1345A and FADE_CONVERSIONS during a fade; Start held at 30C4's
    poll would pause the game and rejects.
    With active_timer the 1345A timer may be active: the transition block then
    changes only across each frame's timer call, and each pair records it before
    (transition_before) and after (transition) that call. With exit_transition
    (which needs active_timer) P1's 710E may start 13208 inside the wrapper: the
    block then equals EXIT_FADE from that call on (transition_out); and 7126 may
    end by setting FF33E0 = 7."""
    require(early or not hub,'hub frames without the early window\'s checks')
    events=trace['events']
    require(all(a['sequence']<b['sequence'] for a,b in zip(events,events[1:])),'session trace sequence differs')
    require(all(start<=e['frame']<end for e in events),'session event outside window')
    # Per-frame drains keep worker response sizes bounded. Validate each complete
    # wrapper then explicitly enforce continuity across those validation chunks.
    pairs=[]
    for frame in range(start,end):
        pairs += validate_dispatch(dict(trace,events=[e for e in events if e['frame']==frame]),frame,frame+1,
                                   wrapper_returns=(0x5f3a,) if hub else (0x6986,) if early else (0x5f3a,0x7ec),completion_modes=(7,) if exit_transition else ())
    first=pairs[0]['wrapper']
    require(len(inputs)==len(native_traces)==end-start,'session input/write extent differs')
    require(all(len(block(first,k))==n for k,n in zip(FIXED,(2,10,8,2,20))),'fixed snapshot extent differs')
    require(active_timer or be(block(first,'transition'),0)==0,'active transition timer outside session')
    require(active_timer or not exit_transition,'exit transition without the active timer')
    fixed=tuple(k for k in FIXED if not (active_timer and k=='transition') and not (exit_transition and k=='action_globals'))
    params=input_case(first)[16:25]
    writes=0
    for index,p in enumerate(pairs):
        frame=start+index;es=[e for e in events if e['frame']==frame]
        # 1345A returns at 134B0, or at 134D4 after a positive direction's level step.
        timers=[e for e in es if e['pc'] in (0x1345a,0x134b0,0x134d4,0xebf2)]
        require([e['pc'] for e in timers] in ([0x1345a,0x134b0,0xebf2],[0x1345a,0x134d4,0xebf2]),'timer phase differs')
        timer,last,returned=timers;sp=timer['registers']['M68K A7']
        polled=not (early or hub) and be(block(returned,'transition'),0)==0
        converted=validate_producers(es,inputs[index],HUB_CONVERSIONS if hub else EARLY_CONVERSIONS if early else CONVERSIONS if polled else FADE_CONVERSIONS)
        # With Start held there, 3126 pauses the game (ECF14) unless +1A6 is FFFF/FFFE.
        require(not polled or not physical_fields(inputs[index])[1][11] or be(block(converted,'tracking_selector'),0) in (0xffff,0xfffe),'30C4 pause not native')
        require(be(block(timer,'stack'),0,4)==0xebf2 and last['registers']['M68K A7']==sp and returned['registers']['M68K A7']==sp+4,'timer return differs')
        require(returned['sequence']<next(e['sequence'] for e in es if e['pc']==0x14e4e)<converted['sequence']<p['wrapper']['sequence'],'timer/producer/wrapper order differs')
        require(all(block(timer,k)==block(e,k) for e in (last,returned) for k in ('actor','control','scratch',*fixed)),'inactive timer changed session inputs')
        if active_timer:
            carried=block(timer,'transition') if not index else pairs[index-1].get('transition_out',pairs[index-1]['transition']);after=block(returned,'transition')
            require(block(timer,'transition')==carried and block(last,'transition')==after,'transition block changed outside 1345A')
            # P1's 710E tail-jumps to 13208 inside the wrapper (actor A6).
            fades=[e for e in es if e['pc']==EXIT_FADE_CODE[0]] if exit_transition else []
            require(len(fades)<=1 and all(e['registers']['M68K A6']==0xffff1ab4 and p['wrapper']['sequence']<e['sequence']<p['return']['sequence'] for e in fades),'exit fade outside P1\'s wrapper')
            fade=fades[0]['sequence'] if fades else None
            def expected(e):
                if e['sequence']<timer['sequence']:return carried
                return EXIT_FADE if fade is not None and e['sequence']>fade else after
            require(all(block(e,'transition')==expected(e) for e in es if e['sequence']<timer['sequence'] or e['sequence']>last['sequence']),'transition block changed outside 1345A')
            p.update(transition_before=carried,transition=after)
            if fade is not None:p['transition_out']=EXIT_FADE
        require(control_fields(converted)==control_fields(p['wrapper']),'input changed before actor')
        for e in es:
            require(all(block(e,k)==block(first,k) for k in fixed),'shared state changed during session')
            if exit_transition:
                # Only 7126's completion may change the action globals: FF33E0 becomes 7.
                globals_=block(e,'action_globals');initial=block(first,'action_globals')
                require(globals_[:8]==initial[:8] and be(globals_,8) in (be(initial,8),7),'shared state changed during session')
            require(tuple(be(block(e,'control'),i) for i in PARAMETERS)==params,'movement parameters changed')
            if early:
                require(all(block(e,k)==block(first,k) for k in ('difficulty','stage','multiplayer')),'banner configuration changed')
                require(block(e,'action_globals')[6]==0 and be(block(e,'multiplayer'),0)==0,'unsupported world/multiplayer state')
        if index:
            previous=pairs[index-1]['return']
            require(block(previous,'actor')==block(p['wrapper'],'actor') and tracking_fields(previous)==tracking_fields(p['wrapper']),'external actor/tracking change')
        if early and not hub:
            before,after,request=validate_banner(es)
            p.update(banner_before=before,banner_request=request)
            require(returned['sequence']<before['sequence']<after['sequence']<next(e['sequence'] for e in es if e['pc']==0x14e4e),'banner phase order differs')
            require(block(after,'scratch')==block(p['wrapper'],'scratch'),'scratch changed between banner and actor')
            if index:require(block(previous,'scratch')==block(before,'scratch'),'scratch changed before banner')
        elif index:require(block(previous,'scratch')==block(p['wrapper'],'scratch'),'external scratch update between actor calls')
        scratch=validate_writes(native_traces[index],frame,terrain,early,active_timer,exit_transition,hub,polled or early or hub);writes+=len(scratch)+int(early and not hub)
        query=[e for e in es if e['pc'] in (0x99de,0x99e4,0x99ea)]
        require(len(query)*2==len(scratch)*3,'scratch instruction/access counts differ')
        for j in range(0,len(query),3):
            a,b,c=query[j:j+3];x,y=scratch[2*j//3:2*j//3+2]
            require([a['pc'],b['pc'],c['pc']]==[0x99de,0x99e4,0x99ea],'terrain write instruction order differs')
            require(p['wrapper']['sequence']<a['sequence']<b['sequence']<c['sequence']<p['return']['sequence'],'scratch writer outside P1 wrapper')
            require(all(e['registers']['M68K A6']==0xffff1ab4 for e in (a,b,c)),'scratch owner differs')
            require((be(block(b,'scratch'),0),be(block(c,'scratch'),0),be(block(c,'scratch'),2))==(x['value'],x['value'],y['value']),'scratch writer values differ')
    return pairs,writes


def session_seed(e):
    c=input_case(e)
    return (*c[:25],c[31],*c[32:34],*tracking_fields(e))


def decode(data,count,early=False):
    rows=[tuple(map(int,r.split())) for r in data.splitlines()]
    require(len(rows)==count and all(len(r)>=40 and r[39]>=0 and len(r)==40+4*r[39]+5*early for r in rows),'session output shape differs')
    return rows


def compare_session(pairs,inputs,directory,native,scene,bank,early=False):
    for name,data in [('scene.bin',scene),('bank.bin',bank)]:atomic_write(directory/name,data)
    seed=session_seed(pairs[0]['wrapper']);masks=[physical_fields(row)[0] for row in inputs]
    if early:
        before=pairs[0]['banner_before']
        seed=(*seed[:26],be(block(before,'scratch'),0),be(block(before,'scratch'),2),*seed[28:],
              be(block(before,'difficulty'),0),be(block(before,'stage'),0),before['registers']['M68K D1']&65535)
    data=encode_cases([seed,*[(mask,) for mask in masks]]);atomic_write(directory/'session.in',data)
    command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin')]
    if early:command.append('--level-banner')
    proc=subprocess.run(command,input=data,capture_output=True,timeout=30)
    atomic_write(directory/'native.stdout',proc.stdout);atomic_write(directory/'native.stderr',proc.stderr)
    require(proc.returncode==0,'native session failed: '+proc.stderr.decode())
    rows=decode(proc.stdout,len(pairs),early)
    for i,(r,p) in enumerate(zip(rows,pairs)):
        frame=p['wrapper']['frame'];event=p['return']
        require(r[0]==i+1,'native invocation ordinal differs')
        require(r[1:19]==snapshot_fields(event,be(block(p['wrapper'],'actor'),0x1a,4)),f'session actor/scratch divergence at {frame}')
        require(r[19:23]==tracking_fields(event),f'session tracking divergence at {frame}')
        require(r[23:35]==control_fields(event),f'session input divergence at {frame}')
        require(tuple(tuple(r[j:j+4]) for j in range(40,40+4*r[39],4))==p['sounds'],f'session sound request divergence at {frame}')
        if early:require(r[-5:]==p['banner_request'],f'session banner divergence at {frame}')
        require(not p['samples'],'unexpected sample effect')
    return dict(calls=len(pairs),command=command,seed_fields=len(seed),button_rows=len(masks),per_call_environment_feeds=0,
                output_sha256=hashlib.sha256(proc.stdout).hexdigest(),sound_requests=sum(len(p['sounds']) for p in pairs),
                banner_invocations=len(pairs) if early else 0,
                handlers=dict(Counter(hex(e['pc']) for p in pairs for e in p['handlers'])))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path)
    p.add_argument('--preset',choices=PRESETS,default='debug');p.add_argument('--window',choices=('late','early'),default='late');args=p.parse_args(argv)
    early=args.window=='early';start,end=(700,1067) if early else (START,END)
    external=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug';sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient, ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity);native=verify_executable(args.preset,'wiznliz-session')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[],'movie input identity differs')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256,'movie identity differs')
    require(source['instrumentation']=={} and source['rom']['sha256']==identity['sha256'],'movie baseline differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/session-movie')))
    report={'ok':False,'preset':args.preset,'start':start,'end':end,'classification':'ordinary unchanged user movie; no RAM/register/ROM/input edits',
            'scope':'One initial scene/actor/control configuration, then physical held sets only; P1 movement wrapper state, requests and terrain scratch. Early window includes level-banner requests before input. Inactive timer and zero clear of unused FF33DE observed, not scheduled natively. No whole-world/frame/render/audio parity.',
            'recording_sha256':hashlib.sha256(args.recording.read_bytes()).hexdigest(),'movie_sha256':MOVIE_SHA256,'input_sha256':INPUT_SHA256,
            'native_build':json.loads((native.parent/'provenance.json').read_text()),'recipe':recipe(early),
            'sources':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ('tools/genesis_session_capture.py','tools/genesis_dispatch_capture.py','tools/genesis_movie_actor_capture.py','tools/genesis_actions_capture.py')}}
    try:
        inputs=source['inputs'][start:end];save(out/'inputs.json',inputs);writes=[];routine_events=[]
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'hooked-worker')]) as w:
            s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];report['capabilities']=check_worker(w,s,external)
            require(report['capabilities']['capabilities']['nativeTrace'],'native trace unavailable')
            s.seek(start);before=w.read_bytes('68K RAM',0,65536);atomic_write(out/'before.ram',before)
            scene,bank,terrain=terrain_fixture(before);report['terrain']=terrain
            w.request('trace.configure',recipe(early));w.request('debug.trace.configure',{'mask':4|65536})
            for frame in range(start,end):
                s.seek(frame+1);t=w.request('debug.trace.drain');save(out/f'writes-{frame}.json',t)
                require(t['identity']==s.opened['identity'],'write trace identity differs');validate_writes(t,frame,terrain,early);writes.append(t)
                trace=w.request('trace.drain');save(out/f'routines-{frame}.json',trace)
                require(trace['identity']==s.opened['identity'] and trace['dropped']==0 and trace['overflow'] is False and trace['error'] is None,'incomplete routine trace')
                require(all(e['frame']==frame for e in trace['events']),'routine drain frame differs');routine_events.extend(trace['events'])
            trace=dict(trace,events=routine_events);save(out/'trace.json',trace)
            after=w.read_bytes('68K RAM',0,65536);atomic_write(out/'after.ram',after)
            require(terrain_fixture(after)[:2]==(scene,bank),'terrain endpoints differ')
            pairs,scratch_writes=validate_session(trace,writes,inputs,start,end,terrain,early)
            report['comparison']=compare_session(pairs,inputs,out,native,scene,bank,early)
            report['cadence']=dict(video_frames=end-start,actor_invocations=len(pairs),producer_invocations=(3 if early else 6)*len(pairs),input_polls=(4 if early else 8)*len(pairs),inactive_timer_invocations=len(pairs),scratch_writes=scratch_writes,banner_invocations=len(pairs) if early else 0)
            snap=w.request('snapshot');save(out/'hooked.json',snap)
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'unhooked-worker')]) as w:
            s=ReplaySession.from_recording(w,source);check_worker(w,s,external);s.seek(end);unhooked=w.request('snapshot');save(out/'unhooked.json',unhooked)
            require(snap['canonicalSha256']==unhooked['canonicalSha256'] and snap['hashScope']==unhooked['hashScope'],'hooked/unhooked endpoint differs')
            report['endpoint']=dict(hooked=snap['canonicalSha256'],unhooked=unhooked['canonicalSha256'],scope=snap['hashScope'])
        report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True
        report['artifacts']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}
        save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','cadence','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
