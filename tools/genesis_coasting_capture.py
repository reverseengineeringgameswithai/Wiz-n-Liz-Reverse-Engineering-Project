"""Movie-proven 630A initializer and continuous 632A wrapper calls; no state edits."""
import hashlib
import subprocess
from genesis_actor_capture import block,be,require,actor_fields
from genesis_dispatch_capture import recipe as dispatch_recipe,validate_dispatch,tracking_fields
from genesis_actions_capture import action_case,shared_fields
from genesis_movie_actor_capture import snapshot_fields
from genesis_transition_capture import recipe as transition_recipe,transition_fields,main as capture_main
from transition_cases import decode
from actions_cases import split
from terrain_cases import encode_cases
from rnc import atomic_write

START,END=1742,1759
EXTRA=(0x630a,0x6328,0x62f8,0x632a,0xa148,0xa15c,0xa168)
LABELS=('actor','control','scratch','gate','action_globals','mailbox','tracking_selector','transition','palette_flags','requested_position','saved_position')


def recipe():
    # Reuse fixed state ranges without unrelated transition/timer hook PCs.
    r=transition_recipe();r['pcs']=list(dict.fromkeys(dispatch_recipe()['pcs']+list(EXTRA)))
    return r


def validate(trace,start,end):
    events=trace['events'];require(trace['schemaVersion']==1 and trace['boundary']=='instruction-pre-execute','trace schema differs')
    require(trace['overflow'] is False and type(trace['dropped']) is int and trace['dropped']==0 and trace['error'] is None,'incomplete trace')
    require(0<len(events)<=20000 and all(a['sequence']<b['sequence'] for a,b in zip(events,events[1:])),'trace ordering/extent differs')
    require(all(e['kind']=='entry' and start<=e['frame']<end for e in events),'trace event outside contract')
    def initial(pc):
        es=[e for e in events if e['frame']==start and e['pc']==pc and e['registers']['M68K A5']==0xffff0690]
        require(len(es)==1,'initializer boundary count differs');return es[0]
    entry,last,returned=initial(0x630a),initial(0x6328),initial(0x62f8)
    sp=entry['registers']['M68K A7']
    require(entry['sequence']<last['sequence']<returned['sequence'],'initializer order differs')
    require(be(block(entry,'control'),0,4)==0xffff1ab4 and last['registers']['M68K A4']==0xffff1ab4,'initializer associated actor differs')
    require(last['registers']['M68K A7']==sp and returned['registers']['M68K A7']==sp+4,'initializer return stack differs')
    require(all(be(block(e,'stack'),0,4)==0x62f8 for e in (entry,last)),'initializer pending return differs')
    require(all(e['registers']['M68K A6']==entry['registers']['M68K A6'] for e in (last,returned)),'initializer changed caller owner')
    require(all(block(last,l)==block(returned,l) for l in LABELS),'initializer RTS changed state')
    require(all(block(entry,l)==block(returned,l) for l in LABELS if l not in ('actor','tracking_selector')),'initializer changed unrelated state')
    a,b=block(entry,'actor'),block(returned,'actor');allowed={0,6,7,22,23,24,25}
    require(all(a[i]==b[i] for i in range(78) if i not in allowed),'initializer uncontracted actor write')
    require(b[0]==128 and be(b,6)==541 and be(b,22,4)==0x632a and be(block(returned,'tracking_selector'),0)==65535,'initializer output differs')
    sub=dict(trace,events=[e for e in events if start<e['frame']<end]);pairs=validate_dispatch(sub,start+1,end)
    first=pairs[0]['wrapper']
    require(actor_fields(block(first,'actor'))==actor_fields(b) and be(block(first,'actor'),0x1a,4)==be(b,0x1a,4),'external change between initializer and first update')
    require(tracking_fields(first)==tracking_fields(returned),'tracking changed before first update')
    for p in pairs:
        require(len(p['handlers'])==1 and p['handlers'][0]['pc']==0x632a and not p['callbacks'],'unexpected coasting continuation/callback')
        handler=p['handlers'][0];es=[e for e in events if e['frame']==handler['frame'] and e['registers']['M68K A6']==0xffff1ab4]
        coasts=[e for e in es if e['pc']==0xa148];returns=[e for e in es if e['pc'] in (0xa15c,0xa168)]
        require(len(coasts)==len(returns)==1,'missing/duplicate coasting tail boundary');coast,rts=coasts[0],returns[0]
        require(handler['sequence']<coast['sequence']<rts['sequence']<p['end']['sequence'],'coasting tail order differs')
        require(all(block(handler,l)==block(coast,l) for l in LABELS),'coasting tail entry changed state')
        sp=handler['registers']['M68K A7']
        require(be(block(handler,'actor'),0x4a,4)==0xffff0690 and coast['registers']['M68K A5']==0xffff0690,'coasting control binding differs')
        require(all(e['registers']['M68K A7']==sp and be(block(e,'stack'),0,4)==0xf906 for e in (handler,coast,rts)),'tail replaced caller return')
        require(all(block(rts,l)==block(p['end'],l) for l in LABELS),'coasting RTS changed state')
        require(all(block(p['wrapper'],l)==block(p['return'],l) for l in LABELS if l not in ('actor','control','scratch')),'coasting wrote shared transition/global state')
    return (entry,returned),pairs


def compare_window(trace,directory,native,scene,bank,start,end):
    initialization,pairs=validate(trace,start,end)
    boundaries=[initialization]+[(p['wrapper'],p['return']) for p in pairs]
    cases=[(*action_case(a),*tracking_fields(a),*transition_fields(a)) for a,b in boundaries]
    for name,data in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/name,data)
    command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),'--coast-sequence']
    proc=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60)
    atomic_write(directory/'native.stdout',proc.stdout);atomic_write(directory/'native.stderr',proc.stderr)
    require(proc.returncode==0,'native coasting sequence failed: '+proc.stderr.decode())
    for row,(a,b) in zip(decode(proc.stdout,len(cases)),boundaries):
        require(row[-13:]==transition_fields(b,a),'shared transition fields diverged')
        require(row[-17:-13]==tracking_fields(b),'tracking diverged')
        core,shared,samples=split(row[:-17])
        require(core[:18]==snapshot_fields(b,be(block(a,'actor'),0x1a,4)),f'actor diverged at {a["frame"]}')
        require(shared==shared_fields(b) and not samples and core[21]==0,'unexpected global/request effect')
    return {'ok':True,'initializers':1,'continuous_wrapper_calls':len(pairs),'first_update_frame':pairs[0]['wrapper']['frame'],
            'command':command,'output_sha256':hashlib.sha256(proc.stdout).hexdigest(),
            'scope':'one P1 initializer and its next 16 P1 updates; P2 initializer observed but not compared; shared transition and other world objects excluded'}


def main(argv=None):
    return capture_main(argv,capture_recipe=recipe,comparator=compare_window,start=START,end=END,output_name='coasting-movie',
        scope='P1 associated-actor initializer at frame 1742 and continuous wrapper calls at 1743..1758; actor/service/tracking coordinates retained, inputs and shared environment feeds explicit; no world, palette or P2 scheduling parity')

if __name__=='__main__':raise SystemExit(main())
