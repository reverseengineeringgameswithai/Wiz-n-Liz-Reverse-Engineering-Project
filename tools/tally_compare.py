"""Original/native parity for bounded tally countdown, credit and Start completion."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import PRESETS,verify_executable
from build_terrain_reference import verify_executable as reference_executable,REPORT
from actor_compare import fixture,catalog_entry,read_extracted,MAX_BANK_BYTES,MAX_SCENE_BYTES
from actions_compare import compare
from tally_cases import case,decode,goldens,unsupported
from movement_probe import validate


def actor_cases():
    rows=[c for c,_ in goldens()]
    rows.extend(case(tally_countdown=v) for v in range(65536))
    rows.extend(case(credit=v,tally_countdown=65535) for v in range(65536))
    rows.extend(case(remaining=v,tally_countdown=65535) for v in range(65536))
    rows.extend(c for raw in range(256) for start in (0,1,255) for skip in (0,1,65535)
        for special in (0,1) for remaining in (0,1) for delay in (0,65535)
        if not unsupported(c:=case(raw=raw,start=start,skip=skip,special_gate=special,remaining=remaining,tally_countdown=delay)))
    rows.extend(case(handler=h,speed=v,flags=f,tally_countdown=65535,remaining=1,repeats=n)
        for h in (24,25) for f in (0,0x800) for v in (0,1,31,32,192,32767,32768,32769,65504,65535) for n in (1,2,5,16))
    rows.extend(case(handler=25,palette_gate=v,mode=mode) for v in (0,1,32768,65535) for mode in range(256))
    return rows


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug')
    p.add_argument('--rom',action='store_true',help='Add cataloged terrain; original code ROM always required');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/tally_step.json').read_text());validate(data,meta)
    native=verify_executable(args.preset,'wiznliz-actor');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/tally-comparison')))
    r={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'groups':[],
       'scope':meta['contract'],'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REPORT.read_text()),
       'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/tally_compare.py','tests/tally_cases.py','re/tally_step.json')}}
    try:
        rom=out/'rom.bin';atomic_write(rom,data);scene,bank=fixture(True)
        for name,mode,rows,expected in (('actor-flat','--tally',actor_cases(),goldens()),):
            r['groups'].append(compare(out,name,mode,scene,bank,rows,0,native,reference,rom,expected,decode))
        rows=[case(handler=h,speed=v,x=x,y=y,direction=d) for h in (24,25) for d in (0,1) for v in (0,1,32,192,65504,65344)
              for x in range(116,372,4) for y in (105,109,113)]
        scene,bank=fixture(False);r['groups'].append(compare(out,'authored-terrain','--tally',scene,bank,rows,257,native,reference,rom,decoder=decode))
        if args.rom:
            entry=catalog_entry('scene.companion.0001','companion_scene_v1');base=catalog_entry(entry['structure']['base_bank_id'])
            _,scene=read_extracted(entry,MAX_SCENE_BYTES);_,bank=read_extracted(base,MAX_BANK_BYTES)
            rows=[case(handler=h,speed=v,x=116+col*8,y=105+row*8,direction=d)
                  for row in range(28) for col in range(0,128,4) for h in (24,25) for d in (0,1) for v in (0,32,65504)]
            r['groups'].append(compare(out,'cataloged-terrain','--tally',scene,bank,rows,257,native,reference,rom,decoder=decode))
        r['cases']=sum(g['cases'] for g in r['groups']);r['visited_pcs']=sorted({pc for g in r['groups'] for pc in g['observation']['visited']})
        r['new_instructions_visited']=sum(any(a['start']<=pc<a['end_exclusive'] for a in meta['regions']) for pc in r['visited_pcs'])
        if r['new_instructions_visited']!=sum(a['instruction_count'] for a in meta['regions']):raise ValueError('new instruction coverage incomplete')
        r['ok']=True
    except Exception as e:r['error']=str(e)
    finally:
        verify_expected(inspect_file());r['rom_unchanged']=True;atomic_write(out/'report.json',(json.dumps(r,indent=2)+'\n').encode())
    print(json.dumps({k:r.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not r['ok'])

if __name__=='__main__':raise SystemExit(main())
