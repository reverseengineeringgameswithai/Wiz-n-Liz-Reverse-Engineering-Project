"""Up/down actions, contextual callbacks and sample-mailbox original/native parity."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import PRESETS,verify_executable
from build_terrain_reference import verify_executable as reference_executable,REPORT
from actor_compare import fixture,catalog_entry,read_extracted,MAX_BANK_BYTES,MAX_SCENE_BYTES
from terrain_compare import reference_resources
from terrain_cases import encode_cases
from actions_cases import case,decode,goldens,presentation_goldens,scheduled_goldens
from movement_probe import validate


def handler_cases():
    rows=[c for c,_ in goldens()]
    # Exhaust both wrapping interval arithmetic and every signed cooldown value.
    rows.extend(case(handler=16,up=1,raw=0,interval=v) for v in range(65536))
    rows.extend(case(handler=16,up=1,raw=0,cooldown=v) for v in range(65536))
    rows.extend(case(handler=16,up=1,raw=raw,world_mode=mode,cooldown=timer)
                for raw in range(256) for mode in (0,7,18,19,20,65535) for timer in (0,32767,32768,65535))
    for h in (7,8,16,17,18,19):
        for bits in range(64):
            for speed in (0,1,4,5,65531,65532,65535):
                rows.append(case(handler=h,mode=128,flags=0xa5a5,speed=speed,raw=0,
                                 **dict(zip(('jump','drop','up','down','left','right'),((bits>>i)&1 for i in range(6))))))
    for h in (16,18):
        for begin in (0,1,32767,32768,65535):
            for jump in (0,1):
                rows.append(case(handler=h,begin=begin,jump=jump,raw=0,interval=9,gate=65535))
    return rows


def phase_cases(scheduled):
    rows=[c for c,_ in (scheduled_goldens() if scheduled else presentation_goldens())]
    for cb in (9,10):
        for flags in (0,0x800,0xa5a5,65535):
            for bits in range(64):
                for raw in (0,255):
                    rows.append(case(handler=17,callback=cb,flags=flags,mode=135,first=31,begin=30,end=35,
                        target=31,counter=1,reload=2,raw=raw,
                        **dict(zip(('jump','drop','up','down','left','right'),((bits>>i)&1 for i in range(6))))))
    # Presentation phase alone can run inactive modes; scheduled phase gates them.
    rows.extend(case(handler=18,down=1,mode=mode,counter=count,callback=9,first=40,begin=36,end=41,target=40)
                for mode in range(256) for count in (0,1,2,255))
    rows.extend(case(handler=h,mode=0x80,flags=flags,up=h==7,down=h==8,repeats=n)
                for h in (7,8) for flags in (0,0x800) for n in (1,2,3,8,16))
    return rows


def compare(out,name,mode,scene,bank,rows,base,native,reference,rom,expected=(),decoder=decode):
    directory=out/name;directory.mkdir();map_data,records=reference_resources(scene,bank,base)
    inputs={'scene.bin':scene,'bank.bin':bank,'map.bin':map_data,'records.bin':records,'cases.txt':encode_cases(rows)}
    for n,data in inputs.items():atomic_write(directory/n,data)
    report={'cases':len(rows),'name':name,'mode':mode,'inputs':{n:hashlib.sha256(d).hexdigest() for n,d in inputs.items()},'processes':{}}
    commands={'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),str(base),mode],
              'native':[str(native),'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin'),mode]}
    results={}
    for kind,command in commands.items():
        with (directory/'cases.txt').open('rb') as inp,(directory/f'{kind}.txt').open('wb') as output:
            proc=subprocess.run(command,stdin=inp,stdout=output,stderr=subprocess.PIPE,timeout=120,
                env=os.environ|{'ASAN_OPTIONS':'detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'})
        atomic_write(directory/f'{kind}.stderr',proc.stderr)
        report['processes'][kind]={'command':command,'exit_status':proc.returncode}
        if proc.returncode:raise ValueError(f'{name} {kind}: '+proc.stderr[:2000].decode())
        data=(directory/f'{kind}.txt').read_bytes();report['processes'][kind]['sha256']=hashlib.sha256(data).hexdigest()
        results[kind]=decoder(data,len(rows))
        if kind=='reference':report['observation']=json.loads(proc.stderr)
    for i,(a,b) in enumerate(zip(results['reference'],results['native'])):
        if a!=b:raise ValueError(f'{name} case {i}: {rows[i]} original={a}, native={b}')
    for i,(_,e) in enumerate(expected):
        if results['reference'][i]!=e:raise ValueError(f'{name} authored golden {i}: {results["reference"][i]} != {e}')
    report['independent_goldens']=len(expected);report['ok']=True
    atomic_write(directory/'report.json',(json.dumps(report,indent=2)+'\n').encode());return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug')
    p.add_argument('--rom',action='store_true',help='Add cataloged terrain; original code ROM always required');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/actions_step.json').read_text());validate(data,meta)
    native=verify_executable(args.preset,'wiznliz-actor');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/actions-comparison')))
    r={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
       'scope':'handler/contextual presentation/scheduled actor plus action globals and sample mailbox writes; no world timing, mailbox consumption or audio parity',
       'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REPORT.read_text()),
       'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/actions_compare.py','tests/actions_cases.py','re/actions_step.json')}}
    try:
        rom=out/'rom.bin';atomic_write(rom,data);scene,bank=fixture(True)
        for name,mode,rows,expected in (('handler-flat','--actions',handler_cases(),goldens()),
                ('presentation-flat','--actions-presentation',phase_cases(False),presentation_goldens()),
                ('scheduled-flat','--actions-scheduled',phase_cases(True),scheduled_goldens())):
            r['groups'].append(compare(out,name,mode,scene,bank,rows,0,native,reference,rom,expected))
        rows=[case(handler=17,flags=flags,x=x,y=y,mode=135,first=31,begin=30,end=35,target=31,counter=1,reload=2,callback=10,
                   jump=jump,up=not jump,raw=0)
              for flags in (0,0x800) for x in range(116,372,4) for y in (105,109,113) for jump in (0,1)]
        scene,bank=fixture(False);r['groups'].append(compare(out,'authored-terrain','--actions-scheduled',scene,bank,rows,257,native,reference,rom))
        if args.rom:
            entry=catalog_entry('scene.companion.0001','companion_scene_v1');base=catalog_entry(entry['structure']['base_bank_id'])
            _,scene=read_extracted(entry,MAX_SCENE_BYTES);_,bank=read_extracted(base,MAX_BANK_BYTES)
            rows=[case(handler=17,flags=flags,x=116+col*8,y=105+row*8,mode=135,first=31,begin=30,end=35,target=31,counter=1,reload=2,callback=10,jump=1)
                  for row in range(28) for col in range(0,128,4) for flags in (0,0x800)]
            r['groups'].append(compare(out,'cataloged-terrain','--actions-scheduled',scene,bank,rows,257,native,reference,rom))
        r['cases']=sum(g['cases'] for g in r['groups']);r['visited_pcs']=sorted({pc for g in r['groups'] for pc in g['observation']['visited']})
        r['new_instructions_visited']=sum(any(a['start']<=pc<a['end_exclusive'] for a in meta['regions']) for pc in r['visited_pcs'])
        if r['new_instructions_visited']!=sum(a['instruction_count'] for a in meta['regions']):raise ValueError('new instruction coverage incomplete')
        r['ok']=True
    except Exception as e:r['error']=str(e)
    finally:
        verify_expected(inspect_file());r['rom_unchanged']=True;atomic_write(out/'report.json',(json.dumps(r,indent=2)+'\n').encode())
    print(json.dumps({k:r.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not r['ok'])

if __name__=='__main__':raise SystemExit(main())
