"""Authored 6BD6/6C00 pickup walks: contacts with dormant and carrying links, the
vanish/release, swap and re-dress callbacks, family and callback stops."""
import random

PICKUP = ('x', 'y', 'flags', 'mode', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'target', 'count')
LINK = (*PICKUP, 'cd36', *(f'h{i}' for i in range(10)), 'owner', 'ext1e', 'ext20', 'record')
FIELDS = (*PICKUP, 'control', 'ext1e', 'ext20', 'record', 's', 'l1', 'l2', 'kind1', 'kind2',
          *(f'{n}_1' for n in LINK), *(f'{n}_2' for n in LINK), *(f'kind_{k}' for k in range(16)), *(f'entry_{r}' for r in range(16)),
          'p1x', 'p1y', 'mask', 'gate', 'present', 'p2x', 'p2y', 'depth', 'walks', 'leave', 'phase')
DORMANT = (0x1234, 0x0567, 0, 0, 0x21d, 9, 11, 13, 15, 900, 3, 0, *(0,) * 10, 0xffff0690, 0, 0, 0)
EMITTER = (0x2d0, 0xb0, 0, 0x81, 0x27e, 0x27e, 0x283, 2, 5, 911, 0, 1, *(0xff80 + i for i in range(10)), 0xffff0690, 0x10, 0x10, 0)
# Pickup 54 of the ordinary movie (kind 6 at 0370,00B0, record 1), P1 on it.
DEFAULT = (0x370, 0xb0, 0, 0x81, 0x284, 0x284, 0x289, 5, 5, 900, 0, 0xffff0690, 0x10, 0x10, 1, 54, 53, 52, 0, 0,
           *DORMANT, *DORMANT, 5, 6, *(0xffff,) * 14, 0, 1, *(16,) * 14, 0x370, 0xb0, 0x3ff, 0, 0, 0, 0, 4, 1, 0, 0)
assert len(FIELDS) == len(DEFAULT) == 115


def case(**changes):
    assert not changes.keys() - set(FIELDS), changes.keys() - set(FIELDS)
    return tuple((dict(zip(FIELDS, DEFAULT)) | changes).values())


def emitter(n, **changes):
    """Link n (1 or 2) as a carrying emitter holding record 0 (entry 0) unless changed."""
    return {'kind%d' % n: 1, **{f'{k}_{n}': v for k, v in zip(LINK, EMITTER)}, **{f'{k}_{n}': v for k, v in changes.items()}}


def corpus():
    rows = []
    # Dormant P1 link: conversion, then the vanish animation to the FAA4 release.
    for walks in (1, 2, 3, 4, 10, 26, 27, 28, 29, 30, 40, 64):
        rows.append(case(walks=walks))
        rows.append(case(walks=walks, depth=0, c0c=1, r0d=1, w06=0x288))
    # A carrying P1 emitter: exchange, vanish, 5964 return, 6CF4 re-dress (and,
    # with P1 still there, the next contact in the same walk), at every stage.
    for walks in (1, 2, 27, 28, 29, 30, 31, 32, 48, 49, 50, 51, 52, 53, 64):
        for count, kind in ((0, 5), (2, 6), (7, 0x20d), (2, 0x205), (1, 0x1fd), (0, 0x7fff), (0, 0x8000)):
            rows.append(case(walks=walks, **emitter(1, count=count), kind_0=kind))
        rows.append(case(walks=walks, p1x=0x100, p1y=0x30, **emitter(1)))   # No contact at all.
    # The re-dressed pickup moves X back by 8 and is tested in the same walk:
    # with P1 still there it is hit again; after P1 leaves it stays collectable.
    for x in (0x358, 0x360, 0x368, 0x370, 0x378, 0x380, 0x388):
        rows.append(case(walks=64, p1x=x, **emitter(1)))
        for leave in (1, 2, 30, 50, 51, 52):rows.append(case(walks=64, p1x=x, leave=leave, **emitter(1)))
    rows.append(case(walks=64, leave=1, gate=1, present=1, p2x=0x370, p2y=0xb0, p1x=0x100, **emitter(2, record=2, owner=0xffff0838), entry_2=2))
    # P2 behind FF33E2 (P1 away): its own link, owner FF0838; P1 wins ties.
    for gate in (1, 0x8000, 0xffff):
        for second in (False, True):
            r = dict(gate=gate, present=1, p2x=0x370, p2y=0xb0, p1x=0x100, owner_2=0xffff0838, walks=64)
            if second: r |= emitter(2, record=2, owner=0xffff0838) | dict(entry_2=2)
            rows.append(case(**r))
        rows.append(case(gate=gate, present=1, p2x=0x370, p2y=0xb0, walks=3))
    # Contact boundaries in X (masked) and Y around the 0010/0010 extents.
    for dx in range(-0x14, 0x15, 2):
        for dy in (-0x10, -0xc, -0xb, 0, 0x10, 0x11):
            rows.append(case(p1x=(0x370 + dx) & 0xffff, p1y=(0xb0 + dy) & 0xffff, walks=1))
    for mask in (0, 0x3ff, 0xffff):rows.append(case(mask=mask, p1x=0x770, walks=1))
    # Family frames on +08 stop at 6E32/6E5E/6E8A; the sound request comes first.
    for w08 in (0x20d, 0x205, 0x1fd, 0x20c, 0x206, 0x1fe):
        rows.append(case(w08=w08, walks=2))
        rows.append(case(w08=w08, walks=2, **emitter(1)))
    # A collectable presentation callback stops at its seeded target.
    rows.append(case(mode=0x85, w06=900, c0c=1, walks=1)); rows.append(case(mode=0x85, w06=899, c0c=1, walks=3, p1x=0))
    # Non-animating and reverse/bouncing pickups (an inactive pickup is a released
    # slot, not an occupied seed); records, kinds and free depths.
    for mode in (0x80, 0x83, 0x8b, 0x8f):rows.append(case(mode=mode, walks=8))
    for record in range(16):
        r = dict(record=record, **{f'entry_{k}': (15 - k if k in (record, (record + 1) % 16) else 16) for k in range(16)})
        rows.append(case(walks=30, **r))
        rows.append(case(walks=64, **r, **emitter(1, record=(record + 1) % 16)))
    # Seeded later phases (as the movie evidence seeds them): each callback, on
    # time and early, with and without P1 on the re-dressed pickup.
    for phase, mode, words, target in ((1, 0x85, (0x226, 0x21e, 0x227), 0x227), (2, 0x85, (0x227, 0x21e, 0x227), 0x227), (3, 0x87, (0x21e, 0x227, 0x21e), 0x21e)):
        for counter in (1, 2, 3):
            for walks, leave in ((1, 0), (2, 0), (5, 0), (64, 0), (64, 1)):
                rows.append(case(phase=phase, mode=mode, w06=words[0], w08=words[1], w0a=words[2], target=target, c0c=counter, r0d=3, walks=walks, leave=leave,
                                 **(emitter(1) if phase > 1 else {})))
    # After a 6D22 conversion the vanishing pickup still points at the record
    # that now names the emitter (as pickup 54 does after frame 780).
    for walks in (1, 3, 30, 31, 32):rows.append(case(phase=1, mode=0x85, w06=0x21e, w08=0x21e, w0a=0x227, target=0x227, c0c=3, r0d=3, walks=walks, **emitter(1, record=1)))
    rng = random.Random(0x6c006d22)
    for _ in range(6144):
        s, l1, l2 = rng.sample(range(68), 3); rp, re1, re2 = rng.sample(range(16), 3)
        entries = [rng.randrange(16) if rng.random() < 0.5 else 16 for _k in range(16)]
        for r in (rp, re1, re2):entries[r] = rng.randrange(16)
        kinds = [rng.choice((rng.randrange(14), 0x20d, 0x205, 0x1fd, 0xffff, rng.randrange(65536))) for _k in range(16)]
        x, y = rng.randrange(65536), rng.randrange(65536)
        near = lambda v: (v + rng.randrange(-0x18, 0x19)) & 0xffff
        gate = rng.choice((0, 0, 1, rng.randrange(65536)))
        def link(n, record, owner):
            if rng.random() < 0.5:return {'kind%d' % n: 0, **{f'{k}_{n}': v for k, v in zip(LINK, DORMANT)}}
            return emitter(n, x=rng.randrange(65536), y=rng.randrange(65536), mode=rng.choice((0x81, 0x85, 0x83, 0x80)), w06=rng.randrange(65536),
                           w08=rng.randrange(65536), w0a=rng.randrange(65536), c0c=rng.randrange(256), r0d=rng.randrange(256), target=rng.randrange(65536),
                           count=rng.choice((2, rng.randrange(65536))), cd36=rng.randrange(65536), **{f'h{i}': rng.randrange(65536) for i in range(10)}, owner=owner,
                           ext1e=rng.randrange(65536), ext20=rng.randrange(65536), record=record)
        r = dict(x=x, y=y, flags=rng.randrange(65536), mode=rng.choice((0x81, 0x81, 0x85, 0x83, 0x80, 0x8b)), w06=rng.randrange(65536),
                 w08=rng.choice((rng.randrange(65536), 0x260 + 6 * rng.randrange(14))), w0a=rng.randrange(65536), c0c=rng.randrange(256), r0d=rng.randrange(256),
                 target=rng.randrange(65536), count=rng.choice((2, rng.randrange(65536))), control=rng.choice((0xffff0690, rng.randrange(2**32))),
                 ext1e=rng.choice((0x10, rng.randrange(65536))), ext20=rng.choice((0x10, rng.randrange(65536))), record=rp, s=s, l1=l1, l2=l2,
                 **link(1, re1, 0xffff0690), **link(2, re2, 0xffff0838), **{f'kind_{k}': v for k, v in enumerate(kinds)},
                 **{f'entry_{k}': v for k, v in enumerate(entries)}, p1x=near(x), p1y=near(y), mask=rng.choice((0x3ff, 0xffff, rng.randrange(65536))),
                 gate=gate, present=int(bool(gate)), p2x=near(x) if gate else 0, p2y=near(y) if gate else 0, depth=rng.randrange(65), walks=rng.randrange(1, 65), leave=rng.choice((0, 0, rng.randrange(65))), phase=rng.choice((0, 0, 0, 1, 2, 3)))
        rows.append(case(**r))
    return rows
