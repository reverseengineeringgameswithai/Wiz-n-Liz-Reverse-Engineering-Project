"""Original airborne execution versus native motion and continuation boundaries; local only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import PRESETS,verify_executable
from build_terrain_reference import verify_executable as reference_executable,REPORT as REFERENCE_REPORT
from airborne_probe import validate
from movement_probe import validate as validate_movement
from terrain_probe import validate as validate_terrain
from terrain_compare import reference_resources
from bank_atlas import catalog_entry,read_extracted,MAX_BANK_BYTES
from scene_preview import MAX_SCENE_BYTES

sys.path.insert(0,str(ROOT/'tests'))
from airborne_cases import fixture,case,goldens,decode_results
from terrain_cases import encode_cases


def flat_cases():
    cases=[c for c,_ in goldens()]
    cases.extend(case(op=op,speed=v) for op in (5,6) for v in range(65536))
    cases.extend(case(op=4,speed=v,flags=flags) for flags in (0,0x800) for v in range(65536))
    cases.extend(case(update=2,vertical=v) for v in range(65536))
    cases.extend(case(delay=v,boost=255) for v in range(65536))
    for acceleration in (0,12,192,32768,65535):
        for gate in (0,1,65535):
            for left,right in ((0,0),(1,0),(0,1),(255,128)):
                for speed in (0,1,65535,191,192,193,32767,32768):
                    cases.append(case(update=2,vertical=16,gravity=0,speed=speed,acceleration=acceleration,
                                      gate=gate,left=left,right=right,flags=0xa5a5))
    for gravity in (0,1,4,32767,32768,65535):
        for vertical in (0,1,32767,32768,0xffcf,0xffd0,65535):
            cases.append(case(update=2,vertical=vertical,gravity=gravity))
    for op in (5,6,4):
        for speed in (0,1,32767,32768,65535):
            for limit in (0,1,32767,32768,65535):
                cases.append(case(op=op,speed=speed,positive=limit,negative=limit,flags=0x800))
                cases.append(case(op=op,speed=speed,positive=limit,negative=limit))
    return cases


def authored_cases():
    cases=[]
    verticals=(0xffcc,0xfff8,0,16,64)
    for op in (0,1,2,3):
        for x in range(116,372):
            for y in range(105,113):
                cases.append(case(op=op,x=x,y=y,speed=64 if x%2 else 0xffc0,vertical=verticals[x%5],flags=(x%2)*0x800))
    rng=random.Random(0x414952)
    for i in range(2048):
        cases.append(case(x=rng.randrange(65536),y=rng.randrange(120,201),speed=rng.choice((0,1,32,193,0xff3f,0xffe0,65535)),
                          vertical=rng.choice((0xffcf,0xffd0,0xfff8,0,8,48)),delay=rng.choice((0,1,2,65535,32768)),
                          flags=rng.randrange(65536),boost=rng.randrange(2),left=rng.randrange(2),right=rng.randrange(2),
                          gate=rng.randrange(2),sx=rng.randrange(65536),sy=rng.randrange(65536),repeats=1+i%8))
    return cases


def real_cases():
    cases=[]
    for row in range(30):
        for column in range(128):
            for speed,vertical in ((64,16),(0xffc0,0xffd0),(0,0)):
                cases.append(case(x=116+column*8+(row%8),y=105+row*8+(column%8),speed=speed,
                                  vertical=vertical,flags=(column%2)*0x800))
    for column in range(128):
        for speed in (32,0xffe0):
            cases.append(case(x=116+column*8,y=169,speed=speed,vertical=32,delay=3,boost=1,repeats=16))
    return cases


def compare_group(out,name,scene,bank,cases,base,native,reference,rom):
    directory=out/name;directory.mkdir();map_data,records=reference_resources(scene,bank,base)
    inputs={'scene.bin':scene,'bank.bin':bank,'map.bin':map_data,'records.bin':records,'cases.txt':encode_cases(cases)}
    for filename,data in inputs.items():atomic_write(directory/filename,data)
    result={'name':name,'base':base,'cases':len(cases),'inputs':{k:hashlib.sha256(v).hexdigest() for k,v in inputs.items()},'processes':{}}
    commands={'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),str(base),'--airborne'],
              'native':[str(native),'comparison.scene',str(directory/'scene.bin'),'comparison.bank',str(directory/'bank.bin')]}
    environment={'ASAN_OPTIONS':'detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'}
    rows={}
    for kind,command in commands.items():
        with (directory/'cases.txt').open('rb') as input_stream,(directory/(kind+'.txt')).open('wb') as output:
            process=subprocess.run(command,stdin=input_stream,stdout=output,stderr=subprocess.PIPE,cwd=ROOT,env=os.environ|environment,timeout=60)
        atomic_write(directory/(kind+'.stderr'),process.stderr)
        result['processes'][kind]={'command':command,'exit_status':process.returncode,'environment':environment}
        atomic_write(directory/'report.json',(json.dumps(result,indent=2)+'\n').encode())
        if process.returncode:raise ValueError(f'{name} {kind}: {process.stderr[:2000].decode(errors="replace")}')
        data=(directory/(kind+'.txt')).read_bytes();rows[kind]=decode_results(data,len(cases))
        result['processes'][kind]['output_sha256']=hashlib.sha256(data).hexdigest()
        if kind=='reference':result['observation']=json.loads(process.stderr)
    for i,(observed,actual) in enumerate(zip(rows['reference'],rows['native'])):
        if observed!=actual:raise ValueError(f'airborne mismatch {name} case {i} {cases[i]}: original={observed} native={actual}')
    if name=='flat':
        for i,(_,expected) in enumerate(goldens()):
            if rows['reference'][i]!=expected:raise ValueError(f'independent airborne golden mismatch {i}')
        result['independent_goldens']=len(goldens())
    result['horizontal_steps']=sum(r[15] for r in rows['reference'])
    result['settle_calls']=sum(r[16] for r in rows['reference'])
    result['landings']=sum(r[17] for r in rows['reference'])
    result['entry_calls']=sum(r[18] for r in rows['reference'])
    result['immediate_continuations']=sum(r[19] for r in rows['reference']);result['ok']=True
    atomic_write(directory/'report.json',(json.dumps(result,indent=2)+'\n').encode());return result


def check_rejections(out,native,reference,rom):
    directory=out/'flat'
    commands={'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),'0','--airborne'],
              'native':[str(native),'comparison.scene',str(directory/'scene.bin'),'comparison.bank',str(directory/'bank.bin')]}
    results=[]
    for kind,command in commands.items():
        process=subprocess.run(command,input=encode_cases([case(y=361)]),capture_output=True,timeout=10)
        if process.returncode!=2 or process.stdout:raise ValueError('airborne invalid address was not rejected')
        expected=b'outside declared fixture' if kind=='reference' else b'outside map resource'
        if expected not in process.stderr:raise ValueError('airborne rejection had an unexpected cause')
        results.append({'kind':kind,'case':case(y=361),'command':command,'exit_status':process.returncode,'stderr':process.stderr.decode()})
    return results


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preset',choices=PRESETS,default='debug')
    parser.add_argument('--rom',action='store_true',help='Add cataloged terrain states; original routine ROM is always required')
    args=parser.parse_args(argv);identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes()
    metadata=json.loads((ROOT/'re/airborne_update.json').read_text());validate(data,metadata)
    validate_terrain(data,json.loads((ROOT/'re/terrain_query.json').read_text()))
    validate_movement(data,json.loads((ROOT/'re/movement_step.json').read_text()))
    native=verify_executable(args.preset,'wiznliz-airborne');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/airborne-comparison')))
    report={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
            'scope':'airborne and landing state to RTS or explicit immediate idle boundary; no idle execution, full controller, frame timing or register/CCR ABI',
            'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REFERENCE_REPORT.read_text()),
            'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('tools/airborne_compare.py','tools/airborne_probe.py','tests/airborne_cases.py','re/airborne_update.json','tools/movement_probe.py','re/movement_step.json','re/terrain_query.json')}}
    try:
        rom=out/'reference-rom.bin';atomic_write(rom,data)
        for name,flat,cases,base in (('flat',True,flat_cases(),0),('authored',False,authored_cases(),257)):
            scene,bank=fixture(flat);report['groups'].append(compare_group(out,name,scene,bank,cases,base,native,reference,rom))
        report['rejections']=check_rejections(out,native,reference,rom)
        if args.rom:
            entry=catalog_entry('scene.companion.0001','companion_scene_v1');base=catalog_entry(entry['structure']['base_bank_id'])
            _,scene=read_extracted(entry,MAX_SCENE_BYTES);_,bank=read_extracted(base,MAX_BANK_BYTES)
            report['groups'].append(compare_group(out,'cataloged-scene',scene,bank,real_cases(),257,native,reference,rom))
        report['cases']=sum(g['cases'] for g in report['groups'])
        report['visited_pcs']=sorted({pc for g in report['groups'] for pc in g['observation']['visited']})
        report['new_instruction_addresses_visited']=len([pc for pc in report['visited_pcs'] if any(r['start']<=pc<r['end_exclusive'] for r in metadata['regions'] if r['execution_compared'])])
        if report['new_instruction_addresses_visited']!=sum(r['instruction_count'] for r in metadata['regions']):
            raise ValueError('airborne instruction coverage incomplete')
        report['ok']=True
    except (OSError,ValueError,subprocess.SubprocessError) as e:report['error']=str(e)
    finally:
        try:verify_expected(inspect_file());report['rom_unchanged']=True
        except (OSError,ValueError) as e:report.update(ok=False,error=str(e),rom_unchanged=False)
        atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'ok':report['ok'],'cases':report.get('cases'),'report':str(out/'report.json'),'error':report.get('error')},indent=2))
    return int(not report['ok'])
