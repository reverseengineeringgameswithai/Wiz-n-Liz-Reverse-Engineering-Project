"""Authored --world-pool rows and a decoder for its output lines."""

# Field counts after the type of each world object (print_world_object).
WIDTHS = {2: 12, 3: 10, 4: 26, 5: 13, 6: 15, 7: 14, 8: 12, 9: 16, 10: 15, 11: 17, 12: 13, 13: 13, 14: 16, 15: 7}


def world_seed(slots=20, kinds=(5, 6), positions=((100, 100), (200, 100)), message=(0, 0, 0, 0xe000, 0, 0, 3), gates=(0, 0, 0, 0, 0, 0, 0, 1),
               world=(0, 0, 0, 0x1234, 0, 0, 0, 1, 1, 0, 352, 224)):
    """Header, free stack (bottom to top) and slot rows, tables, then 7DB8,
    gated and world rows. The top sixteen slots carry zero inheritance."""
    table = (*kinds, *(0xffff,) * (16 - len(kinds)), *(0,) * 16, *(v for xy in positions for v in xy), *(0,) * (32 - 2 * len(positions)))
    rows = [(slots, slots), tuple(range(slots)), *((9,) + (0,) * 9 if i >= slots - 16 else (0,) for i in range(slots))]
    return rows, [table, message, gates, world]


def phase(p1=(0, 0), owner=None, calls=0, messages=(None, None)):
    """One phase row: P1 tracking with mask 1023 and no P2, the owner, external
    E918 calls and per-control message updates."""
    row = [*p1, 1023, 0, 0, 0, 0, *((1, *owner) if owner else (0, 0, 0)), calls]
    for m in messages: row += (1, *m) if m else (0, 0, 0, 0)
    return tuple(row)


def world_input(phases, **kw):
    rows, rest = world_seed(**kw)
    return [(*rows[0], len(phases)), *rows[1:], *rest, *phases]


def objects(v, i, n):
    out = []
    for _ in range(n):
        kind = v[i]; out.append((kind, v[i + 1:i + 1 + WIDTHS[kind]])); i += 1 + WIDTHS[kind]
    return out, i


def state(v, i):
    """print_world_state from index i; returns (fields, next index)."""
    s = {}; n = v[i]; s['free'] = v[i + 1:i + 1 + n]; i += 1 + n
    s['random'] = v[i:i + 2]; i += 2
    s['records'] = [v[i + 4 * r:i + 4 * r + 4] for r in range(16)]; i += 64
    for name, count in (('activation', 1), ('links', 2), ('dormant', 2), ('anchor', 1), ('spell', 1), ('door', 1)):
        s[name] = [v[i + 3 * k:i + 3 * k + 3] for k in range(count)]; i += 3 * count
    s['messages'] = [v[i:i + 3], v[i + 3:i + 6]]; i += 6
    s['timer'], s['private'], s['loop'] = v[i], v[i + 1:i + 4], v[i + 4:i + 6]; i += 6
    s['pair_request'], s['spell_flags'], s['recipe'] = v[i], v[i + 1], v[i + 2:i + 5]; i += 5
    s['exit_control'], s['exit_camera'] = v[i], v[i + 1:i + 4]; i += 4
    n = v[i]; s['sounds'] = [v[i + 1 + 4 * k:i + 5 + 4 * k] for k in range(n)]; i += 1 + 4 * n
    n = v[i]; s['clears'] = v[i + 1:i + 1 + n]; i += 1 + n
    s['link_objects'], i = objects(v, i, sum(1 for l in s['links'] if l[0]))
    return s, i


def setup_line(v, members=16):
    ids = [v[2 * k:2 * k + 2] for k in range(members)]; i = 2 * members
    selection = v[i:i + 4]; s, i = state(v, i + 4); made, i = objects(v, i, members)
    assert i == len(v), 'setup line extent'
    return ids, selection, s, made


def phase_line(v):
    """Events as flat (kind, slot, generation, type, *fields), then the state."""
    events = []; i = 1
    for _ in range(v[0]):
        ((kind, fields),), j = objects(v, i + 3, 1); events.append((*v[i:i + 3], kind, *fields)); i = j
    s, i = state(v, i); assert i == len(v), 'phase line extent'
    return events, s
