"""Pinned actor instruction ranges, transfer checks and explicit rejected exits."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from movement_probe import validate,closed_graph
from terrain_probe import validate as validate_terrain
from rnc_loader_probe import parse_disassembly,require


def disassemble(data,metadata,out):
    regions=metadata['regions'][:]
    for name in ('terrain_query','movement_step','airborne_update'):
        dependency=json.loads((ROOT/f're/{name}.json').read_text())
        (validate_terrain if name=='terrain_query' else validate)(data,dependency)
        regions.extend(r for r in dependency['regions'] if r['execution_compared'])
    rows=[];commands=[]
    for cpu,expected in (('68000','invalid'),('68020','extb.l')):
        argv=['rasm2','-a','m68k','-b','32','-e','-c',cpu,'-D','49c0']
        p=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=True)
        require(expected in p.stdout,'actor decoder CPU sentinel failed')
        commands.append(dict(argv=argv,stdout=p.stdout,stderr=p.stderr,exit_status=p.returncode))
    for region in regions:
        lo,hi=region['start'],region['end_exclusive']
        argv=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=True)
        decoded=parse_disassembly(p.stdout,data,lo,hi)
        require(len(decoded)==region['instruction_count'],'actor instruction count differs')
        rows.extend(decoded);commands.append(dict(argv=argv,stdout=p.stdout,stderr=p.stderr,exit_status=p.returncode))
    graph=closed_graph(data,rows,metadata['rejected_boundaries'])
    # Independent GNU checks of stack discard, map-bit test, asymmetric control
    # branches and jump parameter loads. Bulk output remains ignored.
    for pc,size,mnemonic in ((0xa214,4,'btst'),(0xa21a,4,'lea'),(0xa43a,4,'addw'),(0xa578,4,'subw'),
                             (0xa54e,4,'bne'),(0xaae2,4,'movew'),(0xaae6,4,'movew')):
        argv=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
        p=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=True)
        decoded=parse_disassembly(p.stdout,data,pc,pc+size)
        require(decoded[0]['assembly'].split()[0].startswith(mnemonic),'GNU actor corroboration failed')
        commands.append(dict(argv=argv,stdout=p.stdout,stderr=p.stderr,exit_status=p.returncode))
    result={'graph':graph,'commands':commands,'new_instructions':sum(r['instruction_count'] for r in metadata['regions'])}
    atomic_write(out/'decoder-evidence.json',(json.dumps(result,indent=2)+'\n').encode());return result['new_instructions']


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--disassemble',action='store_true');args=parser.parse_args(argv)
    verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes();metadata=json.loads((ROOT/'re/actor_update.json').read_text())
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/actor-probe')))
    result={'ok':False,'metadata':metadata}
    try:
        result['static']=validate(data,metadata)
        if args.disassemble:result['instructions']=disassemble(data,metadata,out)
        result['ok']=True
    except (OSError,ValueError,subprocess.SubprocessError) as e:result['error']=str(e)
    verify_expected(inspect_file());result['rom_unchanged']=True
    atomic_write(out/'report.json',(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({'ok':result['ok'],'report':str(out/'report.json'),'error':result.get('error')},indent=2));return int(not result['ok'])
