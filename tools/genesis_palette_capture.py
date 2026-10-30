"""Controlled movie-state experiments for fixed tally palette preparation and waits."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from rom import ROOT,inspect_file,verify_expected
from rnc import approved_directory,atomic_write
from native_build import verify_executable
from genesis_actor_capture import block,be,save,require,terrain_fixture
from genesis_actions_capture import action_case,shared_fields,check_worker
from genesis_dispatch_capture import validate_dispatch,tracking_fields
from genesis_movie_actor_capture import snapshot_fields,MOVIE_SHA256,INPUT_SHA256
from genesis_transition_capture import transition_fields
from genesis_tally_capture import recipe as tally_recipe,tally_fields,LABELS
from palette_cases import decode
from actions_cases import split
from terrain_cases import encode_cases

START=3403
EXTRA=(0x51da,0x51f4,0x51fa,0x5202,0x5204,0x520e,0x5218,0x5220,0x137ce,0x1372c,0x13752,0x137ee,0x137f4,0x1324e,0x13292)
RANGES=(('palette_source',0xea8,32),('palette_components',0xdc8,48),('palette_other_before',0xd68,96),('palette_other_after',0xdf8,48))
ALL_LABELS=LABELS+tuple(l for l,o,n in RANGES)


def recipe():
    r=tally_recipe();r['pcs']=list(dict.fromkeys(r['pcs']+list(EXTRA)))
    r['ranges'] += [dict(label=l,domain='68K RAM',offset=o,length=n) for l,o,n in RANGES]
    return r


def palette_fields(e):
    require(all(len(block(e,l))==n for l,o,n in RANGES),'palette snapshot extent differs')
    return (*(be(block(e,'palette_source'),i) for i in range(0,32,2)),*block(e,'palette_components'))


def validate(trace,start,end):
    pairs=validate_dispatch(trace,start,end);events=trace['events'];initialized=[];completed=[]
    for p in pairs:
        es=[e for e in events if e['frame']==p['start']['frame'] and e['registers']['M68K A6']==0xffff1ab4]
        def one(pc):
            found=[e for e in es if e['pc']==pc];require(len(found)==1,'palette boundary count differs: '+hex(pc));return found[0]
        def same(a,b,labels=ALL_LABELS):
            require(all(block(a,l)==block(b,l) for l in labels),'uncontracted palette state change')
        def stack(e,sp,ret):
            require(e['registers']['M68K A7']==sp and be(block(e,'stack'),0,4)==ret,'palette pending return differs')
        require(len(p['handlers'])==1 and not p['callbacks'] and not p['sounds'] and not p['samples'],'unexpected palette continuation/effect')
        entry=p['handlers'][0];pc=entry['pc'];sp=entry['registers']['M68K A7'];stack(entry,sp,0xf906)
        require(pc in (0x51c8,0x5204,0x5222),'unexpected palette handler')
        require(be(block(entry,'actor'),0x4a,4)==0xffff0690,'palette control association differs')
        same(p['wrapper'],entry);same(p['end'],p['return'],tuple(l for l in ALL_LABELS if l not in ('control',)))
        require(not any(e['pc']==0x5266 for e in es),'unsupported bonus path')
        coast=one(0xa148);after=one({0x51c8:0x51da,0x5204:0x520e,0x5222:0x522c}[pc])
        returns=[e for e in es if e['pc'] in (0xa15c,0xa168)];require(len(returns)==1,'coasting return count differs');last=returns[0]
        require(entry['sequence']<coast['sequence']<last['sequence']<after['sequence']<p['end']['sequence'],'coast call order differs')
        stack(coast,sp-4,after['pc']);stack(last,sp-4,after['pc']);stack(after,sp,0xf906);same(last,after)
        # Reloading A5 and JSR do not mutate logical memory.
        same(entry,coast)
        if pc==0x51c8:
            require(tally_fields(entry)[0]!=0,'palette gate is zero');branch=one(0x51d0);same(entry,branch);stack(branch,sp,0xf906)
            require(entry['sequence']<branch['sequence']<coast['sequence'],'palette gate branch order differs')
        direction=transition_fields(after)[0]
        initializes=pc==0x51c8 and not direction
        helper_pcs=(0x137ce,0x1372c,0x13752,0x137ee,0x137f4,0x51f4,0x1324e,0x13292,0x51fa,0x5202)
        require(all(sum(e['pc']==v for e in es)==int(initializes) for v in helper_pcs),'unexpected palette helper execution')
        if initializes:
            points=[one(v) for v in helper_pcs]
            require(after['sequence']<points[0]['sequence'] and all(a['sequence']<b['sequence'] for a,b in zip(points,points[1:])) and points[-1]['sequence']<p['end']['sequence'],'palette helper order differs')
            wrapper,convert,converted,back,wrts,ret,init,irts,iret,tail=points
            for e in (wrapper,wrts):stack(e,sp-4,0x51f4)
            for e in (convert,converted):stack(e,sp-20,0x137ee)
            require(back['registers']['M68K A7']==sp-16,'palette saved-register stack differs')
            for e in (init,irts):stack(e,sp-4,0x51fa)
            for e in (ret,iret,tail):stack(e,sp,0xf906)
            require(wrapper['registers']['M68K A0']==0xffff0ea8 and wrapper['registers']['M68K D0']&65535==2,'palette bank/source differs')
            require(convert['registers']['M68K A0']==0xffff0ea8 and convert['registers']['M68K A1']==0xffff0dc8 and convert['registers']['M68K D0']&65535==15,'palette conversion extent differs')
            require(converted['registers']['M68K A0']==0xffff0ec8 and converted['registers']['M68K A1']==0xffff0df8 and converted['registers']['M68K D0']&65535==65535,'palette conversion endpoint differs')
            require(all(wrapper['registers'][r]==wrts['registers'][r] for r in ('M68K A0','M68K A1','M68K D1')),'palette wrapper failed to restore registers')
            same(after,wrapper);same(wrapper,convert);same(converted,back);same(back,wrts);same(wrts,ret);same(ret,init);same(irts,iret)
            same(wrapper,ret,tuple(l for l in ALL_LABELS if l!='palette_components'))
            same(init,iret,tuple(l for l in ALL_LABELS if l not in ('transition','palette_flags')))
            require(block(init,'palette_flags')[:2]==block(iret,'palette_flags')[:2],'initializer changed dirty flag')
            same(iret,tail,tuple(l for l in ALL_LABELS if l!='actor'))
            require(be(block(tail,'actor'),0x16,4)==0x5204,'palette wait assignment differs')
            initialized.append(entry['frame'])
        elif pc in (0x51c8,0x5204):
            tail=one(0x4f8c if direction else 0x5220);stack(tail,sp,0xf906)
            if direction:same(after,tail)
            else:
                select=one(0x5218);same(after,select);stack(select,sp,0xf906)
                require(after['sequence']<select['sequence']<tail['sequence'],'wait assignment order differs')
                same(after,tail,tuple(l for l in ALL_LABELS if l!='actor'))
                require(be(block(tail,'actor'),0x16,4)==0x5222,'tally assignment differs');completed.append(entry['frame'])
        else:
            # This bounded experiment ends during the ordinary positive countdown.
            counter=one(0x537c);tail=one(0x53a2);stack(counter,sp,0xf906);stack(tail,sp,0xf906)
            require(after['sequence']<counter['sequence']<tail['sequence'],'tally countdown order differs')
        require(after['sequence']<tail['sequence']<p['end']['sequence'],'selected handler return order differs');same(tail,p['end'])
        same(entry,p['end'],('palette_source','palette_other_before','palette_other_after'))
        if p is not pairs[0]:
            previous=pairs[pairs.index(p)-1]['return']
            require(block(previous,'palette_components')==block(entry,'palette_components'),'external palette destination change')
            require(tally_fields(previous)[1:5]==tally_fields(entry)[1:5],'external tally counter change')
    require(len(initialized)==len(completed)==1 and initialized[0]<completed[0]<end-1,'missing initialization/wait completion/deferred tally')
    return pairs,initialized,completed


def compare_window(trace,directory,native,scene,bank,start,end):
    pairs,initialized,completed=validate(trace,start,end)
    cases=[(*action_case(p['wrapper']),*tracking_fields(p['wrapper']),*transition_fields(p['wrapper']),*tally_fields(p['wrapper']),block(p['wrapper'],'control')[0x21],*palette_fields(p['wrapper'])) for p in pairs]
    for n,d in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases(cases))]:atomic_write(directory/n,d)
    command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),'--palette-sequence']
    proc=subprocess.run(command,input=encode_cases(cases),capture_output=True,timeout=60)
    atomic_write(directory/'native.stdout',proc.stdout);atomic_write(directory/'native.stderr',proc.stderr)
    require(proc.returncode==0,'palette sequence failed: '+proc.stderr.decode())
    for row,p in zip(decode(proc.stdout,len(cases)),pairs):
        a,b=p['wrapper'],p['return'];require(row[-64:]==palette_fields(b),'palette destination/source diverged')
        row=row[:-64];require(row[-6:]==tally_fields(b),'tally diverged');row=row[:-6]
        require(row[-13:]==transition_fields(b,a) and row[-17:-13]==tracking_fields(b),'transition/tracking diverged')
        core,shared,samples=split(row[:-17]);require(core[:18]==snapshot_fields(b,be(block(a,'actor'),0x1a,4)),'actor/scratch diverged')
        require(shared==shared_fields(b) and not samples and core[21]==0,'shared state/effects diverged')
    return dict(ok=True,continuous_wrapper_calls=len(pairs),handlers=dict(Counter(hex(p['handlers'][0]['pc']) for p in pairs)),
                initialized_frames=initialized,completed_wait_frames=completed,command=command,output_sha256=hashlib.sha256(proc.stdout).hexdigest())


def edits(before,delayed):
    require(before[0x33ce:0x33d0]==b'\0\0' and before[0xb90:0xb98].hex()=='000000000001000e','experiment starting gate/transition differs')
    writes=[(0x33ce,'0001')]
    if delayed:writes += [(0xb90,'0001'),(0xb92,'0003'),(0xb96,'0000'),(0xdc8,'a5'*48)]
    return dict(expectedFrame=START,writes=[dict(domain='68K RAM',offset=o,expectedHex=before[o:o+len(v)//2].hex(),hex=v) for o,v in writes])


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path);p.add_argument('--preset',choices=('debug','release','sanitize'),default='debug')
    p.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug');args=p.parse_args(argv)
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity);native=verify_executable(args.preset,'wiznliz-actor')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[],'movie input/edit identity differs')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256 and source['instrumentation']=={} and source['rom']['sha256']==identity['sha256'],'movie baseline differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/palette-experiments')))
    names=('tools/genesis_palette_capture.py','tools/genesis_tally_capture.py','tools/genesis_transition_capture.py','tools/genesis_actions_capture.py','tools/genesis_dispatch_capture.py','tools/genesis_movie_actor_capture.py','tests/actor_cases.py','tests/palette_cases.py')
    report=dict(ok=False,classification='controlled RAM-edit experiments branching from the user movie; not ordinary gameplay',recipe=recipe(),experiments=[],
        scope='continuous P1 actor/service/tracking, tally counters and prepared palette destination; explicit world timer/source/control/scratch inputs; no palette consumer/rendering or whole-frame parity',
        recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(),movie_sha256=MOVIE_SHA256,input_sha256=INPUT_SHA256,
        contract_sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},native_build=json.loads((native.parent/'provenance.json').read_text()))
    try:
        for delayed,end in ((False,3420),(True,3423)):
            name='initial-wait' if delayed else 'ready';directory=out/name;directory.mkdir();results=[]
            for hooked in (True,False):
                label='hooked' if hooked else 'unhooked'
                with WorkerClient([str(external/'run-worker.sh'),'--storage',str(directory/(label+'-worker'))]) as w:
                    s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];report['capabilities']=check_worker(w,s,external);s.seek(START)
                    before=w.read_bytes('68K RAM',0,65536);edit=edits(before,delayed);save(directory/(label+'-edit.json'),w.request('experiment.edit',edit))
                    if hooked:
                        atomic_write(directory/'before.ram',before);scene,bank,terrain=terrain_fixture(before);w.request('trace.configure',recipe())
                    # After direct mutation, do not seek/export the unchanged ReplaySession timeline.
                    advance=w.request('advance',dict(rows=source['inputs'][START:end],render=False,audio=False,timeoutMs=120000))
                    save(directory/(label+'-advance.json'),advance);require(advance.get('frame',advance.get('endFrame'))==end,'incomplete experiment advance')
                    if hooked:
                        trace=w.request('trace.drain');save(directory/'trace.json',trace);require(trace['identity']==s.opened['identity'],'trace identity differs')
                        after=w.read_bytes('68K RAM',0,65536);atomic_write(directory/'after.ram',after);require(terrain_fixture(after)[:2]==(scene,bank),'terrain endpoints differ')
                        comparison=compare_window(trace,directory,native,scene,bank,START,end)
                    snapshot=w.request('snapshot');save(directory/(label+'-snapshot.json'),snapshot);results.append(snapshot)
            require(results[0]['canonicalSha256']==results[1]['canonicalSha256'] and results[0]['hashScope']==results[1]['hashScope'],'hooked/unhooked experiment differs')
            report['experiments'].append(dict(name=name,start=START,end=end,edits=edit,inputs=source['inputs'][START:end],terrain=terrain,comparison=comparison,
                hooked_unhooked_equal=True,final_hash=results[0]['canonicalSha256'],hash_scope=results[0]['hashScope'],
                artifacts={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in directory.iterdir() if f.is_file()}))
        report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
