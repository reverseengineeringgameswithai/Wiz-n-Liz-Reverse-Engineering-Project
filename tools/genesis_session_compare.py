"""Revalidate a completed session capture and compare a fresh native build without replaying the emulator."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from rom import ROOT, inspect_file, verify_expected
from rnc import approved_directory
from native_build import PRESETS, verify_executable
from genesis_actor_capture import save, require, terrain_fixture
from genesis_movie_actor_capture import MOVIE_SHA256, INPUT_SHA256
from genesis_session_capture import recipe, validate_session, compare_session


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path)
    p.add_argument('--preset',choices=PRESETS,default='debug');args=p.parse_args(argv)
    verify_expected(inspect_file());native=verify_executable(args.preset,'wiznliz-session')
    out=Path(tempfile.mkdtemp(prefix='run-',dir=approved_directory(ROOT,'local/generated/session-comparison')))
    report=dict(ok=False,preset=args.preset,reference_report=str(args.report),
                reference_report_sha256=hashlib.sha256(args.report.read_bytes()).hexdigest(),
                classification='fresh native comparison of a previously captured ordinary movie; no new worker replay',
                native_build=json.loads((native.parent/'provenance.json').read_text()),
                sources={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in
                         ('tools/genesis_session_compare.py','tools/genesis_session_capture.py','tools/genesis_dispatch_capture.py')})
    try:
        parent=json.loads(args.report.read_text());directory=args.report.parent
        require(parent['ok'] is True and parent['rom_unchanged'] is True,'reference capture did not pass')
        require(parent['movie_sha256']==MOVIE_SHA256 and parent['input_sha256']==INPUT_SHA256,'reference movie differs')
        start,end=parent['start'],parent['end'];require((start,end) in ((700,1067),(3100,3200)),'unknown session window')
        early=start==700;require(parent['recipe']==recipe(early),'reference instrumentation differs')
        require(parent['endpoint']['hooked']==parent['endpoint']['unhooked'],'reference endpoint mismatch')
        require(set(parent['sources'])=={'tools/genesis_session_capture.py','tools/genesis_dispatch_capture.py',
                'tools/genesis_movie_actor_capture.py','tools/genesis_actions_capture.py'},'incomplete capture source provenance')
        for name,digest in parent['sources'].items():
            require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'capture validation source changed; review and recapture')
        for name,digest in parent['artifacts'].items():
            require(Path(name).name==name,'invalid capture artifact path')
            require(hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest,'capture artifact changed: '+name)
        def read(name):
            require(name in parent['artifacts'],'unhashed capture input: '+name)
            return (directory/name).read_bytes()
        inputs=json.loads(read('inputs.json'));writes=[];events=[]
        for frame in range(start,end):
            t=json.loads(read(f'routines-{frame}.json'))
            require(t['identity']==parent['identity'] and t['dropped']==0 and t['overflow'] is False and t['error'] is None,'incomplete captured routine trace')
            require(all(e['frame']==frame for e in t['events']),'captured drain frame differs');events.extend(t['events'])
            w=json.loads(read(f'writes-{frame}.json'));require(w['identity']==parent['identity'],'captured write identity differs');writes.append(w)
        trace=dict(t,events=events);scene,bank,terrain=terrain_fixture(read('before.ram'))
        require(terrain==parent['terrain'] and terrain_fixture(read('after.ram'))[:2]==(scene,bank),'captured terrain changed')
        pairs,scratch=validate_session(trace,writes,inputs,start,end,terrain,early)
        report['comparison']=compare_session(pairs,inputs,out,native,scene,bank,early)
        report.update(ok=True,start=start,end=end,scratch_writes=scratch,reference_endpoint=parent['endpoint'])
    except Exception as e:report['error']=str(e)
    finally:
        verify_expected(inspect_file());report['rom_unchanged']=True;save(out/'report.json',report)
    print(json.dumps({k:report.get(k) for k in ('ok','error','comparison')}|{'report':str(out/'report.json')},indent=2));return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
