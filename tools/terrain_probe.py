"""Validate exact terrain routine boundaries/calls and capture original-68000 decode."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write
from rnc_loader_probe import direct_target, require
from reset_probe import word, branch_target


def routine_cfg(data, instructions, allowed_calls):
    by_address={row["address"]:row for row in instructions}
    work=[instructions[0]["address"]];seen=set();edges=[];returns=[]
    while work:
        pc=work.pop()
        if pc in seen:continue
        require(pc in by_address,"terrain branch leaves routine/instruction boundary")
        seen.add(pc);op=word(data,pc)
        if op==0x4e75:returns.append(pc);continue
        successors=[pc+by_address[pc]["size"]]
        target=direct_target(data,pc)
        if target is not None:
            require(allowed_calls.get(pc)==target,"unreviewed terrain call/transfer")
        elif op&0xf000==0x6000:
            if op&0xff00==0x6000:successors=[]
            successors.append(branch_target(data,pc))
        else:require(not 0x4e80<=op<=0x4eff,"indirect terrain transfer")
        for successor in successors:edges.append([pc,successor]);work.append(successor)
    require(len(seen)==len(instructions) and returns,"unexplained terrain instructions")
    return {"reachable_instructions":len(seen),"returns":sorted(returns),"edges":edges}


def validate(data, metadata):
    require(metadata["schema_version"] == 1 and metadata["address_space"] == "rom_file_offset", "terrain metadata schema")
    require(hashlib.sha256(data).hexdigest() == metadata["rom_sha256"], "terrain ROM identity mismatch")
    for region in metadata["regions"]:
        lo, hi = region["start"], region["end_exclusive"]
        require(0 <= lo < hi <= len(data), "terrain range invalid")
        require(hashlib.sha256(data[lo:hi]).hexdigest() == region["sha256"], "terrain code range changed")
        require(data[hi-2:hi] == b"\x4e\x75", "terrain routine must end at RTS")
    for call in metadata["validated_calls"]:
        require(direct_target(data, call["pc"]) == call["target"], "terrain caller target changed")
    return {"ranges":len(metadata["regions"]),"calls":len(metadata["validated_calls"]),"dynamic_execution":False}


def disassemble(data, metadata, output):
    # Independent selected GNU decoding, with the same documented four-byte
    # limitation as the existing probes; no generated bulk assembly is tracked.
    import subprocess
    from rnc_loader_probe import parse_disassembly
    commands=[]; rows={};cfg={}
    for cpu, expected in (("68000","invalid"),("68020","extb.l")):
        command=["rasm2","-a","m68k","-b","32","-e","-c",cpu,"-D","49c0"]
        p=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
        require(expected in p.stdout,"terrain decoder CPU sentinel failed")
        commands.append({"argv":command,"stdout":p.stdout,"stderr":p.stderr,"exit_status":p.returncode})
    def run(backend,cpu,lo,hi):
        command=["rasm2","-a",backend,"-b","32","-e","-c",cpu,"-s",hex(lo),"-D",data[lo:hi].hex()]
        p=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
        commands.append({"argv":command,"stdout":p.stdout,"stderr":p.stderr,"exit_status":p.returncode})
        return parse_disassembly(p.stdout,data,lo,hi)
    for region in metadata["regions"]:
        instructions=run("m68k","68000",region["start"],region["end_exclusive"])
        require(len(instructions)==region["instruction_count"],"terrain instruction count differs")
        rows[region["id"]]=instructions
        cfg[region["id"]]=routine_cfg(data,instructions,{c["pc"]:c["target"] for c in metadata["validated_calls"]})
    checks=[(0x99d4,4,"subiw"),(0x99dc,2,"bmis"),(0x99f2,2,"andw"),(0x9a08,2,"addaw"),
            (0x9a0a,2,"addaw"),(0x9a22,2,"lslw"),(0x9a54,4,"eoriw"),(0x9a36,4,"moveb"),
            (0x9aa2,2,"cmpb"),(0x9aa6,4,"addqw"),(0x9b58,2,"cmpb"),(0x9b80,2,"cmpb")]
    for pc,size,mnemonic in checks:
        row,=run("m68k.gnu","m68000",pc,pc+size)
        require(row["assembly"].split()[0]==mnemonic,f"GNU terrain corroboration failed at {pc:#x}")
    version=subprocess.check_output(["rasm2","-v"],text=True,timeout=10).strip()
    atomic_write(output/"decoder-evidence.json",(json.dumps({"version":version,"commands":commands,"instructions":rows,"cfg":cfg},indent=2)+"\n").encode())
    return {"version":version,"instructions":sum(len(r) for r in rows.values()),"gnu_checks":len(checks)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--disassemble",action="store_true")
    args=parser.parse_args(argv)
    verify_expected(inspect_file());data=DEFAULT_ROM.read_bytes()
    metadata=json.loads((ROOT/"re/terrain_query.json").read_text())
    out=Path(tempfile.mkdtemp(prefix="run-",dir=approved_directory(ROOT,"local/generated/terrain-probe")))
    report={"ok":False,"metadata":metadata}
    try:
        report["static"]=validate(data,metadata)
        if args.disassemble: report["decoders"]=disassemble(data,metadata,out)
        report["ok"]=True
    finally:
        verify_expected(inspect_file());report["rom_unchanged"]=True
        atomic_write(out/"report.json",(json.dumps(report,indent=2)+"\n").encode())
    print(json.dumps({"ok":True,"report":str(out/"report.json")},indent=2));return 0
