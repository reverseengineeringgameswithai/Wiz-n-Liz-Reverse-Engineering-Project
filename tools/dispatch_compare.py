"""Original/native complete actor wrapper, return-only selector and AA50 callback parity."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import PRESETS,verify_executable
from build_terrain_reference import verify_executable as reference_executable,REPORT
from actor_compare import fixture,catalog_entry,read_extracted,MAX_BANK_BYTES,MAX_SCENE_BYTES
from actions_compare import compare
from terrain_cases import encode_cases
from actions_cases import case as action_case,expected as action_expected
from dispatch_cases import case,decode,goldens
from movement_probe import validate


def boundary_cases():
    rows=[c for c,_ in goldens()]
    rows.extend(case(handler=20,mode=128,x=v,y=v,tracking_selector=v) for v in range(65536))
    # Full mode/countdown sweep, including inactive callbacks that must not fire.
    rows.extend(case(handler=20,mode=mode,counter=count,reload=0,first=542,begin=542,end=551,
                     target=542,callback=11,flags=0xa5a5) for mode in range(256) for count in range(256))
    for flags in (0,0x800):
        for bits in range(64):
            for speed in (0,4,64,144,192,0xff40,0xfffc):
                for delay in (0,1,32767,32768,65535):
                    rows.append(case(handler=20,flags=flags,speed=speed,vertical=32768,delay=delay,
                        mode=135,first=542,begin=542,end=551,target=542,counter=1,reload=3,callback=11,
                        **dict(zip(('jump','drop','up','down','left','right'),((bits>>i)&1 for i in range(6))))))
    # Inactive unknown service and all sentinel alternatives still execute control tail.
    rows.extend(case(handler=20,mode=mode,service=0,tracking_selector=v,x=65534,y=65532)
                for mode in (0,1,5,127) for v in (0,1,32767,32768,65534,65535))
    return rows


def callback_goldens():
    rows=[]
    for flags in (0,0x800,0xa5a5,65535):
        c=action_case(handler=20,flags=flags,mode=135,first=542,begin=542,end=551,target=542,
                      counter=1,reload=3,callback=11,speed=65535,vertical=32768,delay=3)
        rows.append((c,action_expected(c,handler=1,vertical=0,delay=65535,mode=129,first=58,begin=60,end=61,counter=6,reload=6)))
    return rows


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug')
    p.add_argument('--rom',action='store_true',help='Add cataloged terrain; original code ROM always required');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/dispatch_step.json').read_text());validate(data,meta)
    native=verify_executable(args.preset,'wiznliz-actor');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/dispatch-comparison')))
    r={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
       'scope':'F8F6 through actual RTS with verified return-only service; explicit control coordinates; no full world/frame parity',
       'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REPORT.read_text()),
       'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/dispatch_compare.py','tests/dispatch_cases.py','re/dispatch_step.json')}}
    try:
        rom=out/'rom.bin';atomic_write(rom,data);scene,bank=fixture(True)
        r['groups'].append(compare(out,'wrapper-flat','--dispatch',scene,bank,boundary_cases(),0,native,reference,rom,goldens(),decode))
        cb=callback_goldens();r['groups'].append(compare(out,'callback-only','--actions-presentation',scene,bank,[c for c,_ in cb],0,native,reference,rom,cb))
        rows=[case(handler=20,flags=flags,x=x,y=y,mode=135,first=542,begin=542,end=551,target=542,counter=1,reload=3,callback=11,jump=jump)
              for flags in (0,0x800) for x in range(116,372,4) for y in (105,109,113) for jump in (0,1)]
        scene,bank=fixture(False);r['groups'].append(compare(out,'authored-terrain','--dispatch',scene,bank,rows,257,native,reference,rom,decoder=decode))
        if args.rom:
            entry=catalog_entry('scene.companion.0001','companion_scene_v1');base=catalog_entry(entry['structure']['base_bank_id'])
            _,scene=read_extracted(entry,MAX_SCENE_BYTES);_,bank=read_extracted(base,MAX_BANK_BYTES)
            rows=[case(handler=20,flags=flags,x=116+col*8,y=105+row*8,mode=135,first=542,begin=542,end=551,target=542,counter=1,reload=3,callback=11)
                  for row in range(28) for col in range(0,128,4) for flags in (0,0x800)]
            r['groups'].append(compare(out,'cataloged-terrain','--dispatch',scene,bank,rows,257,native,reference,rom,decoder=decode))
        r['cases']=sum(g['cases'] for g in r['groups']);r['visited_pcs']=sorted({pc for g in r['groups'] for pc in g['observation']['visited']})
        r['new_instructions_visited']=sum(any(a['start']<=pc<a['end_exclusive'] for a in meta['regions']) for pc in r['visited_pcs'])
        if r['new_instructions_visited']!=sum(a['instruction_count'] for a in meta['regions']):raise ValueError('new instruction coverage incomplete')
        # Both original and native must reject actual invoked unknown selectors.
        r['rejections']=[]
        directory=out/'wrapper-flat'
        commands={
            'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),'0','--dispatch'],
            'native':[str(native),'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin'),'--dispatch']}
        for name,c,message in (('service',case(handler=20,mode=128,service=0),b'unsupported actor service'),
                               ('callback',case(handler=20,mode=133,first=2,target=2,counter=1,callback=0),b'unsupported presentation callback')):
            for kind,cmd in commands.items():
                proc=subprocess.run(cmd,input=encode_cases([c]),capture_output=True,timeout=10)
                expected=b'unsupported code boundary 00cafe' if kind=='reference' else message
                if proc.returncode!=2 or proc.stdout or expected not in proc.stderr:raise ValueError('unknown selector was not rejected at its boundary')
                r['rejections'].append(dict(case=name,kind=kind,exit_status=proc.returncode,stderr=proc.stderr.decode()))
        r['ok']=True
    except Exception as e:r['error']=str(e)
    finally:
        verify_expected(inspect_file());r['rom_unchanged']=True;atomic_write(out/'report.json',(json.dumps(r,indent=2)+'\n').encode())
    print(json.dumps({k:r.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not r['ok'])

if __name__=='__main__':raise SystemExit(main())
