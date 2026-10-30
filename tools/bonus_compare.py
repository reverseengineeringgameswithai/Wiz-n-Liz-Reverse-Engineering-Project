"""Original/native bonus slot selection, partial success and bounded failure parity."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import itertools
import subprocess
from terrain_compare import reference_resources
from terrain_cases import encode_cases
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import PRESETS,verify_executable
from build_terrain_reference import verify_executable as reference_executable,REPORT
from actor_compare import fixture,catalog_entry,read_extracted,MAX_BANK_BYTES,MAX_SCENE_BYTES
from actions_compare import compare
from bonus_cases import case,decode,goldens,ASSIGNED,CHOICES
from movement_probe import validate


def actor_cases():
    rows=[c for c,_ in goldens()]
    rows.extend(case(cursor=v) for v in range(65536))
    rows.extend(case(choices=(v,)*11) for v in range(65536))
    rows.extend(case(assigned=(*prefix,65535,0,0,0,0,0),cursor=cursor)
        for prefix in itertools.product((0,1,65535),repeat=5) for cursor in (0,1,5,6,32768,65535))
    rows.extend(case(count=count,cursor=cursor,assigned=(*(0 for _ in range(count-1)),65535,*(0 for _ in range(11-count))))
        for count in range(1,12) for cursor in (0,1,count-1,count,count+1,3853,3854,32767,32768,65535))
    rows.extend(case(handler=h,raw=raw,start=start,skip=skip,special_gate=special,flags=f)
        for h in (24,25) for raw in range(256) for start in (0,1,255) for skip in (0,1)
        for special in (0,1) for f in (0,0x800))
    rows.extend(case(handler=h,speed=v,flags=f,repeats=n) for h in (24,25) for f in (0,0x800)
        for v in (0,1,31,32,192,32767,32768,32769,65504,65535) for n in (1,2,16))
    rows.extend(case(mode=mode) for mode in range(256))
    return rows


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug')
    p.add_argument('--rom',action='store_true',help='Add cataloged terrain; original code ROM always required');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/bonus_step.json').read_text());validate(data,meta)
    native=verify_executable(args.preset,'wiznliz-actor');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/bonus-comparison')))
    r={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
       'scope':meta['contract'],'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REPORT.read_text()),
       'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/bonus_compare.py','tests/bonus_cases.py','re/bonus_step.json')}}
    try:
        rom=out/'rom.bin';atomic_write(rom,data);scene,bank=fixture(True)
        for name,mode,rows,expected in (('actor-flat','--bonus',actor_cases(),goldens()),):
            r['groups'].append(compare(out,name,mode,scene,bank,rows,0,native,reference,rom,expected,decode))
        rows=[case(handler=h,speed=v,x=x,y=y,direction=d) for h in (24,25) for d in (0,1) for v in (0,1,32,192,65504,65344)
              for x in range(116,372,4) for y in (105,109,113)]
        scene,bank=fixture(False);r['groups'].append(compare(out,'authored-terrain','--bonus',scene,bank,rows,257,native,reference,rom,decoder=decode))
        if args.rom:
            entry=catalog_entry('scene.companion.0001','companion_scene_v1');base=catalog_entry(entry['structure']['base_bank_id'])
            _,scene=read_extracted(entry,MAX_SCENE_BYTES);_,bank=read_extracted(base,MAX_BANK_BYTES)
            rows=[case(handler=h,speed=v,x=116+col*8,y=105+row*8,direction=d)
                  for row in range(28) for col in range(0,128,4) for h in (24,25) for d in (0,1) for v in (0,32,65504)]
            r['groups'].append(compare(out,'cataloged-terrain','--bonus',scene,bank,rows,257,native,reference,rom,decoder=decode))
        # Both transports reject malformed or nonterminating logical tables before publishing output.
        failed=[];directory=out/'rejections';directory.mkdir();scene,bank=fixture(True);map_data,records=reference_resources(scene,bank,0)
        for name,contents in [('scene.bin',scene),('bank.bin',bank),('map.bin',map_data),('records.bin',records)]:atomic_write(directory/name,contents)
        commands={'native':[str(native),'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin'),'--bonus'],
                  'reference':[str(reference),str(rom),str(directory/'map.bin'),str(directory/'records.bin'),'0','--bonus']}
        for label,c in [('zero-divisor',case(count=0)),('outside-extent',case(count=12)),('missing-terminator',case(assigned=(1,)*11)),('nontermination',case(count=1,assigned=(1,0,65535)+(0,)*8))]:
            for kind,command in commands.items():
                proc=subprocess.run(command,input=encode_cases([c]),capture_output=True,timeout=20)
                atomic_write(directory/(label+'-'+kind+'.stderr'),proc.stderr)
                if proc.returncode!=2 or proc.stdout:raise ValueError(label+' did not reject atomically in '+kind)
                failed.append(dict(case=label,kind=kind,exit_status=proc.returncode,error=proc.stderr.decode().strip()))
        r['expected_rejections']=failed
        r['cases']=sum(g['cases'] for g in r['groups']);r['visited_pcs']=sorted({pc for g in r['groups'] for pc in g['observation']['visited']})
        r['new_instructions_visited']=sum(any(a['start']<=pc<a['end_exclusive'] for a in meta['regions']) for pc in r['visited_pcs'])
        if r['new_instructions_visited']!=sum(a['instruction_count'] for a in meta['regions']):raise ValueError('new instruction coverage incomplete')
        r['ok']=True
    except Exception as e:r['error']=str(e)
    finally:
        verify_expected(inspect_file());r['rom_unchanged']=True;atomic_write(out/'report.json',(json.dumps(r,indent=2)+'\n').encode())
    print(json.dumps({k:r.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not r['ok'])

if __name__=='__main__':raise SystemExit(main())
