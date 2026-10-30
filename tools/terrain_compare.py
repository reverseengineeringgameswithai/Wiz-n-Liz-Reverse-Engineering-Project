"""Compare native terrain semantics against executed original 68000 routines.

Requires a separately built, hash-pinned research CPU. No downloads or reference
execution in normal builds/tests. All proprietary inputs/results remain local.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

from bank_atlas import catalog_entry, read_extracted, MAX_BANK_BYTES
from build_terrain_reference import verify_executable as reference_executable, REPORT as REFERENCE_REPORT
from native_build import verify_executable, PRESETS
from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write
from scene_preview import MAX_SCENE_BYTES
from terrain_probe import validate
from scene_probe import inspect_scene
from rnc_loader_probe import inspect_pattern_bank

sys.path.insert(0,str(ROOT/"tests"))
from terrain_cases import fixture, golden_cases, encode_cases, decode_results


def reference_resources(scene, bank, base):
    sm, bm = inspect_scene(scene), inspect_pattern_bank(bank)
    lo,hi=sm["regions"]["map"]["range"]
    words=struct.unpack(">4096H",scene[lo:hi])
    records=b""
    for data,layout in ((bank,bm),(scene,sm)):
        lo,hi=layout["regions"]["opaque_records"]["range"];records+=data[lo:hi]
    if base < 0 or base + len(records)//8 > 2048 or any((w&2047)>=len(records)//8 for w in words):
        raise ValueError("terrain reference relocation would alias or exceed record bank")
    return struct.pack(">4096H",*(((w+base)&65535)|0x4000 for w in words)),records


def authored_cases():
    cases=[c for c,_ in golden_cases()]
    # Every 16-bit x at one y, then every legal y alias/sentinel at one x.
    cases.extend((0,x,128,3,7) for x in range(65536))
    for y in range(65536):
        local=(y-128)&65535
        if local >= 32768 or (local//8*256 & 65535) < 8192:
            cases.append((0,135,y,6,7))
    # Every record byte vs all eight comparison heights; all three probes and step.
    for mode,offset in ((1,22),(2,23),(3,24),(4,23)):
        cases.extend((mode,116+value,128-offset+within-1,5,7) for value in range(256) for within in range(1,9))
    return cases


def real_cases():
    cases=[(0,128+x,128+y,0,0) for y in range(256) for x in range(1024)]
    # Every cell/column for all three probes and settle, with varied sub-row y.
    for mode,offset in ((1,22),(2,23),(3,24),(4,23)):
        cases.extend((mode,116+x,128-offset+row*8+(x%8),2,6) for row in range(32) for x in range(1024))
    return cases


def check_reference_rejections(out, reference, rom):
    directory=out/"authored-base-0"
    command=[str(reference),str(rom),str(directory/"map.bin"),str(directory/"records.bin"),"0"]
    # These computed original addresses leave the declared fixture. Do not
    # compare arbitrary zero-filled RAM as though it were a terrain record.
    checks=[]
    for case in ((0,128,384,0,0),(0,128,1152,0,0),(0,128,0x807f,0,0)):
        p=subprocess.run(command,input=encode_cases([case]),capture_output=True,timeout=10)
        if p.returncode!=2 or p.stdout or b"read outside declared fixture" not in p.stderr:
            raise ValueError("reference failed undeclared-memory rejection check")
        checks.append({"case":case,"exit_status":p.returncode,"stderr":p.stderr.decode()})
    return checks


def compare_group(out, name, scene, bank, cases, base, native, reference, rom):
    directory=out/name;directory.mkdir()
    map_data,records=reference_resources(scene,bank,base)
    for filename,data in (("scene.bin",scene),("bank.bin",bank),("map.bin",map_data),("records.bin",records),("cases.txt",encode_cases(cases))):
        atomic_write(directory/filename,data)
    commands={"reference":[str(reference),str(rom),str(directory/"map.bin"),str(directory/"records.bin"),str(base)],
              "native":[str(native),"comparison.scene",str(directory/"scene.bin"),"comparison.bank",str(directory/"bank.bin")]}
    result={"name":name,"base":base,"cases":len(cases),"processes":{},"inputs":{}}
    for filename in ("scene.bin","bank.bin","map.bin","records.bin","cases.txt"):
        result["inputs"][filename]=hashlib.sha256((directory/filename).read_bytes()).hexdigest()
    rows={}
    environment={"ASAN_OPTIONS":"detect_leaks=1:halt_on_error=1","UBSAN_OPTIONS":"halt_on_error=1:print_stacktrace=1"}
    for kind,command in commands.items():
        with (directory/"cases.txt").open("rb") as input_stream, (directory/(kind+".txt")).open("wb") as output:
            process=subprocess.run(command,stdin=input_stream,stdout=output,stderr=subprocess.PIPE,
                                   env=os.environ|environment,cwd=ROOT,timeout=60)
        atomic_write(directory/(kind+".stderr"),process.stderr)
        result["processes"][kind]={"command":command,"exit_status":process.returncode,"environment":environment}
        atomic_write(directory/"report.json",(json.dumps(result,indent=2)+"\n").encode())
        if process.returncode: raise ValueError(f"{name} {kind} failed: {process.stderr[:2000].decode(errors='replace')}")
        data=(directory/(kind+".txt")).read_bytes()
        result["processes"][kind]["output_sha256"]=hashlib.sha256(data).hexdigest()
        rows[kind]=decode_results(data,len(cases))
        if kind=="reference":result["reference_observation"]=json.loads(process.stderr)
    for i,(original,native_row) in enumerate(zip(rows["reference"],rows["native"])):
        if original!=native_row: raise ValueError(f"terrain mismatch {name} case {i}: {cases[i]} original={original} native={native_row}")
    if name.startswith("authored"):
        for i,(_,expected) in enumerate(golden_cases()):
            if rows["reference"][i]!=expected:raise ValueError(f"reference independently authored golden mismatch: {i}")
        result["independent_goldens"]=len(golden_cases())
    result["ok"]=True
    atomic_write(directory/"report.json",(json.dumps(result,indent=2)+"\n").encode())
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset",choices=PRESETS,default="debug")
    parser.add_argument("--rom",action="store_true",help="Also compare every pixel of cataloged scene; original code ROM is always required")
    args=parser.parse_args(argv)
    identity=inspect_file();verify_expected(identity)
    data=DEFAULT_ROM.read_bytes();metadata=json.loads((ROOT/"re/terrain_query.json").read_text());validate(data,metadata)
    native=verify_executable(args.preset,"wiznliz-terrain");reference=reference_executable()
    out=Path(tempfile.mkdtemp(prefix="run-",dir=approved_directory(ROOT,"local/generated/terrain-comparison")))
    report={"ok":False,"rom_sha256":identity["sha256"],"preset":args.preset,"groups":[],
            "scope":"semantic outputs/state/NZVC of six routines; no full game boot, hardware timing or full register ABI",
            "reference_build":json.loads(REFERENCE_REPORT.read_text()),"native_build":json.loads((native.parent/"provenance.json").read_text()),
            "sources":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                       ("tools/terrain_compare.py","tools/terrain_probe.py","tests/terrain_cases.py","re/terrain_query.json","re/rnc_blocks.json")}}
    try:
        rom=out/"reference-rom.bin";atomic_write(rom,data)
        scene,bank=fixture();cases=authored_cases()
        for base in (0,257):
            report["groups"].append(compare_group(out,f"authored-base-{base}",scene,bank,cases,base,native,reference,rom))
        report["reference_rejections"]=check_reference_rejections(out,reference,rom)
        if args.rom:
            scene_entry=catalog_entry("scene.companion.0001","companion_scene_v1")
            bank_entry=catalog_entry(scene_entry["structure"]["base_bank_id"])
            _,scene=read_extracted(scene_entry,MAX_SCENE_BYTES);_,bank=read_extracted(bank_entry,MAX_BANK_BYTES)
            report["groups"].append(compare_group(out,"cataloged-scene",scene,bank,real_cases(),257,native,reference,rom))
        report["total_cases"]=sum(g["cases"] for g in report["groups"])
        report["visited_pcs"]=sorted({pc for g in report["groups"] for pc in g["reference_observation"]["visited"]})
        report["ok"]=True
    except (OSError,ValueError,subprocess.SubprocessError) as exc:report["error"]=str(exc)
    finally:
        try:verify_expected(inspect_file());report["rom_unchanged"]=True
        except (OSError,ValueError) as exc:report.update(ok=False,error=str(exc),rom_unchanged=False)
        atomic_write(out/"report.json",(json.dumps(report,indent=2)+"\n").encode())
    print(json.dumps({"ok":report["ok"],"cases":report.get("total_cases"),"report":str(out/"report.json"),"error":report.get("error")},indent=2))
    return int(not report["ok"])
