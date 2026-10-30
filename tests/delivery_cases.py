"""Authored 78EE/7910 probe walks (deliveries from carrying links, dormant-link
returns, the FF31B0 gate, exhaustion and callback stops) and later walks of the
objects a delivery creates (the 59AE sparkle and the FB06 copy)."""
import random
from pickup_hit_cases import LINK, DORMANT, EMITTER

PROBE = ('x', 'y', 'flags', 'mode', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'target', 'count')
FIELDS = (*PROBE, 'control', 'ext1e', 'ext20', 's', 'l1', 'l2', 'kind1', 'kind2', *(f'{n}_1' for n in LINK), *(f'{n}_2' for n in LINK),
          'rise_hi', 'rise_lo', 'p1x', 'p1y', 'mask', 'gate', 'present', 'p2x', 'p2y', 'depth', 'top', 'below', 'walks', 'leave1', 'leave2')
# The ordinary movie's slot-63 783A probe with P1 on it while carrying in link 53;
# the two pops at frame 823 are slots 48 and 47.
DEFAULT = (0x96, 0x106, 0, 0x80, 0x390, 0, 0, 0, 0, 0, 0, 0xffff0690, 0x38, 8, 63, 53, 52, 1, 0, *EMITTER, *DORMANT,
           0, 0, 0x4a0, 0x106, 0x3ff, 0, 0, 0, 0, 49, 48, 47, 1, 0, 0)
assert len(FIELDS) == len(DEFAULT) == 86
DELIVERED = ('kind', *PROBE, 'control', 'f22', 'f26', 'ext1e', 'ext20', 'record', 'slot', 'depth', 'walks')
SPARKLE = (0, 0x2c8, 0xa8, 0, 0x85, 0x21e, 0x21e, 0x227, 3, 3, 0x227, *(0,) * 7, 48, 20, 1)
COPY = (1, 0xa4, 0xf6, 0, 0x87, 0x227, 0x21e, 0x227, 3, 3, 0x21e, 0, 0xffff0690, 0x27e, 0x283, 0x10, 0x10, 0, 47, 20, 1)
assert len(DELIVERED) == len(SPARKLE) == len(COPY) == 21


def case(**changes):
    assert not changes.keys() - set(FIELDS), changes.keys() - set(FIELDS)
    return tuple((dict(zip(FIELDS, DEFAULT)) | changes).values())


def link(n, emitter=True, **changes):
    """Link n (1 or 2): a carrying emitter (record 0) or a dormant object."""
    return {'kind%d' % n: int(emitter), **{f'{k}_{n}': v for k, v in zip(LINK, EMITTER if emitter else DORMANT)}, **{f'{k}_{n}': v for k, v in changes.items()}}


def delivered(base, **changes):
    assert not changes.keys() - set(DELIVERED), changes.keys() - set(DELIVERED)
    return tuple((dict(zip(DELIVERED, base)) | changes).values())


def probe_corpus():
    rows = []
    # P1 delivers from its carrying link, then later walks find it dormant (7A56).
    for walks in (1, 2, 3, 9, 64):
        rows.append(case(walks=walks))
        rows.append(case(walks=walks, **link(1, False)))                      # Dormant from the start.
        rows.append(case(walks=walks, rise_lo=1)); rows.append(case(walks=walks, rise_hi=0x8000))  # FF31B0 is a long.
    # P2 behind FF33E2 (P1 away), then P1 and P2 one after the other.
    for gate in (1, 0x8000, 0xffff):
        rows.append(case(gate=gate, present=1, p2x=0x4a0, p2y=0x106, p1x=0x100, **link(1, False), **link(2, owner=0xffff0838, record=3)))
        rows.append(case(gate=gate, present=1, p2x=0x4a0, p2y=0x106, walks=6, leave1=3, **link(2, owner=0xffff0838, record=3)))
        rows.append(case(gate=gate, present=1, p2x=0x4a0, p2y=0x106, walks=6, leave1=3, leave2=5, **link(1, False), **link(2, record=5)))
    rows.append(case(gate=1, present=1, p2x=0x4a0, p2y=0x106, walks=4, **link(2, owner=0xffff0838)))   # P1 wins ties.
    # Exhaustion: no entry (F9E2 loops) or one entry (F994 loops); four entries serve two deliveries.
    for depth in (0, 1, 2, 3, 4):
        rows.append(case(depth=depth)); rows.append(case(depth=depth, gate=1, present=1, p2x=0x4a0, p2y=0x106, walks=4, leave1=2, **link(2)))
    # The probe's own callback stops; contact boundaries around the 0038/0008 extents.
    rows.append(case(mode=0x85, w06=0, c0c=1, walks=2)); rows.append(case(mode=0x81, w06=0x390, w08=0x390, w0a=0x392, c0c=2, r0d=2, walks=9))
    for mode, w06 in ((0x85, 0), (0x87, 0), (0x8d, 0xffff), (0x8f, 1), (0xfd, 0)):
        for c0c in (1, 2):rows.append(case(mode=mode, w06=w06, w08=0, w0a=3, c0c=c0c, r0d=1, walks=6, p1x=0))   # No contact: callback first.
    # Two deliveries: P1, then P2 once P1 leaves, at different walks and depths.
    for leave1 in (1, 2, 5, 31):
        for depth in (4, 5, 3, 64):rows.append(case(gate=1, present=1, p2x=0x4a0, p2y=0x106, walks=40, leave1=leave1, depth=depth, **link(2, owner=0xffff0838, record=9)))
    for dx in range(-0x40, 0x41, 4):
        for dy in (-0x16, -0x14, -0x13, -0xc, 0, 8, 9):rows.append(case(p1x=(0x96 + 0x400 + dx) & 0xffff, p1y=(0x106 + dy) & 0xffff))
    for mask in (0, 0x3ff, 0xffff):rows.append(case(mask=mask))
    # Emitter fields carried into the copy, the sparkle position and the dormant link (word wrap).
    for x, y in ((0, 0), (4, 7), (8, 8), (0xffff, 0xfffc), (0x8000, 0x7ffc)):rows.append(case(**link(1, x=x, y=y)))
    for mode in (0x80, 0x81, 0x83, 0x85, 0x8f, 0xff):rows.append(case(**link(1, mode=mode, flags=0xffff, w08=0x1234, w0a=0xfedc, count=2)))
    for record in range(16):rows.append(case(**link(1, record=record, ext1e=record, ext20=0x10 + record)))
    rng = random.Random(0x79107a56)
    for _ in range(4096):
        s, l1, l2, top, below = rng.sample(range(68), 5)
        x, y = rng.randrange(65536), rng.randrange(65536)
        ex, ey = rng.choice((0x38, rng.randrange(65536))), rng.choice((8, rng.randrange(65536)))
        # Mostly inside the inclusive AC5E window (extent + 16 in X, + 12 in Y).
        near = lambda v, e, m: (v + e - rng.randrange(-4, m + 5)) & 0xffff if rng.random() < 0.7 else rng.randrange(65536)
        gate = rng.choice((0, 0, 1, rng.randrange(65536)))
        def make(n, owner):
            if rng.random() < 0.35:return link(n, False, x=rng.randrange(65536), y=rng.randrange(65536), flags=rng.randrange(65536), owner=owner)
            return link(n, x=rng.randrange(65536), y=rng.randrange(65536), flags=rng.randrange(65536), mode=0x80 | rng.randrange(128), w06=rng.randrange(65536),
                        w08=rng.randrange(65536), w0a=rng.randrange(65536), c0c=rng.randrange(256), r0d=rng.randrange(256), target=rng.randrange(65536),
                        count=rng.choice((2, rng.randrange(65536))), cd36=rng.randrange(65536), **{f'h{i}': rng.randrange(65536) for i in range(10)}, owner=owner,
                        ext1e=rng.randrange(65536), ext20=rng.randrange(65536), record=rng.randrange(16))
        walks = rng.randrange(1, 65); w06 = rng.randrange(65536)
        r = dict(x=x, y=y, flags=rng.randrange(65536), mode=rng.choice((0x80, 0x80, 0x80, 0x81, 0x83, 0x85, 0x8b, 0x80 | rng.randrange(128))), w06=w06,
                 w08=rng.randrange(65536), w0a=rng.randrange(65536), c0c=rng.choice((rng.randrange(1, 4), rng.randrange(256))), r0d=rng.choice((rng.randrange(1, 4), rng.randrange(256))),
                 target=rng.choice((rng.randrange(65536), (w06 + rng.randrange(-3, 4)) & 0xffff)), count=rng.randrange(65536),
                 control=rng.choice((0xffff0690, rng.randrange(2**32))), ext1e=ex, ext20=ey, s=s, l1=l1, l2=l2, **make(1, 0xffff0690), **make(2, 0xffff0838),
                 rise_hi=rng.choice((0, 0, 0, 0, rng.randrange(65536))), rise_lo=rng.choice((0, 0, 0, 0, rng.randrange(65536))),
                 p1x=near(x, ex, ex + 16), p1y=near(y, ey, ey + 12), mask=rng.choice((0xffff, 0xffff, 0x3ff, rng.randrange(65536))), gate=gate, present=int(bool(gate)),
                 p2x=near(x, ex, ex + 16) if gate else 0, p2y=near(y, ey, ey + 12) if gate else 0, depth=rng.choice((rng.randrange(5), rng.randrange(65))), top=top, below=below,
                 walks=walks, leave1=rng.choice((0, 0, rng.randrange(65), rng.randrange(1, 8))), leave2=rng.choice((0, 0, rng.randrange(65))))
        rows.append(case(**r))
    return rows


def delivered_corpus():
    rows = []
    # The movie's sparkle and copy from birth: the sparkle releases and the copy
    # reaches 79B6 on their 30th walk.
    for walks in (1, 2, 3, 27, 28, 29, 30, 31, 64):
        rows.append(delivered(SPARKLE, walks=walks)); rows.append(delivered(COPY, walks=walks))
        rows.append(delivered(SPARKLE, walks=walks, depth=0)); rows.append(delivered(COPY, walks=walks, c0c=1))
    rng = random.Random(0x59ae79b6)
    for _ in range(4096):
        kind = rng.randrange(2); base = COPY if kind else SPARKLE
        # Frames near 021E..0227 with short cadences reach the callback often.
        frame = lambda: rng.choice((rng.randrange(65536), rng.randrange(0x21c, 0x229)))
        r = dict(x=rng.randrange(65536), y=rng.randrange(65536), flags=rng.randrange(65536), mode=rng.choice((0x80 | rng.randrange(128), 0x85, 0x87, 0x8d, 0x8f, 0x84 | rng.randrange(4))),
                 w06=frame(), w08=frame(), w0a=frame(), c0c=rng.choice((rng.randrange(1, 4), rng.randrange(256))), r0d=rng.choice((rng.randrange(1, 4), rng.randrange(256))),
                 target=frame(), slot=rng.randrange(68), depth=rng.randrange(65), walks=rng.randrange(1, 65))
        if kind:r |= dict(count=rng.randrange(65536), control=rng.choice((0xffff0690, 0xffff0838, rng.randrange(2**32))), f22=rng.randrange(65536), f26=rng.randrange(65536),
                          ext1e=rng.randrange(65536), ext20=rng.randrange(65536), record=rng.randrange(16))
        rows.append(delivered(base, **r))
    return rows


INGREDIENT = ('x', 'y', 'flags', 'mode', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'target', 'count', 'control', 'f22', 'f26', 'ext1e', 'ext20', 'record',
              'slot', 'target_slot', 'holder', 'entry', 'activation', 'message', 'priority', 'row', 'tile_hi', 'tile_lo', 'loop', 'timer', 'depth', 'walks')
# The ordinary movie's copy (slot 47) on its 30th walk at frame 853: FF31B4 is
# slot 67, its record (1) names link 53; MIX THOSE FRUIT is no longer held.
LAST_WALK = (0xa4, 0xf6, 0, 0x87, 0x21e, 0x21e, 0x227, 1, 3, 0x21e, 0, 0xffff0690, 0x284, 0x289, 0x10, 0x10, 1,
             47, 67, 53, 1, 0, 0, 0, 0, 0, 0xe000, 2, 0, 20, 1)
assert len(INGREDIENT) == len(LAST_WALK) == 31


def ingredient(**changes):
    assert not changes.keys() - set(INGREDIENT), changes.keys() - set(INGREDIENT)
    return tuple((dict(zip(INGREDIENT, LAST_WALK)) | changes).values())


def ingredient_corpus():
    rows = []
    # The last walk: the callback, D20E through CB72 (shown unless +53 holds a
    # higher signed priority), 7AD6 into FF31B4, the release and 7A88 on the
    # released copy; earlier walks only animate.
    for priority in (0, 1, 2, 0x64, 0x7f, 0x80, 0xff):
        for message in range(5):rows.append(ingredient(priority=priority, message=message))
    for counter, walks in ((1, 1), (2, 1), (2, 2), (3, 3), (3, 64)):rows.append(ingredient(c0c=counter, walks=walks))
    rows.append(ingredient(w06=0x227, c0c=3, walks=30)); rows.append(ingredient(w06=0x227, c0c=3, walks=29))
    # The table residue: cadence from the carried count, the frames, wrap at the position adds.
    for count in (0, 1, 2, 3, 0xffff):rows.append(ingredient(count=count))
    for x, y in ((0xfff8, 0xfffc), (0xfff7, 0xfffb), (0x8000, 0x7fff)):rows.append(ingredient(x=x, y=y))
    for loop in (0, 1, 0xffff):rows.append(ingredient(loop=loop, timer=0x1234))
    for row, hi, lo in ((1, 0, 0xe000), (0x1ff, 0x1234, 0xfff0), (0xffff, 0xffff, 0xffff)):rows.append(ingredient(row=row, tile_hi=hi, tile_lo=lo))
    rows.append(ingredient(control=0xffff0838)); rows.append(ingredient(control=0xffff0838, priority=0x64, message=1))
    # FF31AC set: 79B6's second-ingredient branch stops (not native).
    rows.append(ingredient(activation=1)); rows.append(ingredient(activation=1, c0c=3, walks=2))
    for record in range(16):rows.append(ingredient(record=record, entry=15 - record))
    rng = random.Random(0x7ad67b22)
    for _ in range(4096):
        s, t, h = rng.sample(range(68), 3); target = rng.randrange(65536)
        frame = lambda: rng.choice((rng.randrange(65536), (target + rng.randrange(-3, 4)) & 0xffff))
        rows.append(ingredient(x=rng.randrange(65536), y=rng.randrange(65536), flags=rng.randrange(65536), mode=rng.choice((0x87, 0x85, 0x8d, 0x84 | rng.randrange(4), 0x80 | rng.randrange(128))),
                               w06=frame(), w08=frame(), w0a=frame(), c0c=rng.choice((rng.randrange(1, 4), rng.randrange(256))), r0d=rng.choice((rng.randrange(1, 4), rng.randrange(256))),
                               target=target, count=rng.choice((0, 2, rng.randrange(65536))), control=rng.choice((0xffff0690, 0xffff0838)), f22=rng.randrange(65536), f26=rng.randrange(65536),
                               ext1e=rng.randrange(65536), ext20=rng.randrange(65536), record=rng.randrange(16), slot=s, target_slot=t, holder=h, entry=rng.randrange(16),
                               activation=int(rng.random() < 0.1), message=rng.randrange(5), priority=rng.choice((0, 1, rng.randrange(256))), row=rng.randrange(65536),
                               tile_hi=rng.randrange(65536), tile_lo=rng.randrange(65536), loop=rng.choice((0, 1, 2, rng.randrange(8))), timer=rng.randrange(65536),
                               depth=rng.randrange(65), walks=rng.randrange(1, 65)))
    return rows
