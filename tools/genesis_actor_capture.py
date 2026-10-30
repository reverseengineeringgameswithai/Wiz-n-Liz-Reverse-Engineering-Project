#!/usr/bin/env python3
"""Owned GPGX actor-invocation captures; compares native semantic fields, not frames.

External runtime is read-only. All captures, checkpoints and translated terrain
fixtures go to ignored WizNLizPC local storage. No PC writes or ROM patches.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import verify_executable
sys.path.insert(0,str(ROOT/'tests'))
from actor_cases import HANDLERS,CALLBACKS,case,decode_results
from terrain_cases import encode_cases

BUILD_ID='6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6'
COMPARE_FIELDS='handler x y speed vertical delay flags mode first begin end counter reload target cycles callback scratch_x scratch_y'.split()


def save(path,value):
    atomic_write(path,(json.dumps(value,indent=2)+'\n').encode())


def require(b,message):
    if not b:raise ValueError(message)


def be(data,offset,size=2):return int.from_bytes(data[offset:offset+size],'big')


def block(event,label):return bytes.fromhex(next(b['hex'] for b in event['ranges'] if b['label']==label))


def actor_fields(data,original_callback=None):
    handler=be(data,0x16,4);callback=be(data,0x1a,4)
    require(handler in HANDLERS,'unsupported observed handler '+hex(handler))
    if callback not in CALLBACKS:
        require(original_callback is None or callback==original_callback,'unmodeled callback changed')
        callback=0xcafe # Logical retained token; byte preservation checked separately.
    return (HANDLERS.index(handler),be(data,2),be(data,4),be(data,0x22),be(data,0x26),be(data,0x2a),be(data,0x12),
            data[0],be(data,6),be(data,8),be(data,10),data[12],data[13],be(data,14),be(data,16),CALLBACKS.index(callback))


def terrain_fixture(ram):
    base=be(ram,0x140e);map_base=be(ram,0x4452,4)&0xffffff;record_base=be(ram,0x444e,4)&0xffffff
    require(be(ram,0x13a4)==256 and be(ram,0x13ae)==1023,'unsupported live terrain shape')
    require(0xff0000<=map_base<=0xffe000,'live terrain map outside RAM')
    cells=struct.unpack('>4096H',ram[map_base&65535:(map_base&65535)+8192])
    require(all((v&2047)>=base for v in cells),'live map precedes logical base')
    count=max((v&2047)-base for v in cells)+1
    start=(record_base+base*8)&0xffffff
    require(0xff0000<=start and start+count*8<=0x1000000,'live terrain records outside RAM')
    records=ram[start&65535:(start&65535)+count*8]
    bank=bytes(32)+struct.pack('>H',count-1)+bytes(32*count)+records
    # Pixel data and scene coordinates are unused, authored zeros. Collision
    # records/map are captured original RAM, normalized to logical base zero.
    scene=bytes(16)+bytes(32)+struct.pack('>HH4096H',128,32,*[(v-base)&65535 for v in cells])+bytes(8)
    return scene,bank,{'base':base,'map_bus':map_base,'record_bus':start,'records':count}


def compare_trace(trace,directory,native,scene,bank):
    require(trace['schemaVersion']==1 and trace['boundary']=='instruction-pre-execute','unsupported trace schema/boundary')
    require(type(trace['dropped']) is int and trace['dropped']==0 and trace['overflow'] is False
            and trace['error'] is None,'incomplete trace')
    require(0<len(trace['events'])<=20000,'invalid trace event count')
    require(all(a['sequence']<b['sequence'] for a,b in zip(trace['events'],trace['events'][1:])),
            'trace sequence is not strictly increasing')
    events=trace['events'];cases=[];expected=[];pairs=[];start=None;sounds=[];handlers=[]
    for event in events:
        require(event['kind']=='entry','unexpected inferred return in explicit dispatcher capture')
        pc=event['pc'];regs=event['registers']
        if pc==0xf904:
            require(start is None,'nested or unmatched actor entry')
            require(regs['M68K A6']==0xffff1ab4 and regs['M68K A5']==0xffff0690,'unexpected actor pair')
            start=event;sounds=[];handlers=[]
        elif pc==0xf906:
            require(start is not None,'unmatched actor return')
            require(all(regs[r]==start['registers'][r] for r in ('M68K A5','M68K A6','M68K A7')),'actor dispatcher stack/pair mismatch')
            require(start['sequence']<event['sequence'] and start['frame']==event['frame'],'invalid actor boundary order')
            a=block(start,'actor');control=block(start,'control');scratch=block(start,'scratch');gate=block(start,'gate')
            require(handlers and handlers[0]['pc']==be(a,0x16,4),'missing selected handler entry')
            require(handlers[0]['registers']['M68K A7']==regs['M68K A7']-4,'handler entry stack mismatch')
            require(be(block(handlers[0],'stack'),0,4)==0xf906,'handler return address mismatch')
            f=actor_fields(a)
            values=dict(zip(COMPARE_FIELDS[:16],f))
            values.update(positive=be(control,0x5a),negative=be(control,0x5c),damping=be(control,0x66),
                          air_acc=be(control,0x60),contact=be(control,0x6a),gravity=be(control,0x6c),
                          ground_acc=be(control,0x5e),impulse=be(control,0x62),jump_delay=be(control,0x64),
                          jump=control[0x16],drop=control[0x17],up=control[0x1a],down=control[0x1b],
                          left=control[0x1c],right=control[0x1d],gate=be(gate,0),sx=be(scratch,0),sy=be(scratch,2))
            cases.append(case(**values))
            after=block(event,'actor');sc=block(event,'scratch')
            # These handlers do not write any actor bytes beyond this contract.
            changed=set([0,*range(2,20),*range(22,30),34,35,38,39,42,43])
            require(all(a[i]==after[i] for i in range(78) if i not in changed),'uncontracted actor byte changed')
            expected.append((*actor_fields(after,be(a,0x1a,4)),be(sc,0),be(sc,2),tuple(sounds)))
            pairs.append({'frame':start['frame'],'entry':start['sequence'],'return':event['sequence'],
                          'handlers':[hex(h['pc']) for h in handlers]})
            start=None
        elif start is not None:
            if pc==0xfcb32:sounds.append(tuple(be(block(event,'sound'),i*2) for i in range(4)))
            elif pc in HANDLERS:handlers.append(event)
    require(start is None and cases,'incomplete/empty actor trace')
    for name,data in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/name,data)
    command=[str(native),'capture.scene',str(directory/'scene.bin'),'capture.bank',str(directory/'bank.bin')]
    p=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60)
    atomic_write(directory/'native.stdout',p.stdout);atomic_write(directory/'native.stderr',p.stderr)
    require(p.returncode==0,'native actor transport failed: '+p.stderr.decode())
    rows=decode_results(p.stdout,len(cases))
    for i,(actual,want) in enumerate(zip(rows,expected)):
        require(actual[:18]==want[:18],f'actor divergence {i} frame {pairs[i]["frame"]}: actual={actual[:18]} expected={want[:18]}')
        requests=tuple(tuple(actual[j:j+4]) for j in range(23,len(actual),4))
        require(requests==want[18],f'sound request divergence {i}')
    return {'ok':True,'calls':len(cases),'compared_fields':COMPARE_FIELDS+['ordered_sound_requests'],
            'sound_requests':sum(r[21] for r in rows),'pairs':pairs,'command':command,
            'native_output_sha256':hashlib.sha256(p.stdout).hexdigest()}


def run(args,out):
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'));sys.path.insert(0,str(external/'wiz'))
    from capture_scenarios import opened,route,advance,load_checkpoint,SCENARIOS
    verify_expected(inspect_file());native=verify_executable(args.preset,'wiznliz-actor')
    report={'ok':False,'scope':'F904-to-F906 actor fields and sound request arguments; not whole-frame/audio/scheduler parity',
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'native_build':json.loads((native.parent/'provenance.json').read_text()),'branches':[]}
    try:
        worker,initial=opened(out/'worker',DEFAULT_ROM)
        with worker:
            report['open']=initial;report['capabilities']=worker.request('capabilities')
            manifest=json.loads((external/'local/runtime/genesis-build.json').read_text())
            require(manifest['buildId']==BUILD_ID and initial['identity']['build']==manifest,'unverified runtime generation')
            expected_binaries={Path(k).name:v for k,v in manifest['binaries'].items()}
            expected_binaries['GenesisWorker.exe']=manifest['workerSha256']
            require(all(expected_binaries.get(k)==v for k,v in initial['identity']['binaries'].items()),
                    'loaded binaries differ from pinned manifest')
            capabilities=report['capabilities']['capabilities']
            require(all(capabilities[k] for k in ('frameAdvance','saveLoad','memoryInspection','ramEdits','routineTrace')),
                    'required worker capability unavailable')
            report['build_manifest']=manifest
            route(worker);checkpoint=worker.request('save',{'name':'gameplay'})
            report['start_checkpoint']=checkpoint
            # Original route, new ordinary idle-jump/fast-direction routes, and
            # explicitly edited one-call landing/fast states from the same save.
            branches=[('ordinary-route',[(n,b) for _,n,b in SCENARIOS],[]),
                      ('idle-jump',[(1,['P1 B']),(4,['P1 B']),(8,[])],[]),
                      ('fast-right',[(55,['P1 Right']),(1,['P1 Right','P1 B']),(5,[])],[]),
                      ('fast-left',[(65,['P1 Left']),(1,['P1 Left','P1 B']),(5,[])],[]),
                      ('landing-idle-right',[(1,[])],[(0x16,4,0xab04),(0x22,2,0),(0x26,2,0xffff),(0x12,2,0x800)]),
                      ('landing-idle-left',[(1,[])],[(0x16,4,0xab04),(0x22,2,0),(0x26,2,0xffff),(0x12,2,0)])]
            recipe={'pcs':[0xf904,0xf906,0xfcb32]+HANDLERS[1:],'returns':False,'registers':True,'maxEvents':20000,
                    'ranges':[{'label':label,'domain':'68K RAM','offset':offset,'length':length}
                              for label,offset,length in [('actor',0x1ab4,78),('control',0x690,112),('scratch',0x4442,4),('gate',0xf16,2),('sound',0xa9e,8)]]+
                             [{'label':'stack','domain':'68K RAM','register':'M68K A7','offset':0,'length':4}]}
            report['recipe']=recipe
            for name,rows,edits in branches:
                directory=out/name;directory.mkdir()
                load_checkpoint(worker,checkpoint)
                edit_record=None
                if edits:
                    writes=[{'domain':'68K RAM','offset':0x1ab4+offset,
                             'expectedHex':worker.read_bytes('68K RAM',0x1ab4+offset,size).hex(),
                             'hex':value.to_bytes(size,'big').hex()} for offset,size,value in edits]
                    edit_record=worker.request('experiment.edit',{'expectedFrame':1983,'writes':writes})
                before=worker.read_bytes('68K RAM',0,65536);scene,bank,terrain=terrain_fixture(before)
                worker.request('trace.configure',recipe)
                for count,buttons in rows:advance(worker,count,buttons)
                trace=worker.request('trace.drain');save(directory/'trace.json',trace)
                require(trace['identity']==initial['identity'],'trace identity differs from opened worker')
                end=worker.request('save',{'name':name});after=worker.read_bytes('68K RAM',0,65536)
                sidecar=json.loads(Path(end['provenancePath']).read_text())
                require(sidecar['identity']==initial['identity'],'checkpoint identity differs')
                require(terrain_fixture(after)[:2]==(scene,bank),'terrain changed within trace window')
                comparison=compare_trace(trace,directory,native,scene,bank);save(directory/'comparison.json',comparison)
                entry={'name':name,'classification':'controlled RAM edit' if edits else 'ordinary gameplay',
                       'rows':rows,'edits':edit_record,'terrain':terrain,'end_checkpoint':end,'comparison':comparison,
                       'artifact_sha256':{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in (directory/'trace.json',directory/'comparison.json',directory/'cases.txt',
                                                    directory/'scene.bin',directory/'bank.bin',Path(end['provenancePath']))}}
                # Preserve an explicit byte identity for every source used by the comparison.
                # Restore the same start and apply the identical edits without
                # hooks; compare declared exposed state after subsequent execution.
                load_checkpoint(worker,checkpoint)
                if edits:worker.request('experiment.edit',{'expectedFrame':1983,'writes':writes})
                worker.request('trace.configure',{})
                for count,buttons in rows:advance(worker,count,buttons)
                replay=worker.request('snapshot')
                require(replay['canonicalSha256']==end['snapshot']['canonicalSha256'],'hooked/unhooked replay divergence')
                entry['unhooked_hash']=replay['canonicalSha256'];report['branches'].append(entry)
            report['calls']=sum(b['comparison']['calls'] for b in report['branches'])
            hits=Counter(pc for b in report['branches'] for pair in b['comparison']['pairs'] for pc in pair['handlers'])
            require(all(hits[hex(pc)] for pc in (0xa27e,0xa6c8,0xa88e)),'targeted missing paths not reached')
            report['handler_hits']=dict(hits);report['ok']=True
    except Exception as e:
        report['error']=str(e);raise
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug')
    parser.add_argument('--preset',choices=('debug','release','sanitize'),default='debug');args=parser.parse_args(argv)
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/genesis-actor')))
    try:
        result=run(args,out);print(json.dumps({'ok':result['ok'],'calls':result['calls'],'report':str(out/'report.json')},indent=2));return int(not result['ok'])
    except Exception as e:
        save(out/'failure.json',{'error':str(e)});print(json.dumps({'ok':False,'error':str(e),'report':str(out/'report.json')}));return 1

if __name__=='__main__':raise SystemExit(main())
