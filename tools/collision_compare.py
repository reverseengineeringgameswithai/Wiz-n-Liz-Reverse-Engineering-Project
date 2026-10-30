"""Restricted AC5E overlap and 78EE miss-only service comparisons; --variant pickup compares the 6BD6 pickup miss service."""
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
from collision_cases import case, overlap_corpus, service_corpus, presentations


# 78EE probe or 6BD6 pickup: service entry, unsupported hit target and the
# native/reference mode names.
VARIANTS={'probe':dict(step='re/collision_step.json',service=0x78ee,hit=0x7910,output='collision-comparison',
                       groups=(('overlap','--overlap','--overlap'),('service','--service','--collision-service'),('scheduled','--scheduled','--collision-scheduled')),
                       native_hit=b'collision-hit7910',reference_hit=b'007910'),
          'pickup':dict(step='re/pickup_service_step.json',service=0x6bd6,hit=0x6c00,output='pickup-service-comparison',
                        groups=(('service','--pickup-service','--pickup-service'),('scheduled','--pickup-scheduled','--pickup-scheduled')),
                        native_hit=b'pickup-hit 6C00',reference_hit=b'006c00')}


def probe(data,meta,out,variant=VARIANTS['probe']):
    validate(data,meta);rows=[];commands=[]
    ranges=[(r['start'],r['end_exclusive'],r['instruction_count']) for r in meta['regions']]
    ranges += [(0xf76c,0xf850,59),(0x12646,0x12648,1),(0x69aa,0x69c2,7)]
    for lo,hi,n in ranges:
        cmd=['rasm2','-a','m68k','-b','32','-e','-c','68000','-s',hex(lo),'-D',data[lo:hi].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        decoded=parse_disassembly(p.stdout,data,lo,hi);require(len(decoded)==n,'collision decoder count differs')
        rows.extend(decoded);commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    addresses={r['address'] for r in rows};exits={0x69c2,variant['hit'],0};edges=[]
    indirect={0xf84e:[0],0x69ba:[0x12646],0x69c0:[variant['service']]}
    for r in rows:
        pc=r['address'];op=word(data,pc)
        if op==0x4e75:continue
        targets=[pc+r['size']];t=transfer(data,pc)
        if pc in indirect:
            require(op==(0x4ed0 if pc==0xf84e else 0x4e90),'collision indirect opcode differs')
            if op==0x4ed0:targets=[]
            targets+=indirect[pc]
        elif t is not None:
            if op&0xff00==0x6000 or op in (0x4ef9,0x4efa):targets=[]
            targets.append(t)
        else:require(not 0x4e80<=op<=0x4eff,'unknown collision indirect transfer')
        for t in targets:
            require(t in addresses or t in exits,'collision graph escapes declared scope');edges.append([pc,t])
    for pc,n,mnemonic in ((0xac66,2,'addw'),(0xac76,2,'cmpw'),(0xac78,2,'bhi'),(0xac9a,2,'rts')):
        cmd=['rasm2','-a','m68k.gnu','-b','32','-e','-c','m68000','-s',hex(pc),'-D',data[pc:pc+n].hex()]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15);row,=parse_disassembly(p.stdout,data,pc,pc+n)
        require(row['assembly'].split()[0].startswith(mnemonic),'collision GNU corroboration differs');commands.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
    save(out/'static.json',dict(commands=commands,edges=edges,exits=sorted(exits),instructions=len(addresses),gnu_checks=4,
          limitation='GNU corroborates four selected arithmetic, branch and return opcodes; primary decoding and restricted execution cover the full helper and miss service.'))
    return addresses


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preset',choices=PRESETS,default='debug');p.add_argument('--variant',choices=VARIANTS,default='probe')
    args=p.parse_args(argv);variant=VARIANTS[args.variant]
    identity=inspect_file();verify_expected(identity);meta=json.loads((ROOT/variant['step']).read_text())
    native=verify_executable(args.preset,'wiznliz-collision');reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/'+variant['output'])))
    report=dict(ok=False,preset=args.preset,variant=args.variant,scope=meta['contract'],rom_sha256=identity['sha256'],groups=[],
        native_build=json.loads((native.parent/'provenance.json').read_text()),reference_build=json.loads(REPORT.read_text()),
        sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tools/collision_compare.py','tests/collision_cases.py',variant['step'])})
    try:
        pcs=probe(DEFAULT_ROM.read_bytes(),meta,out,variant);visited=set()
        services=service_corpus();corpora={'overlap':overlap_corpus() if args.variant=='probe' else [],'service':services,'scheduled':services+presentations()}
        for name,native_mode,original in variant['groups']:
            rows=corpora[name];data=encode_cases(rows);atomic_write(out/(name+'.in'),data);results={};processes={}
            for kind,cmd in [('native',[str(native),native_mode]),('reference',[str(reference),str(DEFAULT_ROM),original])]:
                r=subprocess.run(cmd,input=data,capture_output=True,timeout=180)
                atomic_write(out/(name+'-'+kind+'.stdout'),r.stdout);atomic_write(out/(name+'-'+kind+'.stderr'),r.stderr)
                require(r.returncode==0,name+' '+kind+' failed: '+r.stderr.decode()[:1000])
                results[kind]=[tuple(map(int,l.split())) for l in r.stdout.splitlines()]
                require(len(results[kind])==len(rows),'collision output extent differs')
                processes[kind]=dict(command=cmd,output_sha256=hashlib.sha256(r.stdout).hexdigest())
                if kind=='reference':obs=json.loads(r.stderr);visited.update(obs['visited'])
            for i,(a,b) in enumerate(zip(results['native'],results['reference'])):require(a==b,f'{name} case {i}: {rows[i]} native={a} original={b}')
            report['groups'].append(dict(name=name,cases=len(rows),processes=processes,observation=obs))
        report['rejections']=[]
        rejections=[('callback',case(mode=133,first=7,counter=1,target=7),b'000000',b'callback'),
            ('primary hit',case(primary_x=150,primary_y=262),variant['reference_hit'],variant['native_hit']+b' (primary)'),
            ('secondary hit',case(secondary_gate=32768,secondary_present=1,secondary_x=150,secondary_y=262),variant['reference_hit'],variant['native_hit']+b' (secondary)'),
            ('missing secondary',case(secondary_gate=1),b'secondary collision input unavailable',b'secondary collision input unavailable')]
        _,native_scheduled,reference_scheduled=variant['groups'][-1]
        for reason,c,ref_error,native_error in rejections:
            for kind,cmd in [('native',[str(native),native_scheduled]),('reference',[str(reference),str(DEFAULT_ROM),reference_scheduled])]:
                r=subprocess.run(cmd,input=encode_cases([c]),capture_output=True,timeout=10)
                require(r.returncode==2 and not r.stdout,'unsupported collision work accepted')
                require((ref_error if kind=='reference' else native_error) in r.stderr,'wrong collision rejection boundary: '+r.stderr.decode())
                report['rejections'].append(dict(kind=kind,reason=reason,stderr=r.stderr.decode()))
        require(visited<=pcs,'execution escaped collision graph')
        # AC5E was mapped by the probe pass; the pickup variant's new code is 6BD6 only.
        own=[r for r in meta['regions'] if args.variant=='probe' or r['id']=='pickup_miss_service']
        new={pc for pc in pcs if any(r['start']<=pc<r['end_exclusive'] for r in own)}
        require(new<=visited,'new collision instruction coverage incomplete')
        report.update(ok=True,cases=sum(g['cases'] for g in report['groups']),visited_pcs=sorted(visited),new_instructions_visited=len(new))
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','cases','new_instructions_visited','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
