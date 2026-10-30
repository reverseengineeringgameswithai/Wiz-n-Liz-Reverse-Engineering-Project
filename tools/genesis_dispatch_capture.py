"""Full bounded actor wrapper through actual caller return, using the preserved movie."""
from collections import Counter
import hashlib
import subprocess
from genesis_actor_capture import block,be,require
from genesis_actions_capture import recipe as actions_recipe,validate_actions,action_case,shared_fields,main as capture_main,EXTRA_PCS
from genesis_movie_actor_capture import snapshot_fields
from dispatch_cases import decode
from actions_cases import split
from terrain_cases import encode_cases
from rnc import atomic_write

WINDOWS=((1608,1690),(3230,3339))
TAIL_PCS=(0xf8f6,0xf90a,0xf90c,0xf928,0xf936,0x5f3a,0x7ec)


def recipe():
    r=actions_recipe();r['pcs']=list(dict.fromkeys(r['pcs']+list(TAIL_PCS)))
    r['ranges'].append({'label':'tracking_selector','domain':'68K RAM','offset':0x836,'length':2})
    return r


def tracking_fields(e):
    a=block(e,'actor');require(be(a,0x46,4)==0x12646,'unsupported observed service')
    selector=block(e,'tracking_selector');require(len(selector)==2,'tracking selector extent differs')
    c=block(e,'control');return (1,be(selector,0),be(c,0x42),be(c,0x44))


def validate_dispatch(trace,start,end,*,completion_modes=(),sample_returns=(0x9ce8,),sample_contract=(0xf0000,200,0xf14,0x8000,30,24),control_writes=(),wrapper_returns=(0x5f3a,0x7ec)):
    # This movie contract expects active P1 calls. Inactive/sentinel tails have
    # exhaustive restricted-original and authored coverage, not invented movie hits.
    pairs=validate_actions(trace,start,end,completion_modes=completion_modes,sample_returns=sample_returns,sample_contract=sample_contract,control_writes=control_writes);events=trace['events'];used=set()
    for p in pairs:
        frame=p['start']['frame'];es=[e for e in events if e['frame']==frame and e['registers']['M68K A6']==0xffff1ab4]
        starts=[e for e in es if e['pc']==0xf8f6];returns=[e for e in es if e['pc'] in wrapper_returns]
        require(len(starts)==len(returns)==1,'wrapper entry/return count differs');entry,returned=starts[0],returns[0]
        require(entry['sequence']<p['start']['sequence']<p['end']['sequence']<returned['sequence'],'wrapper boundary order differs')
        sp=entry['registers']['M68K A7'];require(be(block(entry,'stack'),0,4)==returned['pc'],'wrapper caller differs')
        require(p['start']['registers']['M68K A7']==sp and returned['registers']['M68K A7']==sp+4,'wrapper return stack differs')
        require(all(entry['registers'][r]==returned['registers'][r] for r in ('M68K A5','M68K A6')),'wrapper owner differs')
        require(all(block(entry,l)==block(p['start'],l) for l in ('actor','control','scratch','gate','action_globals','mailbox','tracking_selector')),'active gate changed state')
        tail=[e for e in es if p['end']['sequence']<e['sequence']<returned['sequence']]
        selector=be(block(entry,'tracking_selector'),0);rts=0xf936 if selector==65535 else 0xf928
        require([e['pc'] for e in tail]==[0xf90a,0x12646,0xf90c,rts],'missing/unknown service or tail boundary')
        select,service,after,last=tail
        require(select['registers']['M68K A0']==be(block(p['end'],'actor'),0x46,4)==0x12646,'selected service differs')
        require(service['registers']['M68K A7']==sp-4 and be(block(service,'stack'),0,4)==0xf90c,'service return differs')
        require(all(e['registers']['M68K A7']==sp for e in (select,after,last)),'tail stack differs')
        require(all(e['registers']['M68K A5']==entry['registers']['M68K A5'] for e in tail),'tail owner differs')
        labels=('actor','control','scratch','gate','action_globals','mailbox','tracking_selector')
        require(all(block(p['end'],l)==block(e,l) for e in (select,service,after) for l in labels),'return-only service changed state')
        require(all(block(p['end'],l)==block(returned,l)==block(last,l) for l in labels if l!='control'),'uncontracted wrapper write')
        before=block(entry,'control');c=block(returned,'control');require(c==block(last,'control'),'RTS changed control state')
        require(all(before[i]==c[i] for i in range(len(c)) if i not in range(0x42,0x46) and i not in control_writes),'uncontracted control write')
        x,y=be(block(returned,'actor'),2),be(block(returned,'actor'),4)
        expected=(0xff80,0xff80) if selector==65535 else ((x+4)&65535,(y+6)&65535)
        require(tracking_fields(returned)[2:]==expected,'control coordinates differ')
        # Do not reseed tracking between calls. The selector remains an external input.
        if used:
            previous=pairs[len(used)-1]['return']
            require(tracking_fields(entry)[2:]==tracking_fields(previous)[2:],'external tracking change breaks continuous window')
        p.update(wrapper=entry,service=service)
        p['return']=returned;used.add(frame)
    require(len(used)==end-start,'missing wrapper frame')
    return pairs


def compare_window(trace,directory,native,scene,bank,start,end):
    pairs=validate_dispatch(trace,start,end)
    cases=[(*action_case(p['wrapper']),*tracking_fields(p['wrapper'])) for p in pairs]
    for name,data in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/name,data)
    comparisons={}
    for mode,label,key in (('--actions-presentation','presentation','presentation'),('--actions-sequence','selected-handler','end'),('--dispatch-sequence','continuous-wrapper','return')):
        command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),mode]
        inputs=cases if key=='return' else [c[:43] for c in cases]
        proc=subprocess.run(command,input=encode_cases(inputs),capture_output=True,timeout=60)
        atomic_write(directory/f'{label}.stdout',proc.stdout);atomic_write(directory/f'{label}.stderr',proc.stderr)
        require(proc.returncode==0,label+' failed: '+proc.stderr.decode())
        from actions_cases import decode as action_decode
        for row,pair in zip((decode if key=='return' else action_decode)(proc.stdout,len(cases)),pairs):
            event=pair[key];frame=pair['start']['frame']
            if key=='return':require(row[-4:]==tracking_fields(event),f'tracking divergence at {frame}');row=row[:-4]
            core,shared,samples=split(row)
            require(core[:18]==snapshot_fields(event,be(block(pair['start'],'actor'),0x1a,4)),f'{label} actor divergence at {frame}')
            require(shared==shared_fields(event),f'{label} shared/mailbox divergence at {frame}')
            sounds=tuple(tuple(core[j:j+4]) for j in range(23,len(core),4))
            require(sounds==(pair['callback_sounds'] if key=='presentation' else pair['sounds']),f'{label} sound mismatch at {frame}')
            selected=[s for s,e in pair['samples'] if e['sequence']<event['sequence']]
            require(samples==tuple((0,s['registers']['M68K D1'],s['registers']['M68K D2']) for s in selected),f'{label} sample mismatch at {frame}')
        comparisons[label]={'calls':len(cases),'command':command,'output_sha256':hashlib.sha256(proc.stdout).hexdigest()}
    return {'ok':True,'calls':len(pairs),'comparisons':comparisons,'service_calls':len(pairs),
            'callbacks':dict(Counter(hex(e['pc']) for p in pairs for e in p['callbacks'])),
            'handlers':dict(Counter(hex(e['pc']) for p in pairs for e in p['handlers'])),
            'sound_requests':sum(len(p['sounds']) for p in pairs),'sample_requests':sum(len(p['samples']) for p in pairs),
            'action_boundaries':[{'frame':e['frame'],'pc':hex(e['pc'])} for e in trace['events'] if e['pc'] in EXTRA_PCS and e['registers']['M68K A6']==0xffff1ab4]}


def main(argv=None):
    return capture_main(argv,capture_recipe=recipe,comparator=compare_window,windows=WINDOWS,output_name='dispatch-movie',
        scope='continuous P1 actor wrapper through actual caller return with intermediate presentation/handler checks, return-only +46 service and control +42/+44; external controls/parameters/shared globals/mailbox/scratch/selector feeds; no full world/frame or audio parity')

if __name__=='__main__':raise SystemExit(main())
