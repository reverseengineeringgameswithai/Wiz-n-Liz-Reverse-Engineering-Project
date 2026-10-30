"""Original actor movement execution versus native state transitions; local only."""
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
from movement_probe import validate
from terrain_probe import validate as validate_terrain
from terrain_compare import reference_resources
from bank_atlas import catalog_entry,read_extracted,MAX_BANK_BYTES
from scene_preview import MAX_SCENE_BYTES

sys.path.insert(0,str(ROOT/'tests'))
from movement_cases import fixture,case,goldens,decode_results
from terrain_cases import encode_cases


def flat_cases():
    cases=[c for c,_ in goldens()]
    cases.extend(case(op=op,speed=v) for op in (3,4,5,6) for v in range(65536))
    cases.extend(case(op=3,speed=v,damping=d) for v in (0,1,193,32767,32768,0xff3f,65535) for d in (0,1,31,255,65535))
    # Signed limits are words, not validated positive/negative host integers.
    cases.extend(case(op=op,speed=v,positive=limit,negative=limit) for op in (5,6)
                 for v in (0,1,192,32767,32768,65535) for limit in (0,1,32767,32768,65535))
    return cases


def authored_cases():
    cases=[]
    for op in (0,1,2):
        for x in range(116,372):
            for y in range(105,113):
                cases.append(case(op=op,x=x,y=y,speed=64 if x%2 else 0xffc0))
    rng=random.Random(0x57495a)
    speeds=[0,1,31,32,33,191,192,193,255,0xffff,0xffe1,0xffe0,0xff3f,0xff40]
    for i in range(2048):
        cases.append(case(x=rng.randrange(65536),y=rng.randrange(105,265),speed=rng.choice(speeds),
                          sx=rng.randrange(65536),sy=rng.randrange(65536),repeats=1+i%4))
    return cases


def real_cases():
    # Keep vertical headroom for worst-case loss of contact; no unknown RAM reads.
    cases=[]
    for row in range(30):
        for column in range(128):
            for op in (0,1,2):
                x=116+column*8+(row%8);y=105+row*8+(column%8)
                cases.append(case(op=op,x=x,y=y,speed=64 if column%2 else 0xffc0))
    # Stateful sequences of calls; these are not claims about frame scheduling.
    for column in range(128):
        cases.append(case(x=116+column*8,y=169,speed=32,repeats=16))
        cases.append(case(x=116+column*8,y=169,speed=0xffe0,repeats=16))
    return cases


def compare_group(out,name,scene,bank,cases,base,native,reference,rom):
    directory=out/name;directory.mkdir();map_data,records=reference_resources(scene,bank,base)
    inputs={'scene.bin':scene,'bank.bin':bank,'map.bin':map_data,'records.bin':records,'cases.txt':encode_cases(cases)}
    for filename,data in inputs.items():atomic_write(directory/filename,data)
    result={'name':name,'base':base,'cases':len(cases),'inputs':{k:hashlib.sha256(v).hexdigest() for k,v in inputs.items()},'processes':{}}
    commands={'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),str(base),'--movement'],
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
        if observed!=actual:raise ValueError(f'movement mismatch {name} case {i} {cases[i]}: original={observed} native={actual}')
    if name=='flat':
        for i,(_,expected) in enumerate(goldens()):
            if rows['reference'][i]!=expected:raise ValueError(f'independent movement golden mismatch {i}')
        result['independent_goldens']=len(goldens())
    result['horizontal_steps']=sum(r[14] for r in rows['reference'])
    result['airborne_transitions']=sum(r[15] for r in rows['reference']);result['ok']=True
    atomic_write(directory/'report.json',(json.dumps(result,indent=2)+'\n').encode());return result


def check_rejections(out,native,reference,rom):
    directory=out/'flat'
    commands={'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),'0','--movement'],
              'native':[str(native),'comparison.scene',str(directory/'scene.bin'),'comparison.bank',str(directory/'bank.bin')]}
    results=[]
    for kind,command in commands.items():
        process=subprocess.run(command,input=encode_cases([case(y=361)]),capture_output=True,timeout=10)
        if process.returncode!=2 or process.stdout:raise ValueError('movement invalid address was not rejected')
        expected=b'outside declared fixture' if kind=='reference' else b'outside map resource'
        if expected not in process.stderr:raise ValueError('movement rejection had an unexpected cause')
        results.append({'kind':kind,'case':case(y=361),'command':command,'exit_status':process.returncode,'stderr':process.stderr.decode()})
    return results


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preset',choices=PRESETS,default='debug')
    parser.add_argument('--rom',action='store_true',help='Add cataloged terrain states; original routine ROM is always required')
    args=parser.parse_args(argv);identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes()
    metadata=json.loads((ROOT/'re/movement_step.json').read_text());validate(data,metadata)
    validate_terrain(data,json.loads((ROOT/'re/terrain_query.json').read_text()))
    native=verify_executable(args.preset,'wiznliz-movement');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/movement-comparison')))
    report={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
            'scope':'isolated motion state and explicit transition counts; no full controller, airborne update, frame timing or register/CCR ABI',
            'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REFERENCE_REPORT.read_text()),
            'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('tools/movement_compare.py','tools/movement_probe.py','tests/movement_cases.py','re/movement_step.json')}}
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
        report['ok']=True
    except (OSError,ValueError,subprocess.SubprocessError) as e:report['error']=str(e)
    finally:
        try:verify_expected(inspect_file());report['rom_unchanged']=True
        except (OSError,ValueError) as e:report.update(ok=False,error=str(e),rom_unchanged=False)
        atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'ok':report['ok'],'cases':report.get('cases'),'report':str(out/'report.json'),'error':report.get('error')},indent=2))
    return int(not report['ok'])
