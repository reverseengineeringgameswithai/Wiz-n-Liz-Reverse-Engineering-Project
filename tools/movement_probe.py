"""Pinned movement/control-state dataflow and closed executable call graph."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from rnc_loader_probe import require,direct_target,parse_disassembly
from reset_probe import word,branch_target,dbf_target
from terrain_probe import validate as validate_terrain


def transfer(data,pc):
    target=direct_target(data,pc);op=word(data,pc)
    if target is None and op&0xf000==0x6000:target=branch_target(data,pc)
    if target is None and op&0xf0f8==0x50c8:target=dbf_target(data,pc)[1]
    return target


def validate(data,metadata):
    require(metadata['schema_version']==1 and metadata['address_space']=='rom_file_offset','movement schema mismatch')
    require(hashlib.sha256(data).hexdigest()==metadata['rom_sha256'],'movement ROM identity mismatch')
    for region in metadata['regions']:
        lo,hi=region['start'],region['end_exclusive']
        require(0<=lo<hi<=len(data) and hashlib.sha256(data[lo:hi]).hexdigest()==region['sha256'],'movement region differs')
    for row in metadata['transfers']:require(transfer(data,row['pc'])==row['target'],'movement transfer differs')
    return {'regions':len(metadata['regions']),'transfers':len(metadata['transfers'])}


def closed_graph(data,rows,continuations=()):
    addresses={row['address'] for row in rows};edges=[];returns=[];exits=[]
    require(not addresses.intersection(continuations),'continuation overlaps executable graph')
    for row in rows:
        pc=row['address'];op=word(data,pc)
        if op==0x4e75:returns.append(pc);continue
        successors=[pc+row['size']];target=transfer(data,pc)
        if target is not None:
            if op&0xff00==0x6000 or op in (0x4ef9,0x4efa):successors=[]
            successors.append(target)
        else:require(not 0x4e80<=op<=0x4eff,'unmodeled indirect movement transfer')
        for destination in successors:
            require(destination in addresses or destination in continuations,'movement code escapes declared graph/instruction boundary')
            if destination in continuations:exits.append([pc,destination])
            edges.append([pc,destination])
    return {'instructions':len(addresses),'edges':edges,'returns':returns,'continuations':exits}


def disassemble(data,metadata,out):
    terrain=json.loads((ROOT/'re/terrain_query.json').read_text());validate_terrain(data,terrain)
    commands=[];instructions={};executable=[]
    for region in metadata['regions']+[r for r in terrain['regions'] if r['execution_compared']]:
        lo,hi=region['start'],region['end_exclusive']
        command=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
        rows=parse_disassembly(p.stdout,data,lo,hi);require(len(rows)==region['instruction_count'],'movement decode count differs')
        commands.append({'argv':command,'stdout':p.stdout,'stderr':p.stderr,'exit_status':p.returncode})
        instructions[region['id']]=rows
        if region['execution_compared']:executable.extend(rows)
    graph=closed_graph(data,executable)
    checks=[(0x9ab8,2,'negw'),(0x9aba,2,'asrw'),(0x9ac0,4,'dbf'),(0x9afe,4,'dbf'),(0x9a66,4,'dbf'),
            (0x9aec,4,'subqw'),(0x9b28,4,'addqw'),(0xacda,4,'cmpw'),(0xacec,4,'cmpw'),(0x9952,4,'moveal')]
    for pc,size,mnemonic in checks:
        command=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
        p=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
        row,=parse_disassembly(p.stdout,data,pc,pc+size);require(row['assembly'].split()[0]==mnemonic,'GNU movement corroboration failed')
        commands.append({'argv':command,'stdout':p.stdout,'stderr':p.stderr,'exit_status':p.returncode})
    result={'instructions':instructions,'graph':graph,'commands':commands,
            'version':subprocess.check_output(['rasm2','-v'],text=True,timeout=10).strip(),'gnu_checks':len(checks)}
    atomic_write(out/'decoder-evidence.json',(json.dumps(result,indent=2)+'\n').encode())
    return {'executed_scope_instructions':graph['instructions'],'new_scope_instructions':sum(r['instruction_count'] for r in metadata['regions'] if r['execution_compared']),
            'static_context_instructions':sum(r['instruction_count'] for r in metadata['regions'] if not r['execution_compared']),'gnu_checks':len(checks)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--disassemble',action='store_true');args=parser.parse_args(argv)
    verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes();metadata=json.loads((ROOT/'re/movement_step.json').read_text())
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/movement-probe')))
    report={'ok':False,'metadata':metadata}
    try:
        report['static']=validate(data,metadata)
        if args.disassemble:report['decoders']=disassemble(data,metadata,out)
        report['ok']=True
    except (OSError,ValueError,subprocess.SubprocessError) as e:report['error']=str(e)
    finally:
        try:verify_expected(inspect_file());report['rom_unchanged']=True
        except (OSError,ValueError) as e:report.update(ok=False,error=str(e),rom_unchanged=False)
        atomic_write(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({'ok':report['ok'],'report':str(out/'report.json'),'error':report.get('error')},indent=2));return int(not report['ok'])
