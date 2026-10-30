"""Controlled bonus-table completion, partial success and exhaustion from the movie."""
import argparse
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
from bonus_cases import decode,split as split_bonus
from actions_cases import split
from terrain_cases import encode_cases

START,END=3403,3404
EXTRA=(0x5282,0x528e,0x5290,0x451a,0x451e,0x4524,0x5294,0x4770,0x477c,0x47b0,0x47b2,0x529e,0x52a0,0x52a2,0x52a6,0x52ae)
RANGES=(('bonus_assigned',0x802,22),('bonus_choices',0x818,22),('bonus_counters',0x82e,4))
ALL_LABELS=LABELS+tuple(l for l,o,n in RANGES)
BUTTONS=['P1 A','P1 C','P1 Start']


def recipe():
    r=tally_recipe();r['pcs']=list(dict.fromkeys(r['pcs']+list(EXTRA)))
    r['ranges'] += [dict(label=l,domain='68K RAM',offset=o,length=n) for l,o,n in RANGES]
    return r


def bonus_fields(e):
    require(all(len(block(e,l))==n for l,o,n in RANGES),'bonus table snapshot extent differs')
    return (*(be(block(e,'bonus_counters'),i) for i in (0,2)),*(be(block(e,l),i) for l in ('bonus_assigned','bonus_choices') for i in range(0,22,2)))


def validate(trace,start,end):
    pairs=validate_dispatch(trace,start,end,completion_modes=(3,),sample_returns=(0x5282,));require(len(pairs)==1,'bonus experiment wrapper count differs')
    p=pairs[0];es=[e for e in trace['events'] if e['frame']==start and e['registers']['M68K A6']==0xffff1ab4]
    def one(pc):
        found=[e for e in es if e['pc']==pc];require(len(found)==1,'bonus boundary count differs: '+hex(pc));return found[0]
    def same(a,b,labels=ALL_LABELS):require(all(block(a,l)==block(b,l) for l in labels),'uncontracted bonus state change')
    def stack(e,sp,ret):require(e['registers']['M68K A7']==sp and be(block(e,'stack'),0,4)==ret,'bonus pending return differs')
    require([e['pc'] for e in p['handlers']]==[0x51c8,0x5222] and not p['callbacks'] and not p['sounds'],'unexpected bonus continuation/effect')
    entry,common=p['handlers'];sp=entry['registers']['M68K A7'];stack(common,sp,0xf906);same(entry,common)
    coast,after=one(0xa148),one(0x522c);cr=[e for e in es if e['pc'] in (0xa15c,0xa168)];require(len(cr)==1,'coasting return count differs')
    require(common['sequence']<coast['sequence']<cr[0]['sequence']<after['sequence'],'coasting order differs')
    stack(coast,sp-4,0x522c);stack(cr[0],sp-4,0x522c);stack(after,sp,0xf906);same(cr[0],after)
    branch=one(0x5266);stack(branch,sp,0xf906);same(after,branch)
    require(tally_fields(branch)[1:3]==(0,0) and tally_fields(branch)[5]==0 and block(branch,'control')[0x21]!=0 and block(branch,'control')[0x14]&0x70==0x10,'bonus trigger differs')
    require(len(p['samples'])==1,'bonus sample count differs');sample,sample_rts=p['samples'][0]
    restored,gate=one(0x5282),one(0x528e)
    require(branch['sequence']<sample['sequence']<sample_rts['sequence']<restored['sequence']<gate['sequence'],'sample/gate order differs')
    stack(sample,sp-20,0x5282);stack(sample_rts,sp-20,0x5282)
    require(restored['registers']['M68K A7']==sp-16,'saved D0-D3 extent differs');stack(gate,sp,0xf906)
    same(branch,sample);same(sample_rts,restored)
    same(restored,gate,tuple(l for l in ALL_LABELS if l!='special_gate'))
    require(tally_fields(sample)[5]==0 and tally_fields(gate)[5]==65535,'special gate timing differs')
    starts=[e for e in es if e['pc']==0x451a];require(1<=len(starts)<=5,'availability call count differs')
    done=one(0x52a6);tail=one(0x52ae);assignments=[];negative=False;previous=gate
    for i,call in enumerate(starts):
        stop=starts[i+1] if i+1<len(starts) else done
        window=[e for e in es if call['sequence']<=e['sequence']<stop['sequence']]
        def single(pc):
            hits=[e for e in window if e['pc']==pc];require(len(hits)==1,'bonus helper boundary differs: '+hex(pc));return hits[0]
        scan_rts,returned=single(0x4524),single(0x5294)
        require(previous['sequence']<call['sequence']<scan_rts['sequence']<returned['sequence']<stop['sequence'],'availability order differs')
        same(previous,call);stack(call,sp-4,0x5294);stack(scan_rts,sp-4,0x5294);stack(returned,sp,0xf906);same(call,scan_rts);same(scan_rts,returned)
        scans=[e for e in window if e['pc']==0x451e];require(scans,'missing availability reads')
        index=(scan_rts['registers']['M68K A0']&0xffff)-0x802-2
        require(index>=0 and index%2==0 and index<22,'scan escaped declared table')
        value=be(block(call,'bonus_assigned'),index);negative=bool(value&0x8000)
        require((scan_rts['registers']['M68K SR']&0x0c)==(8 if negative else 4),'availability flags differ')
        require(value==0 or negative,'availability returned a positive value')
        require([e['registers']['M68K A0']&0xffff for e in scans]==list(range(0x802,0x804+index,2)),'scan order/extent differs')
        if negative:
            require(i==len(starts)-1 and not any(e['pc'] in (0x4770,0x52a0) for e in window),'negative scan continued allocation');previous=returned;continue
        select,srts,sret,write,written=(single(pc) for pc in (0x4770,0x47b0,0x529e,0x52a0,0x52a2))
        require(returned['sequence']<select['sequence']<srts['sequence']<sret['sequence']<write['sequence']<written['sequence'],'selection/write order differs')
        stack(select,sp-6,0x529e);stack(srts,sp-6,0x529e);stack(write,sp,0xf906);stack(written,sp,0xf906)
        require(select['registers']['M68K D2']==0 and sret['registers']['M68K A7']==sp-2,'selection mode/saved counter differs')
        same(returned,select);same(srts,sret);same(sret,write)
        same(select,write,tuple(l for l in ALL_LABELS if l!='bonus_counters'))
        j=(write['registers']['M68K A1']&0xffff)-0x802;require(0<=j<22 and j%2==0,'selected slot extent differs')
        value=write['registers']['M68K D3']&65535
        require(be(block(write,'bonus_assigned'),j)==0 and value==be(block(write,'bonus_choices'),j),'selected source/empty slot differs')
        before=bytearray(block(write,'bonus_assigned'));before[j:j+2]=value.to_bytes(2,'big')
        require(bytes(before)==block(written,'bonus_assigned'),'bonus assignment differs');same(write,written,tuple(l for l in ALL_LABELS if l!='bonus_assigned'))
        assignments.append((j//2,value));previous=written
    require(negative or len(assignments)==5,'loop ended without sentinel or five writes')
    stack(done,sp,0xf906);stack(tail,sp,0xf906);same(previous,done)
    require(done['sequence']<tail['sequence']<p['end']['sequence'],'bonus completion/return order differs')
    same(done,tail,tuple(l for l in ALL_LABELS if l!='action_globals'));same(tail,p['end']);same(p['end'],p['return'],tuple(l for l in ALL_LABELS if l!='control'))
    require(shared_fields(tail)[0]==3 and tally_fields(tail)[5]==65535,'bonus completion state differs')
    same(entry,p['return'],('bonus_choices','tally_gate','remaining','skip','tally_countdown','credit','transition','palette_flags','requested_position','saved_position'))
    p['assignments']=tuple(assignments);p['probes']=sum(e['pc'] in (0x451e,0x477c) for e in es)
    return p


def compare_window(trace,directory,native,scene,bank,start,end):
    p=validate(trace,start,end);a,b=p['wrapper'],p['return']
    c=(*action_case(a),*tracking_fields(a),*transition_fields(a),*tally_fields(a),block(a,'control')[0x21],*bonus_fields(a))
    for n,d in [('scene.bin',scene),('bank.bin',bank),('cases.txt',encode_cases([c]))]:atomic_write(directory/n,d)
    command=[str(native),'movie.scene',str(directory/'scene.bin'),'movie.bank',str(directory/'bank.bin'),'--bonus-sequence']
    proc=subprocess.run(command,input=encode_cases([c]),capture_output=True,timeout=60)
    atomic_write(directory/'native.stdout',proc.stdout);atomic_write(directory/'native.stderr',proc.stderr);require(proc.returncode==0,'native bonus failed: '+proc.stderr.decode())
    row,=decode(proc.stdout,1);row,bonus,probes,assigned=split_bonus(row)
    require(bonus==bonus_fields(b) and assigned==p['assignments'] and probes==p['probes'],'bonus fields/order/probes diverged')
    require(row[-6:]==tally_fields(b),'tally diverged');row=row[:-6]
    require(row[-13:]==transition_fields(b,a) and row[-17:-13]==tracking_fields(b),'transition/tracking diverged')
    core,shared,samples=split(row[:-17]);require(core[:18]==snapshot_fields(b,be(block(a,'actor'),0x1a,4)),'actor/scratch diverged')
    require(shared==shared_fields(b) and samples==((0,200,0xf14),) and core[21]==0,'mailbox/request diverged')
    return dict(ok=True,wrapper_calls=1,assignments=assigned,probes=probes,sample_requests=1,command=command,output_sha256=hashlib.sha256(proc.stdout).hexdigest())


def edits(before,kind):
    require(before[0x82e:0x832].hex()=='00060001' and before[0x802:0x80e].hex()=='00000000000000000000ffff','experiment starting tables differ')
    changes=[(0x714,b'\0\0'),(0xf0e,b'\0\0'),(0x104,b'\0\0')]
    if kind=='partial-reset':changes += [(0x802,before[0x818:0x81e]),(0x830,b'\0\6')]
    elif kind=='exhausted':changes += [(0x802,before[0x818:0x822])]
    else:require(kind=='five','unknown bonus experiment')
    return dict(expectedFrame=START,writes=[dict(domain='68K RAM',offset=o,expectedHex=before[o:o+len(v)].hex(),hex=v.hex()) for o,v in changes])


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path);p.add_argument('--preset',choices=('debug','release','sanitize'),default='debug')
    p.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug');args=p.parse_args(argv)
    external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity);native=verify_executable(args.preset,'wiznliz-actor')
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[],'movie input/edit identity differs')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256 and source['instrumentation']=={} and source['rom']['sha256']==identity['sha256'],'movie baseline differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/bonus-experiments')))
    names=('tools/genesis_bonus_capture.py','tools/genesis_tally_capture.py','tools/genesis_transition_capture.py','tools/genesis_actions_capture.py','tools/genesis_dispatch_capture.py','tools/genesis_movie_actor_capture.py','tests/actor_cases.py','tests/bonus_cases.py')
    report=dict(ok=False,classification='controlled RAM edits and explicit A+C+Start input branch from user movie; not ordinary gameplay',recipe=recipe(),experiments=[],
        scope='one P1 wrapper per controlled scenario, sample request, special gate and table assignment order; no object allocation, table consumers or whole-frame parity',
        recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(),movie_sha256=MOVIE_SHA256,input_sha256=INPUT_SHA256,
        contract_sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},native_build=json.loads((native.parent/'provenance.json').read_text()))
    try:
        for kind in ('five','partial-reset','exhausted'):
            end=END
            name=kind;directory=out/name;directory.mkdir();results=[]
            for hooked in (True,False):
                label='hooked' if hooked else 'unhooked'
                with WorkerClient([str(external/'run-worker.sh'),'--storage',str(directory/(label+'-worker'))]) as w:
                    s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity'];report['capabilities']=check_worker(w,s,external);s.seek(START)
                    require(report['capabilities']['capabilities']['ramEdits'],'RAM edits unavailable')
                    before=w.read_bytes('68K RAM',0,65536);edit=edits(before,kind);save(directory/(label+'-edit.json'),w.request('experiment.edit',edit))
                    if hooked:
                        atomic_write(directory/'before.ram',before);scene,bank,terrain=terrain_fixture(before);w.request('trace.configure',recipe())
                    # After direct mutation, do not seek/export the unchanged ReplaySession timeline.
                    advance=w.request('advance',dict(rows=[BUTTONS],render=False,audio=False,timeoutMs=120000))
                    save(directory/(label+'-advance.json'),advance);require(advance.get('frame',advance.get('endFrame'))==end,'incomplete experiment advance')
                    if hooked:
                        trace=w.request('trace.drain');save(directory/'trace.json',trace);require(trace['identity']==s.opened['identity'],'trace identity differs')
                        after=w.read_bytes('68K RAM',0,65536);atomic_write(directory/'after.ram',after);require(terrain_fixture(after)[:2]==(scene,bank),'terrain endpoints differ')
                        comparison=compare_window(trace,directory,native,scene,bank,START,end)
                    snapshot=w.request('snapshot');save(directory/(label+'-snapshot.json'),snapshot);results.append(snapshot)
            require(results[0]['canonicalSha256']==results[1]['canonicalSha256'] and results[0]['hashScope']==results[1]['hashScope'],'hooked/unhooked experiment differs')
            report['experiments'].append(dict(name=name,start=START,end=end,edits=edit,inputs=[BUTTONS],terrain=terrain,comparison=comparison,
                hooked_unhooked_equal=True,final_hash=results[0]['canonicalSha256'],hash_scope=results[0]['hashScope'],
                artifacts={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in directory.iterdir() if f.is_file()}))
        report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','error')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
