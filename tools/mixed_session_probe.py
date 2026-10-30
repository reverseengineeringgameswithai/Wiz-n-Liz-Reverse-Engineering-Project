"""Exact static boundaries for omitted private objects in the mixed pool capture."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory
from genesis_actor_capture import save,require
from movement_probe import validate,transfer
from rnc_loader_probe import parse_disassembly


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv);verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/mixed_session.json').read_text())
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/mixed-session-probe')));report=dict(ok=False,metadata=meta)
    try:
        report['static']=validate(data,meta);commands=[];rows=[]
        import hashlib
        for r in meta['data']:require(hashlib.sha256(data[r['start']:r['end_exclusive']]).hexdigest()==r['sha256'],'private table differs')
        for r in meta['regions']:
            lo,hi=r['start'],r['end_exclusive'];cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
            p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15);decoded=parse_disassembly(p.stdout,data,lo,hi)
            require(len(decoded)==r['instruction_count'],'private context instruction count differs');rows+=decoded;commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
        addresses={r['address'] for r in rows};edges=[]
        for r in rows:
            pc=r['address'];op=int.from_bytes(data[pc:pc+2],'big')
            if op==0x4e75:continue
            targets=[pc+r['size']];t=transfer(data,pc)
            if t is not None:
                if op&0xff00==0x6000:targets=[]
                targets.append(t)
            require(not (0x4e80<=op<=0x4eff and t is None),'unresolved private indirect transfer')
            for t in targets:require(t in addresses or t==0x7910,'private audit escaped declared boundary');edges.append([pc,t])
        for pc,size,mnemonic in ((0x7808,4,'moveal'),(0x7820,4,'subqw'),(0x7aa0,4,'addw'),(0x7ac6,4,'negw'),(0xac94,2,'rts')):
            cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
            p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15);row,=parse_disassembly(p.stdout,data,pc,pc+size)
            require(row['assembly'].split()[0].startswith(mnemonic),'private GNU check differs');commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
        save(out/'decoders.json',commands);report.update(ok=True,context_instructions=len(rows),context_code_bytes=sum(r['end_exclusive']-r['start'] for r in meta['regions']),context_data_bytes=48,gnu_checks=5,edges=edges,unsupported_exit='0x7910',scope=meta['contract'])
    except Exception as e:report['error']=str(e)
    verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps(dict(ok=report['ok'],error=report.get('error'),report=str(out/'report.json')),indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
