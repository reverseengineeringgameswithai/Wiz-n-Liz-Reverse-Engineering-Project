"""Restricted original 6D8C/5A9A/E918 and particle lifetime comparisons."""
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
from trail_cases import case, corpus, particle_cases, rng_cases


def probe(data,meta,out):
    validate(data,meta);rows=[];commands=[]
    ranges=[(r['start'],r['end_exclusive'],r['instruction_count']) for r in meta['regions']]
    ranges += [(0xf994,0xf9d0,14),(0xf76c,0xf850,59),(0xfaa4,0xfabc,7),(0x12646,0x12648,1),(0x69aa,0x69c2,7)]
    for lo,hi,n in ranges:
        cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        decoded=parse_disassembly(p.stdout,data,lo,hi);require(len(decoded)==n,'trail decoder count differs')
        rows.extend(decoded);commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    addresses={r['address'] for r in rows};exits={0x69c2,0xf9d0,0xcafe};edges=[]
    indirect={0xf84e:[0xfaa4,0xcafe],0x69ba:[0x6d8c,0x5ae2],0x69c0:[0x12646]}
    for r in rows:
        pc=r['address'];op=word(data,pc)
        if op==0x4e75:continue
        targets=[pc+r['size']];t=transfer(data,pc)
        if pc in indirect:
            require(op==(0x4ed0 if pc==0xf84e else 0x4e90),'trail indirect opcode differs')
            if op==0x4ed0:targets=[]
            targets+=indirect[pc]
        elif t is not None:
            if op&0xff00==0x6000 or op in (0x4ef9,0x4efa):targets=[]
            targets.append(t)
        else:require(not 0x4e80<=op<=0x4eff,'unknown trail indirect transfer')
        for t in targets:
            require(t in addresses or t in exits,'trail graph escapes declared scope');edges.append([pc,t])
    for pc,n,mnemonic in ((0x6d90,4,'subqw'),(0x6da0,4,'cmpl'),(0x6ddc,2,'moveal'),(0xe928,2,'lsrl'),(0x6dbe,4,'addw')):
        cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+n].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15);row,=parse_disassembly(p.stdout,data,pc,pc+n)
        require(row['assembly'].split()[0].startswith(mnemonic),'trail GNU corroboration differs');commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    save(out/'static.json',dict(commands=commands,edges=edges,exits=sorted(exits),instructions=len(addresses),gnu_checks=5,
          limitation='GNU plugin ignores CPU selection and misdecodes absolute EOR.W at E932; primary decoding and original execution cover that instruction. Only five selected compatible opcodes are GNU-corroborated.'))
    return addresses


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug');args=p.parse_args(argv)
    identity=inspect_file();verify_expected(identity);meta=json.loads((ROOT/'re/trail_step.json').read_text())
    native=verify_executable(args.preset,'wiznliz-trail');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/trail-comparison')))
    report=dict(ok=False,preset=args.preset,scope=meta['contract'],rom_sha256=identity['sha256'],groups=[],
        native_build=json.loads((native.parent/'provenance.json').read_text()),reference_build=json.loads(REPORT.read_text()),
        sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/trail_compare.py','tests/trail_cases.py','re/trail_step.json')})
    try:
        pcs=probe(DEFAULT_ROM.read_bytes(),meta,out);visited=set()
        emitters=corpus()
        groups=[('emitter','--trail',emitters),('scheduled','--trail-scheduled',emitters+[case(mode=m,countdown=1) for m in range(128)]),
                ('particle','--trail-particle',particle_cases()),('rng','--trail-rng',rng_cases()),('spawn','--trail-spawn',[(x,y,1) for x in (0,1,32767,32768,65535) for y in (0,1,32767,32768,65535)])]
        for name,original,rows in groups:
            data=encode_cases(rows);atomic_write(out/(name+'.in'),data);results={};processes={}
            for kind,cmd in [('native',[str(native),'--'+name]),('reference',[str(reference),str(DEFAULT_ROM),original])]:
                r=subprocess.run(cmd,input=data,capture_output=True,timeout=180)
                atomic_write(out/(name+'-'+kind+'.stdout'),r.stdout);atomic_write(out/(name+'-'+kind+'.stderr'),r.stderr)
                require(r.returncode==0,name+' '+kind+' failed: '+r.stderr.decode()[:1000])
                results[kind]=[tuple(map(int,l.split())) for l in r.stdout.splitlines()]
                require(len(results[kind])==len(rows),'trail output extent differs')
                processes[kind]=dict(command=cmd,output_sha256=hashlib.sha256(r.stdout).hexdigest())
                if kind=='reference':obs=json.loads(r.stderr);visited.update(obs['visited'])
            for i,(a,b) in enumerate(zip(results['native'],results['reference'])):require(a==b,f'{name} case {i}: {rows[i]} native={a} original={b}')
            report['groups'].append(dict(name=name,cases=len(rows),processes=processes,observation=obs))
        report['rejections']=[]
        for mode,c,reason in [('emitter',case(capacity=0),'capacity'),('emitter',case(available_owner=2),'owner'),('scheduled',case(mode=133,first=7,counter=1,target=7),'callback')]:
            for kind,cmd in [('native',[str(native),'--'+mode]),('reference',[str(reference),str(DEFAULT_ROM),'--trail'+('-scheduled' if mode=='scheduled' else '')])]:
                r=subprocess.run(cmd,input=encode_cases([c]),capture_output=True,timeout=10)
                require(r.returncode==2 and not r.stdout,'unsupported trail path accepted')
                expected={'capacity':b'00f9d0','owner':b'outside declared fixture','callback':b'00cafe'} if kind=='reference' else {'capacity':b'allocation exhausted','owner':b'owner unavailable','callback':b'unsupported trail emitter callback'}
                require(expected[reason] in r.stderr,'wrong trail rejection boundary')
                report['rejections'].append(dict(kind=kind,reason=reason,stderr=r.stderr.decode()))
        require(visited<=pcs,'execution escaped trail graph')
        new={pc for pc in pcs if any(r['start']<=pc<r['end_exclusive'] for r in meta['regions'])}
        require(new<=visited,'new trail instruction coverage incomplete')
        report.update(ok=True,cases=sum(g['cases'] for g in report['groups']),visited_pcs=sorted(visited),new_instructions_visited=len(new))
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
