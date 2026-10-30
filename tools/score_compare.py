"""Original/native secondary tally, packed-decimal score and bounded reward thresholds."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
from terrain_compare import reference_resources
from terrain_cases import encode_cases
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import PRESETS,verify_executable
from build_terrain_reference import verify_executable as reference_executable,REPORT
from actor_compare import fixture,catalog_entry,read_extracted,MAX_BANK_BYTES,MAX_SCENE_BYTES
from actions_compare import compare
from score_cases import case,decode,goldens
from movement_probe import validate


def actor_cases():
    from score_cases import packed
    rows=[c for c,_ in goldens()]
    rows.extend(case(tally_countdown=v) for v in range(65536))
    rows.extend(case(secondary_remaining=v) for v in range(65536))
    rows.extend(case(score=0x10000,rewards=v) for v in range(65536))
    rows.extend(case(score=packed(v*10000+9999),threshold=0x99999999) for v in range(10000))
    rows.extend(case(score=packed(v),threshold=0x99999999) for v in range(10000))
    rows.extend(case(score=packed(v*1000),threshold=0,increment=0x1000000) for v in range(65536))
    rows.extend(case(score=packed(v*1000),threshold=packed(v*1000+10000+d),increment=0x20000)
                for v in range(10000) for d in (-1,0,1))
    rows.extend(case(remaining=p,secondary_gate=g,secondary_remaining=n,skip=skip,start=start,tally_countdown=timer,handler=h)
                for p in (0,1) for g in (0,1,65535) for n in (0,1,65535) for skip in (0,1,65535)
                for start in (0,1,255) for timer in (0,32767,32768,65535) for h in (27,28))
    rows.extend(case(speed=s,flags=f,repeats=n,secondary_remaining=1,start=start)
                for s in (0,1,192,32767,32768,65535) for f in (0,0x800) for n in (1,2,5,16) for start in (0,255))
    return rows


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug')
    p.add_argument('--rom',action='store_true',help='Add cataloged terrain; original code ROM always required');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/score_step.json').read_text());validate(data,meta)
    native=verify_executable(args.preset,'wiznliz-actor');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/score-comparison')))
    r={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
       'scope':meta['contract'],'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REPORT.read_text()),
       'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/score_compare.py','tests/score_cases.py','re/score_step.json')}}
    try:
        rom=out/'rom.bin';atomic_write(rom,data);scene,bank=fixture(True)
        for name,mode,rows,expected in (('actor-flat','--score',actor_cases(),goldens()),):
            r['groups'].append(compare(out,name,mode,scene,bank,rows,0,native,reference,rom,expected,decode))
        rows=[case(handler=h,speed=v,x=x,y=y,direction=d,score=0x10000) for h in (27,28) for d in (0,1) for v in (0,1,32,192,65504,65344)
              for x in range(116,372,4) for y in (105,109,113)]
        scene,bank=fixture(False);r['groups'].append(compare(out,'authored-terrain','--score',scene,bank,rows,257,native,reference,rom,decoder=decode))
        if args.rom:
            entry=catalog_entry('scene.companion.0001','companion_scene_v1');base=catalog_entry(entry['structure']['base_bank_id'])
            _,scene=read_extracted(entry,MAX_SCENE_BYTES);_,bank=read_extracted(base,MAX_BANK_BYTES)
            rows=[case(handler=h,speed=v,x=116+col*8,y=105+row*8,direction=d,score=0x10000)
                  for row in range(28) for col in range(0,128,4) for h in (27,28) for d in (0,1) for v in (0,32,65504)]
            r['groups'].append(compare(out,'cataloged-terrain','--score',scene,bank,rows,257,native,reference,rom,decoder=decode))
        directory=out/'rejected-score';directory.mkdir();scene,bank=fixture(True);map_data,records=reference_resources(scene,bank,0)
        for name,contents in [('scene.bin',scene),('bank.bin',bank),('map.bin',map_data),('records.bin',records)]:atomic_write(directory/name,contents)
        commands={'native':[str(native),'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin'),'--score'],
                  'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),'0','--score']}
        r['expected_rejections']=[]
        negatives=[('invalid-score',case(score=0xa)),('invalid-threshold',case(threshold=0xa)),
                   ('invalid-increment',case(threshold=0,increment=0xa)),('zero-increment',case(threshold=0,increment=0)),
                   ('threshold-cycle',case(score=0x89990000,threshold=0,increment=0x50000000))]
        for name,row in negatives:
            for kind,command in commands.items():
                proc=subprocess.run(command,input=encode_cases([row]),capture_output=True,timeout=20)
                atomic_write(directory/(name+'-'+kind+'.stderr'),proc.stderr)
                if proc.returncode!=2 or proc.stdout:raise ValueError('score path did not reject atomically')
                expected=b'digit' if name.startswith('invalid') else b'budget'
                if expected not in proc.stderr:raise ValueError('wrong score rejection')
                r['expected_rejections'].append(dict(name=name,kind=kind,exit_status=proc.returncode,error=proc.stderr.decode().strip()))
        r['cases']=sum(g['cases'] for g in r['groups']);r['visited_pcs']=sorted({pc for g in r['groups'] for pc in g['observation']['visited']})
        r['new_instructions_visited']=sum(any(a['start']<=pc<a['end_exclusive'] for a in meta['regions']) for pc in r['visited_pcs'])
        if r['new_instructions_visited']!=sum(a['instruction_count'] for a in meta['regions'] if a['execution_compared']):raise ValueError('new instruction coverage incomplete')
        r['ok']=True
    except Exception as e:r['error']=str(e)
    finally:
        verify_expected(inspect_file());r['rom_unchanged']=True;atomic_write(out/'report.json',(json.dumps(r,indent=2)+'\n').encode())
    print(json.dumps({k:r.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not r['ok'])

if __name__=='__main__':raise SystemExit(main())
