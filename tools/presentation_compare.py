"""Original presentation/scheduled actor comparisons; no full-frame parity claim."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import PRESETS,verify_executable
from build_terrain_reference import verify_executable as reference_executable,REPORT
from actor_compare import compare_group,fixture,real_cases,catalog_entry,read_extracted,MAX_BANK_BYTES,MAX_SCENE_BYTES
from movement_probe import validate
from presentation_cases import case,goldens
from actor_cases import decode_results
from terrain_cases import encode_cases


def animation_cases():
    rows=[c for c,_ in goldens()]
    # Every mode byte/countdown byte pair, with callback-disabled/enabled paths
    # and both frame directions. Exact-zero countdown expiry only.
    rows.extend(case(mode=mode,counter=count,callback=5,target=2,cycles=2)
                for mode in range(256) for count in range(256))
    # Word-frame wrap and endpoint equality, with callback path and loop/bounce.
    for reverse in (0,2):
        rows.extend(case(mode=0x85|reverse|(8 if value&1 else 0),first=value,
                         begin=0,end=65535,target=value,callback=5,cycles=2)
                    for value in range(65536))
    for cb in (5,6):
        rows.extend(case(mode=0x85,target=2,callback=cb,cycles=value) for value in range(65536))
    # All four normal callbacks after forward/reverse advance at/non-endpoint;
    # loop and bounce decisions run BEFORE callback overwrites the presentation.
    rows.extend(case(mode=mode,first=frame,begin=0,end=5,target=frame,callback=cb,flags=flags)
                for mode in (0x85,0x87,0x8d,0x8f) for frame in (0,2,5)
                for cb in range(1,7) for flags in (0,0xffff))
    # Remaining non-callback bounce/loop paths, disabled target bit, repeat state.
    rows.extend(case(mode=mode,first=frame,begin=0,end=5,target=0x1234,callback=0,repeats=16,reload=reload)
                for mode in range(256) for frame in (0,2,5) for reload in (0,1,2,255))
    return rows


def scheduled_cases():
    rows=[]
    for handler in range(1,14):
        for direction in range(4):
            if handler==5 and direction&1 or handler==6 and direction&2:continue
            for jump in (0,255):
                for gate in (0,1):
                    for speed in (0,4,64,144,149,192,0xff40,0xffc0,65535):
                        rows.append(case(handler=handler,speed=speed,left=direction&1,right=direction&2,
                                         jump=jump,gate=gate,mode=0x81,counter=1))
    # Target callbacks choose the handler in this call, including jump priority.
    rows.extend(case(handler=handler,mode=0x87,first=42,begin=42,end=47,target=42,counter=1,
                     callback=cb,left=direction&1,right=direction&2,jump=jump,speed=speed)
                for handler in (9,10,11,12) for cb in range(1,5) for direction in range(4)
                for jump in (0,1) for speed in (0,64,0xffc0))
    # Inactive objects must not invoke even unknown callbacks/up/down actions.
    rows.extend(case(mode=mode,counter=1,first=2,target=2,up=1,down=1,callback=0) for mode in range(128))
    # Stateful invocation chains, both facings, drop/jump/release/landing.
    rows.extend(case(handler=handler,mode=0x81,left=left,right=right,jump=jump,drop=drop,repeats=16)
                for handler,left,right in ((7,0,1),(8,1,0),(7,1,0),(8,0,1))
                for jump in (0,1) for drop in (0,1))
    return rows


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug')
    p.add_argument('--rom',action='store_true',help='Also use cataloged terrain; original code ROM is always required')
    args=p.parse_args(argv);identity=inspect_file();verify_expected(identity)
    metadata=json.loads((ROOT/'re/presentation_step.json').read_text());data=DEFAULT_ROM.read_bytes();validate(data,metadata)
    native=verify_executable(args.preset,'wiznliz-actor');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/presentation-comparison')))
    report={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
            'scope':'F76C through return, supported callbacks, active gate and F8F6 through F906/F90C; later +46 service excluded',
            'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REPORT.read_text()),
            'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                       ('tools/presentation_compare.py','tools/presentation_probe.py','tests/presentation_cases.py','re/presentation_step.json','tools/actor_compare.py')}}
    try:
        rom=out/'reference-rom.bin';atomic_write(rom,data)
        scene,bank=fixture(True)
        report['groups'].append(compare_group(out,'presentation',scene,bank,animation_cases(),0,native,reference,rom,'--presentation'))
        observed=decode_results((out/'presentation/reference.txt').read_bytes(),report['groups'][0]['cases'])
        if observed[:len(goldens())]!=[e for _,e in goldens()]:raise ValueError('independent presentation golden mismatch')
        report['independent_goldens']=len(goldens())
        report['groups'].append(compare_group(out,'scheduled-flat',scene,bank,scheduled_cases(),0,native,reference,rom,'--scheduled'))
        scene,bank=fixture(False)
        authored=[case(handler=h,x=x,y=y,mode=0x81,speed=64 if x%8 else 0xffc0,drop=(x//4)%2)
                  for h in range(1,14) for x in range(116,372,4) for y in (105,109,113)]
        report['groups'].append(compare_group(out,'scheduled-authored',scene,bank,authored,257,native,reference,rom,'--scheduled'))
        if args.rom:
            entry=catalog_entry('scene.companion.0001','companion_scene_v1');base=catalog_entry(entry['structure']['base_bank_id'])
            _,scene=read_extracted(entry,MAX_SCENE_BYTES);_,bank=read_extracted(base,MAX_BANK_BYTES)
            report['groups'].append(compare_group(out,'scheduled-cataloged',scene,bank,real_cases(),257,native,reference,rom,'--scheduled'))
        report['rejections']=[]
        c=case(mode=0x85,target=2,callback=0)
        for mode in ('--presentation','--scheduled'):
            for kind in ('reference','native'):
                directory=out/'presentation'
                command=([str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),'0',mode] if kind=='reference'
                         else [str(native),'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin'),mode])
                proc=subprocess.run(command,input=encode_cases([c]),capture_output=True,timeout=10)
                expected=b'unsupported code boundary 00cafe' if kind=='reference' else b'unsupported presentation callback'
                if proc.returncode!=2 or proc.stdout or expected not in proc.stderr:raise ValueError('unknown callback not rejected at exact boundary')
                report['rejections'].append(dict(kind=kind,mode=mode,exit_status=proc.returncode,stderr=proc.stderr.decode()))
        report['cases']=sum(g['cases'] for g in report['groups'])
        report['visited_pcs']=sorted({pc for g in report['groups'] for pc in g['observation']['visited']})
        report['new_instructions_visited']=sum(any(r['start']<=pc<r['end_exclusive'] for r in metadata['regions']) for pc in report['visited_pcs'])
        if report['new_instructions_visited']!=sum(r['instruction_count'] for r in metadata['regions']):raise ValueError('incomplete presentation instruction coverage')
        report['ok']=True
    except (OSError,ValueError,subprocess.SubprocessError) as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True
        atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:report.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])
