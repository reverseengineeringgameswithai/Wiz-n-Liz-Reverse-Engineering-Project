"""Restricted original 7A88 table motion and scheduled comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write
from native_build import PRESETS, verify_executable
from build_terrain_reference import verify_executable as reference_executable, REPORT
from genesis_actor_capture import save, require
from movement_probe import validate, transfer
from rnc_loader_probe import parse_disassembly
from reset_probe import word
from terrain_cases import encode_cases
from table_motion_cases import case, corpus, presentations


def probe(data,meta,out):
    validate(data,meta);rows=[];commands=[]
    for r in meta['data']+meta['writers']:
        require(hashlib.sha256(data[r['start']:r['end_exclusive']]).hexdigest()==r['sha256'],'table data/writer hash differs')
    ranges=[(r['start'],r['end_exclusive'],r['instruction_count']) for r in meta['regions']]
    writer_rows=[]
    for r in meta['writers']:
        lo,hi=r['start'],r['end_exclusive'];cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        decoded=parse_disassembly(p.stdout,data,lo,hi);require(len(decoded)==r['instruction_count'],'writer decode differs')
        writer_rows.extend(decoded);commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    ranges += [(0xf76c,0xf850,59),(0x12646,0x12648,1),(0x69aa,0x69c2,7)]
    for lo,hi,n in ranges:
        cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        decoded=parse_disassembly(p.stdout,data,lo,hi);require(len(decoded)==n,'table-motion decoder count differs')
        rows.extend(decoded);commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    addresses={r['address'] for r in rows};exits={0x69c2,0x79b6};edges=[]
    indirect={0xf84e:[0x79b6],0x69ba:[0x7a88],0x69c0:[0x12646]}
    for r in rows:
        pc=r['address'];op=word(data,pc)
        if op==0x4e75:continue
        targets=[pc+r['size']];t=transfer(data,pc)
        if pc in indirect:
            require(op==(0x4ed0 if pc==0xf84e else 0x4e90),'table-motion indirect opcode differs')
            if op==0x4ed0:targets=[]
            targets+=indirect[pc]
        elif t is not None:
            if op&0xff00==0x6000 or op in (0x4ef9,0x4efa):targets=[]
            targets.append(t)
        else:require(not 0x4e80<=op<=0x4eff,'unknown table-motion indirect transfer')
        for t in targets:
            require(t in addresses or t in exits,'table-motion graph escapes declared scope');edges.append([pc,t])
    for pc,n,mnemonic in ((0x7aa0,4,'addw'),(0x7ac6,4,'negw'),(0x7ad0,4,'dbf'),(0x7ad4,2,'rts')):
        cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+n].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15);row,=parse_disassembly(p.stdout,data,pc,pc+n)
        require(row['assembly'].split()[0].startswith(mnemonic),'table-motion GNU corroboration differs');commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    writer_pcs={r['address'] for r in writer_rows}
    for r in writer_rows:
        pc=r['address'];op=word(data,pc)
        if op==0x4e75:continue
        targets=[pc+r['size']];t=transfer(data,pc)
        if t is not None:targets.append(t)
        require(all(t in writer_pcs or t==0x7cea for t in targets),'writer fragment escapes boundary')
    direct=[i for i in range(0,len(data)-3,2) if data[i:i+4]==bytes.fromhex('ffff31bc')]
    require(direct==[0x7a52,0x7a8e,0x7cde],'direct FF31BC references differ')
    save(out/'static.json',dict(writer_instructions=len(writer_pcs),direct_ff31bc_operands=direct,commands=commands,edges=edges,exits=sorted(exits),instructions=len(addresses),gnu_checks=4,
          limitation='GNU corroborates four selected opcodes only. Immediate MOVE.W forms are not GNU-corroborated; primary decoding and restricted execution cover those instructions.'))
    return addresses


def audit_writers(reference,out):
    # Research fragments only: this does not implement/schedule their parent routines.
    rows=[(1,65536,65535,i) for i in range(65536)]
    rows += [(1,1,i,0) for i in range(65536)]
    rows += [(kind,rise,count,timer) for kind in (0,1) for rise in (0,1,65536,0x80000000,0xffffffff)
             for count in (0,1,32767,32768,65535) for timer in (0,1,40,80,32768,32769,65535)]
    data=encode_cases(rows);atomic_write(out/'writers.in',data)
    cmd=[str(reference),str(DEFAULT_ROM),'--table-writers'];p=subprocess.run(cmd,input=data,capture_output=True,timeout=90)
    atomic_write(out/'writers.stdout',p.stdout);atomic_write(out/'writers.stderr',p.stderr)
    require(p.returncode==0,'original writer fragment failed: '+p.stderr.decode()[:500])
    actual=[tuple(map(int,l.split())) for l in p.stdout.splitlines()];require(len(actual)==len(rows),'writer output extent differs')
    for row,got in zip(rows,actual):
        kind,rise,count,timer=row
        if not kind:expected=(0,80)
        elif not rise:expected=(count,timer)
        else:
            timer=(timer-1)&65535;expected=((count+1)&65535,40) if timer&32768 else (count,timer)
        require(got==expected,'writer fragment arithmetic differs')
    obs=json.loads(p.stderr);require(set(obs['visited'])=={0x7a46,0x7a4e,0x7a56,0x7cc8,0x7cd2,0x7cd4,0x7cda,0x7cdc,0x7ce2},'writer fragment coverage differs')
    return dict(cases=len(rows),observation=obs,output_sha256=hashlib.sha256(p.stdout).hexdigest(),command=cmd,
        scope='Restricted original versus authored arithmetic; no native producer or callback implementation.')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);meta=json.loads((ROOT/'re/table_motion_step.json').read_text())
    native=verify_executable(args.preset,'wiznliz-table-motion');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/table-motion-comparison')))
    report=dict(ok=False,preset=args.preset,scope=meta['contract'],rom_sha256=identity['sha256'],groups=[],
        native_build=json.loads((native.parent/'provenance.json').read_text()),reference_build=json.loads(REPORT.read_text()),
        sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/table_motion_compare.py','tests/table_motion_cases.py','re/table_motion_step.json')})
    try:
        pcs=probe(DEFAULT_ROM.read_bytes(),meta,out);visited=set()
        report['writer_audit']=audit_writers(reference,out)
        handlers=corpus()
        groups=[('handler','--table-motion',handlers),('scheduled','--table-motion-scheduled',handlers+presentations())]
        for name,original,rows in groups:
            data=encode_cases(rows);atomic_write(out/(name+'.in'),data);results={};processes={}
            for kind,cmd in [('native',[str(native),'--'+name]),('reference',[str(reference),str(DEFAULT_ROM),original])]:
                r=subprocess.run(cmd,input=data,capture_output=True,timeout=180)
                atomic_write(out/(name+'-'+kind+'.stdout'),r.stdout);atomic_write(out/(name+'-'+kind+'.stderr'),r.stderr)
                require(r.returncode==0,name+' '+kind+' failed: '+r.stderr.decode()[:1000])
                results[kind]=[tuple(map(int,l.split())) for l in r.stdout.splitlines()]
                require(len(results[kind])==len(rows),'table-motion output extent differs')
                processes[kind]=dict(command=cmd,output_sha256=hashlib.sha256(r.stdout).hexdigest())
                if kind=='reference':obs=json.loads(r.stderr);visited.update(obs['visited'])
            for i,(a,b) in enumerate(zip(results['native'],results['reference'])):require(a==b,f'{name} case {i}: {rows[i]} native={a} original={b}')
            report['groups'].append(dict(name=name,cases=len(rows),processes=processes,observation=obs))
        report['rejections']=[]
        c=case(mode=133,first=7,counter=1,target=7)
        for kind,cmd in [('native',[str(native),'--scheduled']),('reference',[str(reference),str(DEFAULT_ROM),'--table-motion-scheduled'])]:
            r=subprocess.run(cmd,input=encode_cases([c]),capture_output=True,timeout=10)
            require(r.returncode==2 and not r.stdout,'unsupported table-motion callback accepted')
            require((b'0079b6' if kind=='reference' else b'callback79B6') in r.stderr,'wrong table-motion callback boundary')
            report['rejections'].append(dict(kind=kind,reason='callback',stderr=r.stderr.decode()))
        for reason,c in [('cursor',case(cursor=24)),('loop budget',case(loops=4096)),('loop budget',case(loops=65535,budget=65535))]:
            for kind,cmd in [('native',[str(native),'--handler']),('reference',[str(reference),str(DEFAULT_ROM),'--table-motion'])]:
                r=subprocess.run(cmd,input=encode_cases([c]),capture_output=True,timeout=10)
                require(r.returncode==2 and not r.stdout and reason.encode() in r.stderr,'wrong table rejection boundary')
                report['rejections'].append(dict(kind=kind,reason=reason,stderr=r.stderr.decode()))
        require(visited<=pcs,'execution escaped table-motion graph')
        new={pc for pc in pcs if any(r['start']<=pc<r['end_exclusive'] for r in meta['regions'])}
        require(new<=visited,'new table-motion instruction coverage incomplete')
        report.update(ok=True,cases=sum(g['cases'] for g in report['groups']),visited_pcs=sorted(visited),new_instructions_visited=len(new))
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
