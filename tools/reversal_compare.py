"""Original fast reversal and dependent effect execution versus bounded native code."""
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
from actor_cases import case
from reversal_cases import actor_goldens,effect_case,effect_goldens,decode_actor_rows
from movement_probe import validate


def actor_cases():
    rows=[c for c,_ in actor_goldens()]
    for h in (5,6,14,15):
        for speed in (0,1,4,31,32,144,145,160,192,193,32767,32768,0xff3f,0xff40,0xff60,0xff6f,0xff70,65532,65535):
            for direction in range(4):
                for jump in (0,255):
                    for gate in (0,1):
                        rows.append(case(handler=h,speed=speed,left=direction&1,right=direction&2,jump=jump,gate=gate,mode=0x81,counter=2,flags=0xa5a5))
    for h in (14,15):
        for acceleration in (0,1,8,192,32767,32768,65535):
            for speed in (0,4,144,32767,32768,65535):
                for damping in (0,3,65535):
                    rows.append(case(handler=h,speed=speed,ground_acc=acceleration,damping=damping,left=1,right=1))
    for h in (5,6,14,15):
        for x in (0,1,127,128,65535):
            for y in (0,105,109,113,65535):
                for drop in (0,1):
                    rows.append(case(handler=h,x=x,y=y,speed=64,left=h in (5,14),right=h in (6,15),drop=drop,flags=65535))
    return rows


def scheduled_cases():
    rows=[]
    for h in (5,6,14,15):
        for speed in (0,64,160,0xff60,0xffc0):
            for jump in (0,1):
                for direction in range(4):
                    rows.append(case(handler=h,speed=speed,left=direction&1,right=direction&2,jump=jump,
                                     mode=0x81,first=2,begin=0,end=5,counter=2,reload=2,repeats=16))
    for cb in (7,8):
        for direction in range(4):
            for jump in (0,1):
                for gate in (0,1):
                    rows.append(case(handler=14 if cb==7 else 15,mode=0x85,first=57,begin=52,end=57,
                                     target=57,counter=1,reload=3,callback=cb,left=direction&1,right=direction&2,
                                     jump=jump,gate=gate,speed=64,flags=0xffff))
    return rows


def effect_cases():
    rows=[c for c,_ in effect_goldens()]
    rows.extend(effect_case(side=side,owner_x=x,owner_y=x) for side in (0,1) for x in range(65536))
    rows.extend(effect_case(mode=mode,counter=count,first=220,target=220,side=mode&1)
                for mode in range(256) for count in range(256))
    rows.extend(effect_case(mode=mode,first=frame,begin=0,end=65535,target=frame,counter=1,reload=reload,repeats=repeats)
                for mode in (0x80,0x81,0x83,0x85,0x87,0x89,0x8b,0x8d,0x8f)
                for frame in (0,1,215,220,32767,32768,65535) for reload in (0,1,2,255) for repeats in (1,16,256))
    return rows


def compare(out,name,mode,scene,bank,rows,base,native,reference,rom):
    directory=out/name;directory.mkdir();map_data,records=reference_resources(scene,bank,base)
    inputs={'scene.bin':scene,'bank.bin':bank,'map.bin':map_data,'records.bin':records,'cases.txt':encode_cases(rows)}
    for n,data in inputs.items():atomic_write(directory/n,data)
    r={'cases':len(rows),'name':name,'mode':mode,'inputs':{n:hashlib.sha256(d).hexdigest() for n,d in inputs.items()},'processes':{}}
    commands={'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),str(base),mode],
              'native':[str(native),'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin'),mode]}
    results={}
    for kind,command in commands.items():
        with (directory/'cases.txt').open('rb') as inp,(directory/f'{kind}.txt').open('wb') as output:
            p=subprocess.run(command,stdin=inp,stdout=output,stderr=subprocess.PIPE,timeout=120,
                env=os.environ|{'ASAN_OPTIONS':'detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'})
        atomic_write(directory/f'{kind}.stderr',p.stderr)
        r['processes'][kind]={'command':command,'exit_status':p.returncode}
        if p.returncode:raise ValueError(f'{name} {kind}: '+p.stderr[:2000].decode())
        data=(directory/f'{kind}.txt').read_bytes();r['processes'][kind]['sha256']=hashlib.sha256(data).hexdigest()
        results[kind]=[tuple(map(int,l.split())) for l in data.splitlines()] if mode=='--effect' else decode_actor_rows(data,len(rows))
        if len(results[kind])!=len(rows) or (mode=='--effect' and any(len(row)!=14 for row in results[kind])):raise ValueError('effect result extent differs')
        if kind=='reference':r['observation']=json.loads(p.stderr)
    for i,(a,b) in enumerate(zip(results['reference'],results['native'])):
        if a!=b:raise ValueError(f'{name} case {i}: {rows[i]} original={a}, native={b}')
    goldens=actor_goldens() if name=='actor-flat' else effect_goldens() if name=='effects' else []
    if results['reference'][:len(goldens)]!=[e for _,e in goldens]:raise ValueError(f'{name} authored golden mismatch')
    r['independent_goldens']=len(goldens);r['ok']=True
    atomic_write(directory/'report.json',(json.dumps(r,indent=2)+'\n').encode());return r


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug')
    p.add_argument('--rom',action='store_true',help='Add cataloged terrain; original code ROM always required');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/reversal_step.json').read_text());validate(data,meta)
    native=verify_executable(args.preset,'wiznliz-actor');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/reversal-comparison')))
    r={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
       'scope':'bounded actor + typed effect spawn, original allocator success, original effect scheduler/release/follow; no general world pool or full-frame parity',
       'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REPORT.read_text()),
       'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/reversal_compare.py','tests/reversal_cases.py','re/reversal_step.json')}}
    try:
        rom=out/'rom.bin';atomic_write(rom,data);scene,bank=fixture(True)
        for name,mode,rows in (('actor-flat','--reversal',actor_cases()),('scheduled-flat','--reversal-scheduled',scheduled_cases()),('effects','--effect',effect_cases())):
            r['groups'].append(compare(out,name,mode,scene,bank,rows,0,native,reference,rom))
        rows=[case(handler=h,x=x,y=y,speed=64 if x%8 else 0xffc0,left=h in (5,14),right=h in (6,15),mode=0x81,counter=2)
              for h in (5,6,14,15) for x in range(116,372,4) for y in (105,109,113)]
        scene,bank=fixture(False);r['groups'].append(compare(out,'authored-terrain','--reversal-scheduled',scene,bank,rows,257,native,reference,rom))
        if args.rom:
            entry=catalog_entry('scene.companion.0001','companion_scene_v1');base=catalog_entry(entry['structure']['base_bank_id'])
            _,scene=read_extracted(entry,MAX_SCENE_BYTES);_,bank=read_extracted(base,MAX_BANK_BYTES)
            rows=[case(handler=h,x=116+col*8,y=105+row*8,speed=64 if col%8 else 0xffc0,left=h in (5,14),right=h in (6,15),mode=0x81,counter=2)
                  for row in range(28) for col in range(0,128,4) for h in (5,6,14,15)]
            r['groups'].append(compare(out,'cataloged-terrain','--reversal-scheduled',scene,bank,rows,257,native,reference,rom))
        r['rejections']=[];directory=out/'actor-flat'
        for kind in ('reference','native'):
            command=([str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),'0','--reversal-empty'] if kind=='reference'
                     else [str(native),'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin'),'--reversal-empty'])
            for h in (5,6):
                proc=subprocess.run(command,input=encode_cases([case(handler=h,left=h==5,right=h==6)]),capture_output=True,timeout=10)
                message=b'unsupported code boundary 00f9d0' if kind=='reference' else b'reversal allocation exhausted'
                if proc.returncode!=2 or proc.stdout or message not in proc.stderr:raise ValueError('exhaustion not rejected at declared boundary')
                r['rejections'].append({'kind':kind,'handler':h,'command':command,'exit_status':proc.returncode,'stderr':proc.stderr.decode()})
        r['cases']=sum(g['cases'] for g in r['groups']);r['visited_pcs']=sorted({pc for g in r['groups'] for pc in g['observation']['visited']})
        r['new_instructions_visited']=sum(any(a['start']<=pc<a['end_exclusive'] for a in meta['regions']) for pc in r['visited_pcs'])
        if r['new_instructions_visited']!=sum(a['instruction_count'] for a in meta['regions']):raise ValueError('new instruction coverage incomplete')
        r['ok']=True
    except Exception as e:r['error']=str(e)
    finally:
        verify_expected(inspect_file());r['rom_unchanged']=True;atomic_write(out/'report.json',(json.dumps(r,indent=2)+'\n').encode())
    print(json.dumps({k:r.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not r['ok'])

if __name__=='__main__':raise SystemExit(main())
