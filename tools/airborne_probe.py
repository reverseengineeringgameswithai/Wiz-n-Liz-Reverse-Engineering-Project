"""Pinned airborne execution ranges and explicit immediate-continuation boundaries."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from rom import ROOT,DEFAULT_ROM,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from rnc_loader_probe import require,parse_disassembly
from terrain_probe import validate as validate_terrain
from movement_probe import closed_graph,validate as validate_movement


def validate(data,metadata):
    result=validate_movement(data,metadata)
    require([r['pc'] for r in metadata.get('continuation_boundaries',[])]==[0xa1be,0xa246],
            'airborne continuation boundary changed')
    return result


def disassemble(data,metadata,out):
    terrain=json.loads((ROOT/'re/terrain_query.json').read_text());validate_terrain(data,terrain)
    movement=json.loads((ROOT/'re/movement_step.json').read_text());validate_movement(data,movement)
    commands=[];instructions={};executable=[]
    for cpu,expected in (('68000','invalid'),('68020','extb.l')):
        command=['rasm2','-a','m68k','-b','32','-e','-c',cpu,'-D','49c0']
        p=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
        require(expected in p.stdout,'airborne decoder CPU sentinel failed')
        commands.append({'argv':command,'stdout':p.stdout,'stderr':p.stderr,'exit_status':p.returncode})
    for region in metadata['regions']+[r for r in terrain['regions']+movement['regions'] if r['execution_compared']]:
        lo,hi=region['start'],region['end_exclusive']
        command=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
        rows=parse_disassembly(p.stdout,data,lo,hi);require(len(rows)==region['instruction_count'],'airborne decode count differs')
        commands.append({'argv':command,'stdout':p.stdout,'stderr':p.stderr,'exit_status':p.returncode})
        instructions[region['id']]=rows
        if region['execution_compared']:executable.extend(rows)
    graph=closed_graph(data,executable,[r['pc'] for r in metadata['continuation_boundaries']])
    checks=[(0xaaea,4,'subqw'),(0xaaf6,4,'addqw'),(0xab20,4,'subw'),(0xab3a,4,'addw'),(0xab4e,4,'subw'),(0xab64,2,'asrw'),(0xab66,2,'negw'),(0xab72,4,'dbf'),(0xab84,4,'subw'),(0xab96,4,'cmpw'),(0xabfc,4,'cmpw'),(0x9c02,4,'dbf')]
    for pc,size,mnemonic in checks:
        command=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+size].hex()]
        p=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
        row,=parse_disassembly(p.stdout,data,pc,pc+size);require(row['assembly'].split()[0]==mnemonic,'GNU airborne corroboration failed')
        commands.append({'argv':command,'stdout':p.stdout,'stderr':p.stderr,'exit_status':p.returncode})
    result={'instructions':instructions,'graph':graph,'commands':commands,
            'version':subprocess.check_output(['rasm2','-v'],text=True,timeout=10).strip(),'gnu_checks':len(checks)}
    atomic_write(out/'decoder-evidence.json',(json.dumps(result,indent=2)+'\n').encode())
    return {'executed_scope_instructions':graph['instructions'],'continuation_exits':graph['continuations'],'new_scope_instructions':sum(r['instruction_count'] for r in metadata['regions'] if r['execution_compared']),
            'static_context_instructions':sum(r['instruction_count'] for r in metadata['regions'] if not r['execution_compared']),'gnu_checks':len(checks)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--disassemble',action='store_true');args=parser.parse_args(argv)
    verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes();metadata=json.loads((ROOT/'re/airborne_update.json').read_text())
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/airborne-probe')))
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
