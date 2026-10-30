"""Verify disjoint fast-reversal/allocation/release ranges and closed call graph."""
import argparse
import json
from pathlib import Path
import tempfile
import subprocess
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from movement_probe import validate
from presentation_probe import disassemble
from rnc_loader_probe import parse_disassembly,require


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--disassemble',action='store_true');args=p.parse_args(argv)
    verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/reversal_step.json').read_text())
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/reversal-probe')))
    report={'ok':False,'metadata':meta}
    try:
        report['static']=validate(data,meta)
        if args.disassemble:
            report['decoders']=disassemble(data,meta,out)
            commands=[]
            for pc,size,mnemonic in ((0xa7ec,4,'moveal'),(0xa9f0,4,'subqw'),(0xf99c,2,'tstl'),(0xfab0,2,'movel'),(0xa81c,2,'bmi')):
                command=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
                proc=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
                row,=parse_disassembly(proc.stdout,data,pc,pc+size)
                require(row['assembly'].split()[0].startswith(mnemonic),'GNU reversal check differs')
                commands.append({'command':command,'stdout':proc.stdout,'stderr':proc.stderr})
            atomic_write(out/'reversal-gnu.json',(json.dumps(commands,indent=2)+'\n').encode())
            report['decoders']['new_gnu_checks']=len(commands)
            report['decoders']['additional_gnu_limit']='Installed plugin misdecodes absolute MOVE.L opcode 23c8 at F9A0; this instruction is not GNU-corroborated.'
        report['ok']=True
    except Exception as e:report['error']=str(e)
    verify_expected(inspect_file());report['rom_unchanged']=True
    atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'ok':report['ok'],'report':str(out/'report.json'),'error':report.get('error')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
