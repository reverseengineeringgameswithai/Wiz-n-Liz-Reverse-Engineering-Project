"""Pinned animation scheduler and callback boundaries, including indirect tails."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from movement_probe import validate,transfer
from rnc_loader_probe import parse_disassembly,require
from reset_probe import word


def disassemble(data,metadata,out):
    regions=metadata['regions'][:]
    for name in metadata.get('dependencies',('terrain_query','movement_step','airborne_update','actor_update')):
        dependency=json.loads((ROOT/f're/{name}.json').read_text())
        regions.extend(r for r in dependency['regions'] if r['execution_compared'])
    rows=[];commands=[]
    for cpu,expected in (('68000','invalid'),('68020','extb.l')):
        argv=['rasm2','-a','m68k','-b','32','-e','-c',cpu,'-D','49c0']
        p=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=True)
        require(expected in p.stdout,'CPU sentinel mismatch');commands.append(dict(argv=argv,stdout=p.stdout,stderr=p.stderr))
    for r in regions:
        lo,hi=r['start'],r['end_exclusive']
        argv=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=True)
        decoded=parse_disassembly(p.stdout,data,lo,hi);require(len(decoded)==r['instruction_count'],'instruction count differs')
        rows.extend(decoded);commands.append(dict(argv=argv,stdout=p.stdout,stderr=p.stderr))
    addresses={r['address'] for r in rows};edges=[]
    exits=set(metadata['rejected_boundaries']+metadata['stop_boundaries'])
    indirect={v['pc']:v for v in metadata['indirect_transfers']}
    require(not addresses.intersection(exits),'executable stop/unsupported boundary')
    for row in rows:
        pc=row['address'];op=word(data,pc)
        if op==0x4e75:continue
        targets=[pc+row['size']];target=transfer(data,pc)
        if pc in indirect:
            require(op==indirect[pc]['opcode'],'indirect opcode differs')
            if op==0x4ed0:targets=[]
            targets+=indirect[pc]['targets']
        elif target is not None:
            if op&0xff00==0x6000 or op in (0x4ef9,0x4efa):targets=[]
            targets.append(target)
        else:require(not 0x4e80<=op<=0x4eff,'unmodeled indirect transfer')
        for target in targets:
            require(target in addresses or target in exits,'graph escaped instruction boundary')
            edges.append([pc,target])
    # The installed GNU plugin rejects immediate BCHG 086e. Retain that decoder
    # limitation; mode/bounce semantics are independently executed by Musashi.
    for pc,size,mnemonic in ((0xf774,4,'subqb'),(0xf79e,4,'addqw'),
                             (0xf84e,2,'jmp'),(0xf8fa,2,'bpl'),(0xa774,4,'subqw')):
        argv=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
        p=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=True)
        row,=parse_disassembly(p.stdout,data,pc,pc+size)
        require(row['assembly'].split()[0].startswith(mnemonic),'independent decoder mismatch')
        commands.append(dict(argv=argv,stdout=p.stdout,stderr=p.stderr))
    result={'commands':commands,'edges':edges,'instructions':len(addresses),'gnu_checks':5,
            'gnu_limit':'installed m68k.gnu rejects immediate BCHG 086e; not claimed as corroborated by this decoder',
            'new_instructions':sum(r['instruction_count'] for r in metadata['regions'])}
    atomic_write(out/'decoder-evidence.json',(json.dumps(result,indent=2)+'\n').encode())
    return {k:v for k,v in result.items() if k not in ('commands','edges')}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--disassemble',action='store_true');args=p.parse_args(argv)
    verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes();meta=json.loads((ROOT/'re/presentation_step.json').read_text())
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/presentation-probe')))
    report={'ok':False}
    try:
        report['static']=validate(data,meta)
        if args.disassemble:report['decoders']=disassemble(data,meta,out)
        report['ok']=True
    except (OSError,ValueError,subprocess.SubprocessError) as e:report['error']=str(e)
    verify_expected(inspect_file());report['rom_unchanged']=True
    atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])
