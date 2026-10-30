#!/usr/bin/env python3
"""Survey selected P1 dispatcher/action boundaries in the verified user movie.

Discovery only: handler observations are NOT native comparisons. Uses bounded
300-frame trace batches and rejects overflow. All bulk results remain ignored.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from rom import ROOT,inspect_file,verify_expected
from rnc import approved_directory
from genesis_actor_capture import save,require,block,be,BUILD_ID
from genesis_movie_actor_capture import MOVIE_SHA256,INPUT_SHA256
from actor_cases import HANDLERS


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording',type=Path)
    p.add_argument('--genesis-tools',type=Path,default=ROOT.parent/'BizHawkOpenSource/Tools/GenesisDebug')
    args=p.parse_args(argv);external=args.genesis_tools.resolve();sys.path.insert(0,str(external/'python'))
    from genesis_debug import WorkerClient,ReplaySession
    from genesis_debug.replay import load_recording
    source=load_recording(args.recording);identity=inspect_file();verify_expected(identity)
    require(source['input_sha256']==INPUT_SHA256 and len(source['inputs'])==5298 and source['experimental_edits']==[],'movie inputs/edits differ')
    require(source['start']['imported_movie']['source']['sha256']==MOVIE_SHA256,'movie identity differs')
    require(source['instrumentation']=={} and source['rom']['sha256']==identity['sha256'],'source baseline/ROM differs')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/movie-survey')))
    pcs=[0xf8fc,0xf900,0xf904,0xf906,0xfcb32,0xa2e8,0xa380,0xa50e,0xa654,0xa774,0xa93a,0xa7a8,0xa96e,0x9c56,0x9d4e,0xf90a]
    recipe={'pcs':pcs,'returns':False,'registers':True,'maxEvents':20000,
            'ranges':[{'label':'actor','domain':'68K RAM','offset':0x1ab4,'length':78}]}
    report={'ok':False,'recording_sha256':hashlib.sha256(args.recording.read_bytes()).hexdigest(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'classification':'ordinary recorded gameplay; selected-PC discovery only; zero native comparisons',
            'recipe':recipe,'chunks':[],'action_callback_events':[],
            'unsupported_handler_frames':{},'invoked_callback_counts':{},'selected_service_counts':{}}
    try:
        with WorkerClient([str(external/'run-worker.sh'),'--storage',str(out/'worker')]) as w:
            s=ReplaySession.from_recording(w,source);report['identity']=s.opened['identity']
            report['capabilities']=w.request('capabilities')
            require(report['capabilities']['capabilities']['routineTrace'],'routine tracing unavailable')
            require(s.opened['identity']['build']['buildId']==BUILD_ID,'runtime build differs')
            w.request('trace.configure',recipe)
            for start in range(0,5298,300):
                end=min(5298,start+300);s.seek(end);trace=w.request('trace.drain')
                require(trace['schemaVersion']==1 and trace['boundary']=='instruction-pre-execute','trace schema/boundary differs')
                require(trace['dropped']==0 and trace['overflow'] is False and trace['error'] is None,'incomplete survey trace')
                require(trace['identity']==s.opened['identity'],'trace identity differs')
                events=trace['events'];require(all(a['sequence']<b['sequence'] for a,b in zip(events,events[1:])),'trace order differs')
                require(all(start<=e['frame']<end and e['kind']=='entry' for e in events),'survey event boundary differs')
                path=out/f'{start}-{end}.json';save(path,trace)
                p1=[e for e in events if e['registers']['M68K A6']==0xffff1ab4]
                report['chunks'].append({'start':start,'end':end,'trace':str(path.relative_to(out)),
                    'trace_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'events':len(events),
                    'p1_pc_counts':dict(Counter(hex(e['pc']) for e in p1)),
                    'p1_handler_counts':dict(Counter(hex(be(block(e,'actor'),0x16,4)) for e in p1 if e['pc']==0xf8fc))})
                for e in p1:
                    a=block(e,'actor')
                    if e['pc']==0xf8fc:
                        handler=be(a,0x16,4)
                        if handler not in HANDLERS:report['unsupported_handler_frames'].setdefault(hex(handler),[]).append(e['frame'])
                        if (a[0]&5)==5 and a[12]==1 and be(a,6)==be(a,14):
                            cb=hex(be(a,0x1a,4));report['invoked_callback_counts'][cb]=report['invoked_callback_counts'].get(cb,0)+1
                    if e['pc']==0xf90a:
                        service=be(a,0x46,4);require(service==e['registers']['M68K A0'],'service load differs')
                        key=hex(service);report['selected_service_counts'][key]=report['selected_service_counts'].get(key,0)+1
                report['action_callback_events'].extend({'frame':e['frame'],'pc':hex(e['pc']),
                    'handler':hex(be(block(e,'actor'),0x16,4)),'sequence':e['sequence']} for e in p1 if e['pc'] not in pcs[:5] and e['pc']!=0xf90a)
            final=w.request('snapshot');baseline=next(c for c in source['checkpoints'] if c['frame']==5298)
            require(final['canonicalSha256']==baseline['canonical_sha256'] and final['hashScope']==baseline['hash_scope'],'survey differs from recorded unhooked baseline')
            report['final_covered_state']=final['canonicalSha256'];report['recorded_unhooked_baseline_matched']=True
        report['ok']=True
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({'ok':report['ok'],'report':str(out/'report.json'),'error':report.get('error')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
