"""Original actor execution versus native motion and continuation boundaries; local only."""
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
from movement_probe import validate as validate_movement
from terrain_probe import validate as validate_terrain
from terrain_compare import reference_resources
from bank_atlas import catalog_entry,read_extracted,MAX_BANK_BYTES
from scene_preview import MAX_SCENE_BYTES

sys.path.insert(0,str(ROOT/'tests'))
from actor_cases import fixture,case,goldens,decode_results
from terrain_cases import encode_cases


def flat_cases():
    cases=[c for c,_ in goldens()]
    # All jump-delay words, including 8000->7FFF, and all impulse words.
    cases.extend(case(handler=13,jump=1,jump_delay=v) for v in range(65536))
    cases.extend(case(handler=13,jump=1,jump_delay=0,impulse=v,right=1) for v in range(65536))
    for handler in range(1,14):
        for speed in (0,1,4,31,32,64,96,144,145,148,149,192,193,32767,32768,0xff3f,0xff40,0xff6f,0xff70,65532,65535):
            for direction in (0,1,2,3):
                # Allocating fast reversal is deliberately outside this contract.
                if handler==5 and direction&1 or handler==6 and direction&2:continue
                for gate in (0,1):
                    for jump in (0,255):
                        cases.append(case(handler=handler,speed=speed,left=direction&1,right=direction&2,
                                          gate=gate,jump=jump,flags=0xa5a5))
    for handler in (3,4,9,10,11,12):
        for acceleration in (0,1,8,192,32767,32768,65535):
            for speed in (0,4,32767,32768,65535):
                for damping in (0,3,65535):
                    cases.append(case(handler=handler,speed=speed,ground_acc=acceleration,damping=damping,
                                      left=handler in (4,10,11),right=handler in (3,9,12)))
    # Word-coordinate wrap and above-map scratch, plus drop priority.
    for handler in (3,4,5,6,7,8):
        for x in (0,1,127,128,65535):
            for y in (0,105,109,110,65535):
                cases.append(case(handler=handler,x=x,y=y,drop=255,jump=255))
    return cases


def authored_cases():
    cases=[]
    for handler in range(1,14):
        for x in range(116,372,4):
            for y in (105,109,113):
                cases.append(case(handler=handler,x=x,y=y,speed=64 if x%8 else 0xffc0,
                                  jump=x%2,drop=(x//4)%2))
    rng=random.Random(0x414354)
    for i in range(2048):
        # Fixed held inputs across up to 16 invocations, preserving scratch and
        # all presentation words/callbacks. These invocations are not frames.
        cases.append(case(handler=rng.choice((1,2,7,8,9,10,11,12)),x=rng.randrange(65536),
                          y=rng.randrange(120,180),speed=rng.choice((0,1,32,64,65535,0xffe0)),
                          jump=rng.randrange(2),drop=rng.randrange(2),flags=rng.randrange(65536),
                          sx=rng.randrange(65536),sy=rng.randrange(65536),repeats=1+i%16))
    return cases


def real_cases():
    return [case(handler=handler,x=116+column*8,y=105+row*8,speed=64 if (column//4)%2 else 0xffc0,
                 flags=((column//4)%2)*0x800,jump=(column//8)%2,drop=(column//16)%2)
            for row in range(28) for column in range(0,128,4) for handler in range(1,14)]


def compare_group(out,name,scene,bank,cases,base,native,reference,rom,mode='--actor'):
    directory=out/name;directory.mkdir();map_data,records=reference_resources(scene,bank,base)
    inputs={'scene.bin':scene,'bank.bin':bank,'map.bin':map_data,'records.bin':records,'cases.txt':encode_cases(cases)}
    for filename,data in inputs.items():atomic_write(directory/filename,data)
    result={'name':name,'base':base,'cases':len(cases),'inputs':{k:hashlib.sha256(v).hexdigest() for k,v in inputs.items()},'processes':{}}
    commands={'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),str(base),mode],
              'native':[str(native),'comparison.scene',str(directory/'scene.bin'),'comparison.bank',str(directory/'bank.bin')]}
    if mode!='--actor':commands['native'].append(mode)
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
        if observed!=actual:raise ValueError(f'actor mismatch {name} case {i} {cases[i]}: original={observed} native={actual}')
    if name=='flat':
        for i,(_,expected) in enumerate(goldens()):
            if rows['reference'][i]!=expected:raise ValueError(f'independent actor golden mismatch {i}')
        result['independent_goldens']=len(goldens())
    result['horizontal_steps']=sum(r[18] for r in rows['reference'])
    result['settle_calls']=sum(r[19] for r in rows['reference'])
    result['landings']=sum(r[20] for r in rows['reference'])
    result['entry_calls']=sum(r[22] for r in rows['reference'])
    result['sound_requests']=sum(r[21] for r in rows['reference']);result['ok']=True
    atomic_write(directory/'report.json',(json.dumps(result,indent=2)+'\n').encode());return result


def check_rejections(out,native,reference,rom):
    directory=out/'flat'
    commands={'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),'0','--actor'],
              'native':[str(native),'comparison.scene',str(directory/'scene.bin'),'comparison.bank',str(directory/'bank.bin')]}
    results=[]
    # Down is now implemented and compared by actions-compare. This older
    # transport omits shared action globals, so Up still rejects explicitly;
    # its reference mode retains the historical code allowlist.
    for c in (case(y=361),case(up=1),case(handler=5,left=1),case(handler=6,right=1)):
        for kind,command in commands.items():
            process=subprocess.run(command,input=encode_cases([c]),capture_output=True,timeout=10)
            if process.returncode!=2 or process.stdout:raise ValueError('actor unsupported case was not rejected')
            if kind=='reference':
                boundary=0x9c56 if c[27] else 0xa7a8 if c[0]==5 else 0xa96e
                expected=b'outside declared fixture' if c[2]==361 else f'unsupported code boundary {boundary:06x}'.encode()
            else:expected=b'outside map resource' if c[2]==361 else b'up action requires shared action globals' if c[27] else b'unsupported'
            if expected not in process.stderr:raise ValueError('actor rejection had an unexpected cause: '+process.stderr.decode())
            results.append({'kind':kind,'case':c,'command':command,'exit_status':process.returncode,'stderr':process.stderr.decode()})
    return results


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preset',choices=PRESETS,default='debug')
    parser.add_argument('--rom',action='store_true',help='Add cataloged terrain states; original routine ROM is always required')
    args=parser.parse_args(argv);identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes()
    metadata=json.loads((ROOT/'re/actor_update.json').read_text());validate(data,metadata)
    validate_terrain(data,json.loads((ROOT/'re/terrain_query.json').read_text()))
    validate_movement(data,json.loads((ROOT/'re/movement_step.json').read_text()))
    validate_movement(data,json.loads((ROOT/'re/airborne_update.json').read_text()))
    native=verify_executable(args.preset,'wiznliz-actor');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/actor-comparison')))
    report={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
            'scope':'complete selected actor invocation and ordered sound requests; sound selector 0 mismatch in reference; no audio driver, presentation scheduling, allocations, frame timing or register/CCR ABI',
            'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REFERENCE_REPORT.read_text()),
            'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('tools/actor_compare.py','tools/actor_probe.py','tests/actor_cases.py','re/actor_update.json','tools/movement_probe.py','re/movement_step.json','re/terrain_query.json','re/airborne_update.json')}}
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
            raise ValueError('actor instruction coverage incomplete')
        report['ok']=True
    except (OSError,ValueError,subprocess.SubprocessError) as e:report['error']=str(e)
    finally:
        try:verify_expected(inspect_file());report['rom_unchanged']=True
        except (OSError,ValueError) as e:report.update(ok=False,error=str(e),rom_unchanged=False)
        atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'ok':report['ok'],'cases':report.get('cases'),'report':str(out/'report.json'),'error':report.get('error')},indent=2))
    return int(not report['ok'])
