"""Validate this vault's deliberately small frontmatter and link conventions."""

from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE_FIELDS = {"id", "type", "status"}
FINDING_FIELDS = {"rom_id", "address_space", "confidence", "task"}
CONFIDENCE = {"confirmed", "probable", "hypothesis", "unknown", "rejected"}


def prose_only(text: str) -> str:
    """Remove fenced and inline code so example links/IDs aren't treated as facts."""
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1] and not match[2].strip():
                fence = None
            continue
        if match:
            fence = (match[1][0], len(match[1]))
            continue
        lines.append(line)
    return re.sub(r"(`+).*?\1", "", "\n".join(lines), flags=re.DOTALL)


def frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("unterminated YAML frontmatter") from exc
    fields = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([a-z_]+):\s*(.*)", line)
        if not match:
            raise ValueError("use flat key: scalar or JSON-array frontmatter")
        key, value = match.groups()
        if key in fields:
            raise ValueError(f"duplicate frontmatter key {key}")
        if value.startswith(("[", '"')) or value == "null":
            value = json.loads(value)
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        fields[key] = value
    return fields, "\n".join(lines[end + 1:])


def check_vault(vault: Path = ROOT / "vault") -> dict:
    errors = []
    notes = {}
    ids = {}
    for path in sorted(vault.rglob("*.md")):
        rel = path.relative_to(vault)
        if any(part.startswith(".") for part in rel.parts):
            continue
        name = rel.with_suffix("").as_posix()
        try:
            fields, body = frontmatter(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            errors.append(f"{name}: {exc}")
            continue
        notes[name] = (fields, prose_only(body))
        for field in BASE_FIELDS:
            if not isinstance(fields.get(field), str) or not fields[field]:
                errors.append(f"{name}: missing/non-string required field {field}")
        note_id = fields.get("id")
        if isinstance(note_id, str):
            if note_id in ids:
                errors.append(f"{name}: duplicate stable ID {note_id} (also {ids[note_id]})")
            ids[note_id] = name
        if fields.get("type") == "task":
            if not isinstance(fields.get("deliverable"), str) or not fields["deliverable"]:
                errors.append(f"{name}: task needs deliverable")
            acceptance = fields.get("acceptance")
            if not isinstance(acceptance, list) or not acceptance or not all(isinstance(v, str) and v for v in acceptance):
                errors.append(f"{name}: task needs nonempty acceptance string array")
            if not rel.stem.startswith(str(note_id) + "-"):
                errors.append(f"{name}: task filename must start with its stable ID plus '-' ")
        if fields.get("type") == "finding":
            for field in FINDING_FIELDS:
                if not isinstance(fields.get(field), str) or not fields[field]:
                    errors.append(f"{name}: finding needs {field}")
            if fields.get("confidence") not in CONFIDENCE:
                errors.append(f"{name}: invalid confidence")

    for name, (fields, body) in notes.items():
        targets = []
        for match in re.finditer(r"\[\[([^\]\n]+)\]\]", body):
            target = match[1].split("|", 1)[0]
            target, _, anchor = target.partition("#")
            target = target.removesuffix(".md") or name
            targets.append(target)
            if target not in notes:
                errors.append(f"{name}: broken/non-vault-relative link [[{match[1]}]]")
            elif anchor:
                target_body = notes[target][1]
                headings = {m[1].strip().casefold() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", target_body, re.MULTILINE)}
                if anchor.startswith("^"):
                    exists = re.search(r"(?:^|\s)" + re.escape(anchor) + r"\s*$", target_body, re.MULTILINE)
                else:
                    exists = anchor.casefold() in headings
                if not exists:
                    errors.append(f"{name}: missing link anchor [[{match[1]}]]")
        if "task" in fields:
            task = fields["task"]
            task_name = ids.get(task) if isinstance(task, str) else None
            if not task_name or notes[task_name][0].get("type") != "task":
                errors.append(f"{name}: task field does not identify a task: {task!r}")
            elif task_name not in targets:
                errors.append(f"{name}: task field {task} requires matching explicit task link")
        for target in targets:
            if target.startswith("07_Tasks/") and target in notes and notes[target][0].get("type") != "task":
                errors.append(f"{name}: task link points to non-task {target}")
    if not notes:
        errors.append("vault contains no valid notes")
    return {"notes_checked": len(notes), "errors": sorted(errors), "ok": not errors}
