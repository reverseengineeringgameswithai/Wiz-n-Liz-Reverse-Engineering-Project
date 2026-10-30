"""Bounded level-banner request/scratch comparison; original rendering calls use a write sink."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write
from movement_probe import validate, closed_graph
from rnc_loader_probe import parse_disassembly, require
from native_build import PRESETS, verify_executable
from build_terrain_reference import verify_executable as reference_executable, REPORT


def cases():
    # Every row and stage word, with difficulty distributed across the sweep.
    for v in range(65536):yield (v%4,v,(73*v)&65535,v^0xa55a,v^0x5aa5)
    # All difficulties, final-stage sides, number wrap and signed row shifts.
    for difficulty in range(4):
        for stage in (0,1,6,7,8,14,15,16,30,31,32,54,55,56,98,99,100,32767,32768,65534,65535):
            for row in (0,1,6,31,63,64,255,256,257,511,512,513,32767,32768,65534,65535):
                yield (difficulty,stage,row,0xbeef,0x1234)


def probe(data,meta,out):
    validate(data,meta);rows=[];commands=[]
    for region in meta['regions']:
        if 'instruction_count' not in region:continue
        lo,hi=region['start'],region['end_exclusive']
        cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        decoded=parse_disassembly(p.stdout,data,lo,hi);require(len(decoded)==region['instruction_count'],'banner decode count differs')
        rows.extend(decoded);commands.append(dict(argv=cmd,stdout=p.stdout,stderr=p.stderr))
    graph=closed_graph(data,rows)
    for pc,size,mnemonic in ((0x63f4,2,'lslw'),(0x63f6,4,'lea'),(0x640c,2,'bne'),(0x6444,2,'addqw')):
        cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        row,=parse_disassembly(p.stdout,data,pc,pc+size);require(row['assembly'].split()[0].startswith(mnemonic),'banner GNU check differs')
        commands.append(dict(argv=cmd,stdout=p.stdout,stderr=p.stderr))
    atomic_write(out/'static.json',(json.dumps(dict(rows=rows,graph=graph,commands=commands,gnu_checks=4,limitation='GNU plugin ignores CPU selection.'),indent=2)+'\n').encode())
    return [r['address'] for r in rows]


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);meta=json.loads((ROOT/'re/level_banner.json').read_text())
    native=verify_executable(args.preset,'wiznliz-session');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/banner-comparison')))
    report=dict(ok=False,preset=args.preset,rom_sha256=identity['sha256'],scope=meta['contract'],
                native_build=json.loads((native.parent/'provenance.json').read_text()),reference_build=json.loads(REPORT.read_text()),
                sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/banner_compare.py','re/level_banner.json')})
    try:
        pcs=probe(DEFAULT_ROM.read_bytes(),meta,out);corpus=list(cases());data=''.join(' '.join(map(str,c))+'\n' for c in corpus).encode()
        atomic_write(out/'cases.in',data);outputs=[]
        for name,cmd in [('native',[str(native),'--banner']),('reference',[str(reference),str(DEFAULT_ROM),'--banner'])]:
            r=subprocess.run(cmd,input=data,capture_output=True,timeout=180)
            atomic_write(out/(name+'.stdout'),r.stdout);atomic_write(out/(name+'.stderr'),r.stderr)
            require(r.returncode==0,name+' failed: '+r.stderr.decode());rows=[tuple(map(int,line.split())) for line in r.stdout.splitlines()]
            require(len(rows)==len(corpus) and all(len(row)==7 for row in rows),'banner output extent differs');outputs.append(rows)
            report[name+'_command']=cmd
        require(outputs[0]==outputs[1],'banner original/native mismatch')
        observation=json.loads((out/'reference.stderr').read_text());require(observation['visited']==pcs and observation['cases']==len(corpus),'banner instruction coverage differs')
        report.update(ok=True,cases=len(corpus),observation=observation,native_instructions=25,reference_only_callee_instructions=46,
                      output_sha256=hashlib.sha256((out/'native.stdout').read_bytes()).hexdigest())
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True
        atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:report.get(k) for k in ('ok','cases','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
