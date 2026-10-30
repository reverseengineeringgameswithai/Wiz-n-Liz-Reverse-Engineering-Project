"""Pin the measured reversal service/slot walk and rendering bookkeeping context."""
import json
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory
from genesis_actor_capture import save, require
from movement_probe import validate
from rnc_loader_probe import parse_disassembly


def main(argv=None):
    import argparse
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes()
    meta=json.loads((ROOT/'re/effect_session.json').read_text())
    out=approved_directory(ROOT,'local/generated/effect-session-probe')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=out))
    report=dict(ok=False,metadata=meta)
    try:
        report['static']=validate(data,meta);commands=[];count=0
        for r in meta['regions']:
            lo,hi=r['start'],r['end_exclusive']
            cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=15,check=True)
            rows=parse_disassembly(p.stdout,data,lo,hi);require(len(rows)==r['instruction_count'],'context decode differs')
            count+=len(rows);commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
        for pc,size,mnemonic in ((0x69bc,4,'moveal'),(0x69c0,2,'jsr'),(0x69cc,2,'bne'),(0xb126,4,'clrw')):
            cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=15,check=True)
            row,=parse_disassembly(p.stdout,data,pc,pc+size)
            require(row['assembly'].split()[0].startswith(mnemonic),'GNU context decode differs')
            commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
        save(out/'decoders.json',commands)
        report.update(ok=True,context_instructions=count,gnu_checks=4,
                      scope='Static/observed context, not restricted original/native coverage or a closed general-world graph.')
    except Exception as e:report['error']=str(e)
    verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps(dict(ok=report['ok'],error=report.get('error'),report=str(out/'report.json')),indent=2))
    return int(not report['ok'])


if __name__=='__main__':raise SystemExit(main())
