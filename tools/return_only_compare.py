"""Restricted original active/presentation/RTS dispatch versus retained return-only objects."""
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
from return_only_cases import case, corpus


def probe(data,meta,out):
    validate(data,meta);rows=[];commands=[]
    ranges=[(r['start'],r['end_exclusive'],r['instruction_count']) for r in meta['regions']]
    for lo,hi,n in ranges:
        cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        decoded=parse_disassembly(p.stdout,data,lo,hi);require(len(decoded)==n,'return-only decoder count differs')
        rows.extend(decoded);commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    addresses={r['address'] for r in rows};exits={0x69c2,0};edges=[]
    indirect={0xf84e:[0],0x69ba:[0x12646],0x69c0:[0x12646]}
    for r in rows:
        pc=r['address'];op=word(data,pc)
        if op==0x4e75:continue
        targets=[pc+r['size']];t=transfer(data,pc)
        if pc in indirect:
            require(op==(0x4ed0 if pc==0xf84e else 0x4e90),'return-only indirect opcode differs')
            if op==0x4ed0:targets=[]
            targets+=indirect[pc]
        elif t is not None:
            if op&0xff00==0x6000 or op in (0x4ef9,0x4efa):targets=[]
            targets.append(t)
        else:require(not 0x4e80<=op<=0x4eff,'unknown return-only indirect transfer')
        for t in targets:
            require(t in addresses or t in exits,'return-only graph escapes declared scope');edges.append([pc,t])
    for pc,n,mnemonic in ((0x69ae,2,'bpl'),(0x69ba,2,'jsr'),(0xf774,4,'subqb'),(0x12646,2,'rts')):
        cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+n].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15);row,=parse_disassembly(p.stdout,data,pc,pc+n)
        require(row['assembly'].split()[0].startswith(mnemonic),'return-only GNU corroboration differs');commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    save(out/'static.json',dict(commands=commands,edges=edges,exits=sorted(exits),instructions=len(addresses),gnu_checks=4,
          limitation='GNU corroborates four selected dispatch/presentation opcodes only. No new original mapping is inferred from composition.'))
    return addresses


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);meta=json.loads((ROOT/'re/return_only_step.json').read_text())
    native=verify_executable(args.preset,'wiznliz-return-only');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/return-only-comparison')))
    report=dict(ok=False,preset=args.preset,scope=meta['contract'],rom_sha256=identity['sha256'],groups=[],
        native_build=json.loads((native.parent/'provenance.json').read_text()),reference_build=json.loads(REPORT.read_text()),
        sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/return_only_compare.py','tests/return_only_cases.py','re/return_only_step.json')})
    try:
        pcs=probe(DEFAULT_ROM.read_bytes(),meta,out);visited=set()
        groups=[('scheduled','--return-only',corpus())]
        for name,original,rows in groups:
            data=encode_cases(rows);atomic_write(out/(name+'.in'),data);results={};processes={}
            for kind,cmd in [('native',[str(native)]),('reference',[str(reference),str(DEFAULT_ROM),original])]:
                r=subprocess.run(cmd,input=data,capture_output=True,timeout=180)
                atomic_write(out/(name+'-'+kind+'.stdout'),r.stdout);atomic_write(out/(name+'-'+kind+'.stderr'),r.stderr)
                require(r.returncode==0,name+' '+kind+' failed: '+r.stderr.decode()[:1000])
                results[kind]=[tuple(map(int,l.split())) for l in r.stdout.splitlines()]
                require(len(results[kind])==len(rows),'return-only output extent differs')
                processes[kind]=dict(command=cmd,output_sha256=hashlib.sha256(r.stdout).hexdigest())
                if kind=='reference':obs=json.loads(r.stderr);visited.update(obs['visited'])
            for i,(a,b) in enumerate(zip(results['native'],results['reference'])):require(a==b,f'{name} case {i}: {rows[i]} native={a} original={b}')
            report['groups'].append(dict(name=name,cases=len(rows),processes=processes,observation=obs))
        report['rejections']=[]
        rejections=[('callback '+str(mode),case(mode=mode,first=921,counter=1,target=921),b'000000',b'callback') for mode in (0x85,0x87,0x8d)]
        for reason,c,ref_error,native_error in rejections:
            for kind,cmd in [('native',[str(native)]),('reference',[str(reference),str(DEFAULT_ROM),'--return-only'])]:
                r=subprocess.run(cmd,input=encode_cases([c]),capture_output=True,timeout=10)
                require(r.returncode==2 and not r.stdout,'unsupported return-only work accepted')
                require((ref_error if kind=='reference' else native_error) in r.stderr,'wrong return-only rejection boundary: '+r.stderr.decode())
                report['rejections'].append(dict(kind=kind,reason=reason,stderr=r.stderr.decode()))
        require(visited<=pcs,'execution escaped return-only graph')
        required={pc for pc in pcs if not 0xf7ee<=pc<0xf850}
        require(required<=visited,'successful return-only instruction coverage incomplete')
        report.update(ok=True,cases=sum(g['cases'] for g in report['groups']),visited_pcs=sorted(visited),successful_instructions_visited=len(visited),new_instructions_visited=0)
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
