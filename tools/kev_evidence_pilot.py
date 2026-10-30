"""Bounded, local-only diagnostic of Kev against already documented evidence.

Prepare requests without networking, or use --run with the existing localhost
server. Labels and rationales remain evaluator-side. This is not a native-game
test, a proof of unknown behavior, or a general accuracy benchmark.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import tempfile
import time
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "re/kev_evidence_pilot.json"
ENDPOINT = "http://127.0.0.1:8021"
CRITERIA = {
    "supported": "The supplied evidence establishes the claim.",
    "contradicted": "The supplied evidence establishes that the claim is false.",
    "insufficient": "The supplied evidence cannot establish whether the claim is true or false.",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def evidence(packet: dict) -> str:
    text = (ROOT / packet["source"]).read_text(encoding="utf-8")
    chunks = []
    for section in packet["sections"]:
        begin = text.index(section["start"])
        end = text.index(section["end"], begin) if section["end"] else len(text)
        chunks.append(text[begin:end].strip())
    result = "\n\n".join(chunks)
    if digest(result.encode()) != packet["evidence_sha256"]:
        raise ValueError(f"Evidence changed: {packet['id']}; review labels before rerunning")
    return result


def request_for(packet: dict, state: str, order: list[str]) -> dict:
    return {
        "model": "kev-latest",
        "state": state,
        "questions": {
            case["id"]: {
                "type": "choice",
                "instructions": (
                    "Classify this claim using only the supplied evidence. "
                    "Respect stated scope and distinguish original behavior from "
                    "native implementation. Missing evidence is not evidence of falsehood. "
                    "Claim: " + case["claim"]
                ),
                "criteria": {key: CRITERIA[key] for key in order},
            }
            for case in packet["cases"]
        },
    }


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Local pilot refuses HTTP redirects")


def call(route: str, payload=None) -> dict:
    # No environment proxies or redirects: research text stays on this host.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(
        ENDPOINT + route,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with opener.open(request, timeout=180) as response:
        body = json.load(response)
    return {"wall_ms": round((time.perf_counter() - started) * 1000, 2), "body": body}


def rows_for(packet: dict, variant: str, response: dict) -> list[dict]:
    body = response["body"]
    if body.get("truncated", False):
        raise ValueError("Truncated evidence is not a valid pilot result")
    answers = body["answers"]
    if set(answers) != {case["id"] for case in packet["cases"]}:
        raise ValueError("Response question IDs do not match request")
    rows = []
    for case in packet["cases"]:
        answer = answers[case["id"]]
        ps = answer["probabilities"]
        if (answer["type"] != "choice" or set(ps) != set(CRITERIA)
                or any(not math.isfinite(p) or not 0 <= p <= 1 for p in ps.values())
                or abs(sum(ps.values()) - 1) > 1e-5
                or answer["choice"] != max(ps, key=ps.get)):
            raise ValueError("Malformed probability response")
        rows.append({"packet": packet["id"], "id": case["id"], "variant": variant,
                     "expected": case["expected"], "choice": answer["choice"],
                     "correct": answer["choice"] == case["expected"],
                     "top_probability": max(ps.values()), "probabilities": ps})
    return rows


def summarize(rows: list[dict], timings: list[dict]) -> dict:
    by_variant = {}
    baseline = {r["id"]: r for r in rows if r["variant"] == "order0"}
    for variant in dict.fromkeys(r["variant"] for r in rows):
        group = [r for r in rows if r["variant"] == variant]
        by_variant[variant] = {
            "correct": sum(r["correct"] for r in group), "total": len(group),
            "confusion": {label: dict(Counter(r["choice"] for r in group
                                              if r["expected"] == label))
                          for label in CRITERIA},
            "false_supported": [r["id"] for r in group
                                if r["choice"] == "supported" and r["expected"] != "supported"],
            "errors": [r for r in group if not r["correct"]],
            "flips_from_order0": [r["id"] for r in group
                                  if r["choice"] != baseline[r["id"]]["choice"]],
            "max_probability_delta_from_order0": max(
                abs(r["probabilities"][label] - baseline[r["id"]]["probabilities"][label])
                for r in group for label in CRITERIA),
        }
    return {
        "unique_claims": len(baseline), "variants": by_variant,
        "latency_ms": {variant: {
            "wall_median": statistics.median(t["wall_ms"] for t in timings if t["variant"] == variant),
            "server_median": statistics.median(t["server_ms"] for t in timings if t["variant"] == variant),
        } for variant in by_variant},
        "limits": ["Hand-authored diagnostic with known labels, not a random or held-out workload sample.",
                   "Repeated option orders and separate requests are not independent test cases.",
                   "No model probability is a proof or a calibrated WizNLiz correctness probability.",
                   "Timing measures this already-running server; not model load or end-to-end research time."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="submit to the existing localhost:8021 server")
    args = parser.parse_args()
    suite = json.loads(SUITE.read_text(encoding="utf-8"))
    # Resolve and verify every evidence slice before creating requests or contacting Kev.
    packets = [(p, evidence(p)) for p in suite["packets"]]
    ids = [c["id"] for p, _ in packets for c in p["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case ID")
    if any(c["expected"] not in CRITERIA for p, _ in packets for c in p["cases"]):
        raise ValueError("Unknown expected label")
    parent = ROOT / "local/generated/kev-evidence-pilot"
    parent.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix="run-", dir=parent))
    write_json(out / "suite.json", suite)
    write_json(out / "provenance.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "endpoint": ENDPOINT,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "suite_sha256": digest(SUITE.read_bytes()), "script_sha256": digest(Path(__file__).read_bytes()),
        "mode": "run" if args.run else "prepare_only",
    })
    rows, timings = [], []
    if args.run:
        models = call("/v1/models")
        write_json(out / "models-before.json", models)
        model = next(m for m in models["body"]["models"] if m["name"] == "kev-latest")
        if model["run"] != suite["expected_model_run"] or model["truncate_states"]:
            raise ValueError("Unexpected model or enabled truncation; review before running")
    for packet, state in packets:
        keys = list(CRITERIA)
        for i in range(4):
            variant = f"order{i}" if i < 3 else "separate"
            order = keys[i:] + keys[:i] if i < 3 else keys
            request = request_for(packet, state, order)
            stem = f"{packet['id']}-{variant}"
            write_json(out / f"{stem}-request.json", request)
            if not args.run:
                continue
            route = "/v1/systemone/separate" if i == 3 else "/v1/systemone"
            response = call(route, request)
            write_json(out / f"{stem}-response.json", response)
            result = rows_for(packet, variant, response)
            rows.extend(result)
            timings.append({"packet": packet["id"], "variant": variant,
                            "wall_ms": response["wall_ms"], "server_ms": response["body"]["latency_ms"]})
            print(f"{stem}: {sum(r['correct'] for r in result)}/{len(result)} "
                  f"({response['wall_ms']:.0f} ms)", flush=True)
    if args.run:
        write_json(out / "models-after.json", call("/v1/models"))
        write_json(out / "rows.json", rows)
        write_json(out / "timings.json", timings)
        write_json(out / "summary.json", summarize(rows, timings))
    print(out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
