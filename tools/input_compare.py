"""Exhaustive byte conversion against restricted original 14E4E execution."""
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


def probe(data, metadata, out):
    validate(data, metadata)
    region, = metadata['regions'];lo,hi=region['start'],region['end_exclusive']
    commands=[]
    cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
    p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
    rows=parse_disassembly(p.stdout,data,lo,hi)
    require(len(rows)==region['instruction_count'],'pad instruction count differs')
    graph=closed_graph(data,rows);require(graph['returns']==[0x14f22],'pad return differs')
    commands.append(dict(argv=cmd,stdout=p.stdout,stderr=p.stderr))
    for pc,size,mnemonic in ((0x14e66,2,'beq'),(0x14ecc,4,'sne'),(0x14f16,4,'moveb')):
        cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        row,=parse_disassembly(p.stdout,data,pc,pc+size)
        require(row['assembly'].split()[0].startswith(mnemonic),'pad GNU check differs')
        commands.append(dict(argv=cmd,stdout=p.stdout,stderr=p.stderr))
    cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s','0x14e58','-D',data[0x14e58:0x14e5e].hex()]
    p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
    commands.append(dict(argv=cmd,stdout=p.stdout,stderr=p.stderr))
    limitation='GNU plugin rejects immediate memory BTST at 14E58; primary decoder and original execution cover it. GNU plugin ignores CPU-model selection.'
    require('invalid' in p.stdout,'GNU limitation changed; review decoder evidence')
    atomic_write(out/'static.json',(json.dumps(dict(commands=commands,graph=graph,rows=rows,gnu_checks=3,limitation=limitation),indent=2)+'\n').encode())
    return [r['address'] for r in rows]


def decode(data):
    rows=[tuple(map(int,line.split())) for line in data.splitlines()]
    require(len(rows)==1024 and all(len(r)==12 and all(0<=v<=255 for v in r) for r in rows),'pad output shape differs')
    return rows


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);data=DEFAULT_ROM.read_bytes()
    meta=json.loads((ROOT/'re/input_conversion.json').read_text())
    native=verify_executable(args.preset,'wiznliz-session');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/input-comparison')))
    report={'ok':False,'preset':args.preset,'rom_sha256':identity['sha256'],'scope':meta['contract'],
            'native_build':json.loads((native.parent/'provenance.json').read_text()),'reference_build':json.loads(REPORT.read_text()),
            'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/input_compare.py','re/input_conversion.json')}}
    try:
        pcs=probe(data,meta,out);results={}
        for name,cmd,rows in [('native',[str(native),'--pad'],[v for v in range(256) for _ in range(4)]),
                             ('reference',[str(reference),str(DEFAULT_ROM),'--pad'],list(range(256)))]:
            inputs=''.join(f'{v}\n' for v in rows).encode();atomic_write(out/(name+'.in'),inputs)
            proc=subprocess.run(cmd,input=inputs,capture_output=True,timeout=30)
            atomic_write(out/(name+'.stdout'),proc.stdout);atomic_write(out/(name+'.stderr'),proc.stderr)
            require(proc.returncode==0,name+' conversion failed: '+proc.stderr.decode());results[name]=decode(proc.stdout)
            report[name+'_command']=cmd
        require(results['native']==results['reference'],'original/native input conversion mismatch')
        observation=json.loads((out/'reference.stderr').read_text())
        require(observation['visited']==pcs and observation['cases']==1024,'pad execution coverage differs')
        report.update(ok=True,cases=1024,raw_bytes=256,initial_reference_fills=[0,85,170,255],
                      observation=observation,output_sha256=hashlib.sha256((out/'reference.stdout').read_bytes()).hexdigest())
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True
        atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:report.get(k) for k in ('ok','cases','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
