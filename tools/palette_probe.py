"""Pin palette paths and explicit unsupported exits with a closed call graph."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from movement_probe import validate
from presentation_probe import disassemble
from rnc_loader_probe import parse_disassembly,require


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--disassemble',action='store_true');args=p.parse_args(argv)
    verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/palette_step.json').read_text())
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/palette-probe')))
    report={'ok':False,'metadata':meta,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        report['static']=validate(data,meta)
        if args.disassemble:
            report['decoders']=disassemble(data,meta,out);commands=[]
            for pc,size,mnemonic in ((0x51e0,4,'bne'),(0x13730,2,'moveb'),(0x137de,2,'addw'),(0x13292,2,'rts')):
                cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
                proc=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
                row,=parse_disassembly(proc.stdout,data,pc,pc+size)
                require(row['assembly'].split()[0].startswith(mnemonic),'GNU palette corroboration differs')
                commands.append({'command':cmd,'stdout':proc.stdout,'stderr':proc.stderr})
            atomic_write(out/'palette-gnu.json',(json.dumps(commands,indent=2)+'\n').encode());report['decoders']['new_gnu_checks']=len(commands)
            report['decoders']['new_gnu_limit']='No new decoder limitation; inherited presentation BCHG limitation remains.'
        report['ok']=True
    except Exception as e:report['error']=str(e)
    verify_expected(inspect_file());report['rom_unchanged']=True
    atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:report.get(k) for k in ('ok','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
