"""Reproduce bounded companion selection, consumer fields and map structure."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write, parse_block, validate_decoded
from rnc_loader_probe import analyze_fields as analyze_base, direct_target, parse_disassembly, require, u32
from reset_probe import word, branch_target, dbf_target


def inspect_scene(data, max_coordinates=4096, max_patterns=65536):
    require(len(data) >= 2, "truncated scene count")
    coordinates = word(data, 0) + 1
    require(coordinates <= max_coordinates, "coordinate count exceeds limit")
    starts = 2 + coordinates * 4
    pattern_count = starts + 8
    require(len(data) >= pattern_count + 2, "truncated scene coordinates or pattern count")
    patterns = word(data, pattern_count) + 1
    require(patterns <= max_patterns, "pattern count exceeds limit")
    pattern_start = pattern_count + 2
    map_header = pattern_start + patterns * 32
    map_start = map_header + 4
    records = map_start + 8192
    require(len(data) == records + patterns * 8, "scene extent mismatch")
    shape = [word(data, map_header), word(data, map_header + 2)]
    require(shape == [128, 32], "unsupported scene shape; only the verified 128x32 layout is implemented")
    regions = {}
    for name, lo, hi in (("coordinate_count",0,2),("coordinates",2,starts),("state_starts",starts,pattern_count),
                         ("pattern_count",pattern_count,pattern_start),("patterns",pattern_start,map_header),
                         ("map_header",map_header,map_start),("map",map_start,records),("opaque_records",records,len(data))):
        regions[name] = {"range":[lo,hi], "size_bytes":hi-lo, "sha256":hashlib.sha256(data[lo:hi]).hexdigest()}
    cells = [word(data, p) for p in range(map_start, records, 2)]
    return {"format":"companion_scene_v1", "coordinate_count":coordinates,
            "additional_pattern_count":patterns, "map_word_count":len(cells), "map_shape":shape,
            "regions":regions, "maximum_relative_pattern_index":max(w & 0x7ff for w in cells),
            "unique_pattern_indices":len({w & 0x7ff for w in cells}),
            "raw_attribute_counts":dict(sorted(Counter(w & 0xf800 for w in cells).items())),
            "coordinate_purpose":None, "opaque_record_meaning":None}


def analyze_fields(data, metadata):
    analyze_base(data, json.loads((ROOT / "re/rnc_loader.json").read_text()))
    for region in metadata["regions"]:
        lo, hi = region["start"], region["end_exclusive"]
        require(0 <= lo < hi <= len(data), "invalid scene code range")
        require(hashlib.sha256(data[lo:hi]).hexdigest() == region["sha256"], "scene code hash mismatch")
    # Fixed reviewed instruction encodings; immediate words and addressing modes
    # matter here, not only the disassembler's mnemonic strings.
    expected = {
        0x18BE:"322d0026", 0x18C2:"342c0026", 0x18C6:"b441", 0x18C8:"6e02", 0x18CA:"c342",
        0x18CC:"48c1", 0x18CE:"82fc0003", 0x18D2:"342a0004", 0x18D6:"0c420008",
        0x18DA:"6602", 0x18DC:"5241", 0x18DE:"e549", 0x18E0:"22701000",
        0x3D0A:"205f", 0x3D0E:"0c805041434b", 0x3D16:"41e80004",
        0x3D1A:"43f9ffff8844", 0x3D26:"41f9ffff8844",
        0x3E14:"45f9ffff4c80", 0x3E1A:"3e18", 0x3E1C:"3018", 0x3E1E:"3218",
        0x3E20:"06400080", 0x3E24:"06410070", 0x3E28:"34c0", 0x3E2A:"34c1",
        0x3E30:"34fcffff34fcffff", 0x3E38:"4bf9ffff0690", 0x3E52:"4bf9ffff0838",
        0x3E3E:"3b58003c3b58003e", 0x3E58:"3b58003c3b58003e",
        0x3E46:"066d0080003c066d0078003e", 0x3E60:"066d0080003c066d0078003e",
        0x3E6C:"3e18", 0x3E6E:"33c7ffff4d00", 0x3ECA:"e348", 0x3ECC:"33c0ffff13a4",
        0x3F16:"41e80004", 0x3F24:"3e39ffff4d00", 0x3F2A:"22d822d8",
        0x3F34:"43f9ffff4d02", 0x3F3A:"23c9ffff4452", 0x3F40:"3c3c001f", 0x3F44:"3e3c007f",
        0x3F48:"3018", 0x3F4A:"d079ffff140e", 0x3F50:"00404000", 0x3F54:"32c0",
        0x4086:"e349", 0x4088:"2079ffff4452", 0x408E:"d0c1", 0x4096:"c3f9ffff13a4",
        0x409C:"d0c1", 0x40C0:"0c41001f", 0x40C6:"3410", 0x40EC:"d0f9ffff13a4"}
    for pc, encoded in expected.items():
        raw = bytes.fromhex(encoded)
        require(data[pc:pc + len(raw)] == raw, f"reviewed scene instruction differs at {pc:#x}")
    for pc, target in ((0x3D20,0x19462),(0x3D2C,0x3E14),(0x3F1A,0x3F34)):
        require(direct_target(data,pc) == target, "scene call target differs")
    require(branch_target(data,0x3D14) == 0x3D2C, "companion PACK bypass differs")
    for pc, register, target in ((0x3E2C,7,0x3E1C),(0x3EC4,7,0x3E94),(0x3F2E,7,0x3F2A),
                                 (0x3F56,7,0x3F48),(0x3F5A,6,0x3F44),(0x40F4,7,0x40C0)):
        require(dbf_target(data,pc) == (register,target), "scene loop differs")
    for pc in range(0x3E94,0x3EC4,6):
        require(word(data,pc) == 0x23D8 and u32(data,pc+2) == 0xFFC00000, "scene pattern transfer differs")
    require(word(data,0x3F32) == word(data,0x3F5E) == 0x4E75, "scene return boundaries differ")
    wrapper = u32(data,metadata["pointer_field"])
    require(wrapper == metadata["wrapper_offset"] and data[wrapper:wrapper+4] == b"PACK", "companion pointer/tag differs")
    header,_ = parse_block(data,wrapper+4)
    return {"runtime_observed":False,"condition":"descriptor zero; minimum signed state word at +0x26 in [0,2] selects slot zero",
            "wrapper":wrapper,"block_offset":wrapper+4,"block_end_exclusive":header.end_exclusive,
            "coordinate_addends":[128,112],"state_start_addends":[128,120],
            "map_word_count":32*128,"map_transform":"((raw_word + original_base) mod 65536) OR 0x4000",
            "map_row_stride":"header first word times two bytes; column reader corroborates",
            "reviewed_instruction_fields":len(expected)}


def capture_decoders(data, metadata, output):
    calls=[]
    def run(backend,cpu,start,fragment):
        argv=["rasm2","-a",backend,"-b","32","-e","-c",cpu,"-s",hex(start),"-D",fragment.hex()]
        p=subprocess.run(argv,capture_output=True,text=True,timeout=15)
        calls.append({"command":argv,"exit_status":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
        require(p.returncode==0,"scene disassembler failed")
        return p.stdout
    require("invalid" in run("m68k","68000",0,bytes.fromhex("49c0")),"68000 sentinel failed")
    require("extb.l" in run("m68k","68020",0,bytes.fromhex("49c0")),"68020 sentinel failed")
    rows={}
    for region in metadata["regions"]:
        lo,hi=region["start"],region["end_exclusive"]
        rows[region["id"]]=parse_disassembly(run("m68k","68000",lo,data[lo:hi]),data,lo,hi)
    checks=((0x18C6,2,"cmpw"),(0x18CE,4,"divuw"),(0x18E0,4,"moveal"),
            (0x3E20,4,"addiw"),(0x3E24,4,"addiw"),(0x3E2C,4,"dbf"),
            (0x3EC4,4,"dbf"),(0x3F16,4,"lea"),(0x3F2E,4,"dbf"),
            (0x3F40,4,"movew"),(0x3F44,4,"movew"),(0x3F50,4,"oriw"),
            (0x3F56,4,"dbf"),(0x3F5A,4,"dbf"),(0x409C,2,"addaw"),(0x40F4,4,"dbf"))
    for pc,size,mnemonic in checks:
        row,=parse_disassembly(run("m68k.gnu","m68000",pc,data[pc:pc+size]),data,pc,pc+size)
        require(row["assembly"].split()[0]==mnemonic,"independent scene instruction mismatch")
    version=subprocess.run(["rasm2","-v"],capture_output=True,text=True,check=True,timeout=10).stdout.strip()
    atomic_write(output/"decoder-evidence.json",(json.dumps({"version":version,"commands":calls,"instructions":rows,
                 "gnu_corroborated_addresses":[pc for pc,_,_ in checks]},indent=2)+"\n").encode())
    return {"version":version,"instructions":{k:len(v) for k,v in rows.items()},"gnu_corroborations":len(checks)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disassemble",action="store_true")
    parser.add_argument("--decoded-scene",type=Path)
    args=parser.parse_args(argv)
    before=inspect_file();verify_expected(before)
    data=DEFAULT_ROM.read_bytes()
    require(hashlib.sha256(data).hexdigest()==before["sha256"],"ROM changed before scene probe")
    meta=json.loads((ROOT/"re/scene_loader.json").read_text())
    require(meta["schema_version"]==1 and meta["address_space"]=="rom_file_offset","unsupported scene metadata")
    out=Path(tempfile.mkdtemp(prefix="run-",dir=approved_directory(ROOT,"local/generated/scene-probe")))
    report={"ok":False,"rom_sha256":before["sha256"],"metadata":meta}
    try:
        report["fields"]=analyze_fields(data,meta)
        if args.disassemble:report["disassembly"]=capture_decoders(data,meta,out)
        else:report["disassembly"]="not requested"
        if args.decoded_scene:
            entry,=[e for e in json.loads((ROOT/"re/rnc_blocks.json").read_text())["blocks"] if e["id"]==meta["block_id"]]
            with args.decoded_scene.open("rb") as stream: decoded=stream.read(entry["unpacked_size"]+1)
            header,_=parse_block(data,entry["file_offset"])
            identity=validate_decoded(header,decoded)
            require(identity["sha256"]==entry["decoded_sha256"],"scene digest differs from independent reference")
            structure=inspect_scene(decoded)
            for field in ("format","coordinate_count","additional_pattern_count","map_word_count"):
                require(structure[field]==entry["structure"][field],"scene catalog field mismatch")
            for name,region in structure["regions"].items():
                require(region["range"]==entry["structure"][name+"_range"],"scene catalog range mismatch")
            report["decoded"]=identity|structure
        else: report["decoded"]="not requested"
        report["ok"]=True
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:report["error"]=str(exc)
    finally:
        try:verify_expected(inspect_file());report["rom_unchanged"]=True
        except (OSError,ValueError) as exc:report.update(ok=False,rom_unchanged=False,identity_error=str(exc))
        atomic_write(out/"report.json",(json.dumps(report,indent=2)+"\n").encode())
    print(json.dumps({"ok":report["ok"],"report":str(out/"report.json"),"error":report.get("error")},indent=2))
    return int(not report["ok"])
