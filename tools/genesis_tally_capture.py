"""Continuous 51C8 tally path from the unchanged user movie, through wrapper RTS."""
import hashlib
import subprocess
from genesis_actor_capture import block,be,require
from genesis_dispatch_capture import validate_dispatch,tracking_fields
from genesis_actions_capture import action_case,shared_fields
from genesis_movie_actor_capture import snapshot_fields
from genesis_transition_capture import recipe as transition_recipe,transition_fields,main as capture_main
from tally_cases import decode
from actions_cases import split
from terrain_cases import encode_cases
from rnc import atomic_write

START,END=3403,3578
EXTRA=(0x51d0,0x522c,0x5266,0x537c,0x53a2,0x53dc,0xaf98,0xafae,0x52a6,0x52ae,0x4f8c,0xa148,0xa15c,0xa168)
TALLY_RANGES=(('tally_gate',0x33ce),('remaining',0x714),('skip',0xf0e),('tally_countdown',0x340a),('credit',0x3402),('special_gate',0x104))
LABELS=('actor','control','scratch','gate','action_globals','mailbox','tracking_selector','transition','palette_flags','requested_position','saved_position')+tuple(l for l,o in TALLY_RANGES)


def recipe():
    r=transition_recipe();r['pcs']=list(dict.fromkeys(r['pcs']+list(EXTRA)))
    r['ranges'] += [dict(label=l,domain='68K RAM',offset=o,length=2) for l,o in TALLY_RANGES]
    return r


def tally_fields(e):
    require(all(len(block(e,l))==2 for l,o in TALLY_RANGES),'tally snapshot extent differs')
    return tuple(be(block(e,l),0) for l,o in TALLY_RANGES)


def validate(trace,start,end):
    pairs=validate_dispatch(trace,start,end,completion_modes=(3,));events=trace['events']
    for p in pairs:
        es=[e for e in events if e['frame']==p['start']['frame'] and e['registers']['M68K A6']==0xffff1ab4]
        def one(pc):
            selected=[e for e in es if e['pc']==pc];require(len(selected)==1,'tally boundary count differs: '+hex(pc));return selected[0]
        require(not any(e['pc'] in (0x51d0,0x5266) for e in es),'unsupported tally path observed')
        require([e['pc'] for e in p['handlers']]==[0x51c8,0x5222] and not p['callbacks'],'unexpected tally continuation')
        entry,common=p['handlers'];sp=entry['registers']['M68K A7']
        require(entry['sequence']<common['sequence'] and common['registers']['M68K A7']==sp and be(block(common,'stack'),0,4)==0xf906,'tally branch changed return')
        require(all(block(entry,l)==block(common,l) for l in LABELS),'tally branch changed state')
        require(be(block(common,'actor'),0x4a,4)==0xffff0690 and tally_fields(common)[0]==0,'tally input association/gate differs')
        coast,after=one(0xa148),one(0x522c)
        rts=[e for e in es if e['pc'] in (0xa15c,0xa168)];require(len(rts)==1,'missing coasting RTS');rts=rts[0]
        require(common['sequence']<coast['sequence']<rts['sequence']<after['sequence']<p['end']['sequence'],'coasting order differs')
        require(all(e['registers']['M68K A7']==sp-4 and be(block(e,'stack'),0,4)==0x522c for e in (coast,rts)),'coasting pending return differs')
        require(after['registers']['M68K A7']==sp and all(block(rts,l)==block(after,l) for l in LABELS),'coasting return changed state')
        tails=[e for e in es if e['pc'] in (0x53a2,0x53dc,0x52ae,0x4f8c)]
        require(len(tails)==1,'tally return boundary count differs');last=tails[0]
        require(after['sequence']<last['sequence']<p['end']['sequence'] and last['registers']['M68K A7']==sp and be(block(last,'stack'),0,4)==0xf906,'tally tail return differs')
        require(all(block(last,l)==block(p['end'],l) for l in LABELS),'tally RTS changed state')
        if tally_fields(entry)[1]:
            counter=one(0x537c)
            require(after['sequence']<counter['sequence']<last['sequence'] and counter['registers']['M68K A7']==sp and be(block(counter,'stack'),0,4)==0xf906,'counter tail differs')
        if p['sounds']:
            credit,credit_rts=one(0xaf98),one(0xafae)
            require(credit['sequence']<credit_rts['sequence']<last['sequence'],'credit order differs')
            require(all(e['registers']['M68K A7']==sp-4 and be(block(e,'stack'),0,4)==0x53ae for e in (credit,credit_rts)),'credit return differs')
            sound=one(0xfcb32)
            require(sound['registers']['M68K A7']==sp-4 and be(block(sound,'stack'),0,4)==0x53d4,'sound request return differs')
            require(p['sounds']==((140,6,192,1),),'tally sound request differs')
        require(tally_fields(p['wrapper'])==tally_fields(entry) and tally_fields(p['end'])==tally_fields(p['return']),'tally state changed outside handler')
        require(all(block(p['wrapper'],l)==block(p['return'],l) for l in ('gate','mailbox','transition','palette_flags','requested_position','saved_position','tally_gate','special_gate')),'uncontracted world write')
        require(shared_fields(p['wrapper'])[1:]==shared_fields(p['return'])[1:],'uncontracted action/mailbox write')
    return pairs


def compare_window(trace,directory,native,scene,bank,start,end):
    pairs=validate(trace,start,end)
    cases=[(*action_case(p['wrapper']),*tracking_fields(p['wrapper']),*transition_fields(p['wrapper']),*tally_fields(p['wrapper']),block(p['wrapper'],'control')[0x21]) for p in pairs]
    for name,data in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/name,data)
    command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),'--tally-sequence']
    proc=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60)
    atomic_write(directory/'native.stdout',proc.stdout);atomic_write(directory/'native.stderr',proc.stderr)
    require(proc.returncode==0,'native tally sequence failed: '+proc.stderr.decode())
    for row,p in zip(decode(proc.stdout,len(cases)),pairs):
        a,b=p['wrapper'],p['return'];require(row[-6:]==tally_fields(b),'tally state diverged')
        row=row[:-6];require(row[-13:]==transition_fields(b,a) and row[-17:-13]==tracking_fields(b),'transition/tracking diverged')
        core,shared,samples=split(row[:-17]);require(core[:18]==snapshot_fields(b,be(block(a,'actor'),0x1a,4)),'actor/scratch diverged')
        require(shared==shared_fields(b) and not samples,'global/mailbox diverged')
        require(tuple(tuple(core[j:j+4]) for j in range(23,len(core),4))==p['sounds'],'sound requests diverged')
    return {'ok':True,'continuous_wrapper_calls':len(pairs),'sound_requests':sum(len(p['sounds']) for p in pairs),
        'completion_frames':[p['return']['frame'] for p in pairs if shared_fields(p['return'])[0]==3],
        'command':command,'output_sha256':hashlib.sha256(proc.stdout).hexdigest()}


def main(argv=None):
    return capture_main(argv,capture_recipe=recipe,comparator=compare_window,start=START,end=END,output_name='tally-movie',
        scope='continuous P1 actor/service/tracking and remaining/skip/countdown/credit through 51C8 zero palette gate; explicit world/control/scratch inputs; sound requests only; palette and bonus-allocation paths unsupported')

if __name__=='__main__':raise SystemExit(main())
