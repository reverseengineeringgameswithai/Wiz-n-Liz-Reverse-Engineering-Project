"""Authored second-ingredient copy walks (callback79B6 with FF31AC set and 7AD6's
FF31B8/FF31B0/anchor path) and 7CC8 producer calls."""
import random

SECOND = ('x', 'y', 'flags', 'mode', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'target', 'count', 'control', 'f22', 'f26', 'ext1e', 'ext20', 'record',
          'slot', 'first_slot', 'target_slot', 'anchor_slot', 'holder', 'entry', 'delta',
          'ax', 'ay', 'aflags', 'amode', 'aw06', 'aw08', 'aw0a', 'ac0c', 'ar0d', 'atarget', 'acount', 'acontrol',
          'message', 'priority', 'row', 'tile_hi', 'tile_lo', 'loop', 'timer', 'depth', 'walks')
# The ordinary movie's second copy (slot 48) on its last walk: FF31AC is slot 67
# (+32 FFFF), FF31B8 slot 66, the FF31C0 anchor slot 58 (the 7B9C second
# member), the record (0) names link 53; FF31BC 0, FF31BE 0050.
SECOND_DEFAULT = (0xa4, 0xf6, 0, 0x87, 0x21e, 0x21e, 0x227, 1, 3, 0x21e, 0, 0xffff0690, 0x27e, 0x283, 0x10, 0x10, 0,
                  48, 67, 66, 58, 53, 0, 0xffff,
                  164, 270, 0x800, 0x81, 919, 916, 921, 5, 5, 0, 0, 0,
                  0, 0, 12, 0, 0xe000, 0, 0x50, 20, 1)
assert len(SECOND) == len(SECOND_DEFAULT) == 45


def second(**changes):
    assert not changes.keys() - set(SECOND), changes.keys() - set(SECOND)
    return tuple((dict(zip(SECOND, SECOND_DEFAULT)) | changes).values())


def anchor_frames(rng):
    """A presentation cycle that never meets its target (target 0, frames >= 1)."""
    lo = rng.randrange(1, 65000); hi = lo + rng.randrange(0, 12)
    return dict(aw08=lo, aw0a=hi, aw06=rng.randrange(lo, hi + 1), atarget=0)


def second_corpus():
    rows = []
    # The last walk: the callback, D22F through CB72 (shown unless +53 holds a
    # higher signed priority), the negated +32, 7AD6 into FF31B8 with FF31B0
    # and the anchor, the release and 7A88 on the released copy.
    for priority in (0, 1, 2, 0x64, 0x7f, 0x80, 0xff):
        for message in range(5): rows.append(second(priority=priority, message=message))
    for delta in (0, 1, 2, 0x7fff, 0x8000, 0x8001, 0xfffe, 0xffff): rows.append(second(delta=delta))
    for counter, walks in ((1, 1), (2, 1), (2, 2), (3, 3), (3, 64)): rows.append(second(c0c=counter, walks=walks))
    rows.append(second(w06=0x227, c0c=3, walks=30)); rows.append(second(w06=0x227, c0c=3, walks=29))
    for count in (0, 1, 2, 3, 0xffff): rows.append(second(count=count))
    for x, y in ((0xfff8, 0xfffc), (0xfff7, 0xfffb), (0x8000, 0x7fff)): rows.append(second(x=x, y=y))
    for loop in (0, 1, 2, 7, 40): rows.append(second(loop=loop, timer=0x1234))
    for row, hi, lo in ((1, 0, 0xe000), (0x1ff, 0x1234, 0xfff0), (0xffff, 0xffff, 0xffff)): rows.append(second(row=row, tile_hi=hi, tile_lo=lo))
    rows.append(second(control=0xffff0838)); rows.append(second(control=0xffff0838, priority=0x64, message=1))
    for amode in (0, 0x80, 0x81, 0x85): rows.append(second(amode=amode, acount=0x1234, acontrol=0xffff0838))
    for record in range(16): rows.append(second(record=record, entry=15 - record))
    rows.append(second(slot=0, first_slot=67, target_slot=1, anchor_slot=2, holder=3)); rows.append(second(slot=67, first_slot=0, target_slot=66, anchor_slot=65, holder=64))
    rng = random.Random(0x7a007ae6)
    for _ in range(4096):
        s, a, t, c, h = rng.sample(range(68), 5); target = rng.randrange(65536)
        frame = lambda: rng.choice((rng.randrange(65536), (target + rng.randrange(-3, 4)) & 0xffff))
        rows.append(second(x=rng.randrange(65536), y=rng.randrange(65536), flags=rng.randrange(65536), mode=rng.choice((0x87, 0x85, 0x8d, 0x84 | rng.randrange(4), 0x80 | rng.randrange(128))),
                           w06=frame(), w08=frame(), w0a=frame(), c0c=rng.choice((rng.randrange(1, 4), rng.randrange(256))), r0d=rng.choice((rng.randrange(1, 4), rng.randrange(256))),
                           target=target, count=rng.choice((0, 2, rng.randrange(65536))), control=rng.choice((0xffff0690, 0xffff0838)), f22=rng.randrange(65536), f26=rng.randrange(65536),
                           ext1e=rng.randrange(65536), ext20=rng.randrange(65536), record=rng.randrange(16), slot=s, first_slot=a, target_slot=t, anchor_slot=c, holder=h,
                           entry=rng.randrange(16), delta=rng.choice((0, 1, 0xffff, 0x8000, rng.randrange(65536))),
                           ax=rng.randrange(65536), ay=rng.randrange(65536), aflags=rng.randrange(65536), amode=rng.randrange(256), ac0c=rng.randrange(256), ar0d=rng.randrange(256),
                           acount=rng.randrange(65536), acontrol=rng.choice((0, 0xffff0690, rng.randrange(2**32))), **anchor_frames(rng),
                           message=rng.randrange(5), priority=rng.choice((0, 1, rng.randrange(256))), row=rng.randrange(65536), tile_hi=rng.randrange(65536), tile_lo=rng.randrange(65536),
                           loop=rng.randrange(48), timer=rng.randrange(65536), depth=rng.randrange(65), walks=rng.randrange(1, 65)))
    return rows


OBJECT = ('x', 'y', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'countdown', 'toggle', 'delta', 'cursor', 'mode', 'flags', 'target', 'control')


def table(**changes):
    base = dict(x=0xac, y=0xfa, w06=0x284, w08=0x284, w0a=0x289, c0c=5, r0d=5, countdown=0x0e, toggle=0, delta=0xffff, cursor=0, mode=0x81, flags=0, target=0x21e, control=0xffff0690)
    return tuple((base | changes).values())


def mix(spell=1, activation=1, timer=0x28, loop=0, slots=(67, 66), first=None, second=None):
    return (spell, activation, timer, loop, *slots, *(first or table()), *(second or table(delta=1, x=0xb4)))


def mix_corpus():
    rows = []
    # Both presences, the countdown boundary, FF31BC wrap and every exchange order.
    for spell in (0, 1):
        for activation in (0, 1):
            for timer in (0, 1, 0x28, 0x7fff, 0x8000, 0xffff): rows.append(mix(spell, activation, timer))
    for loop in (0, 1, 0x7fff, 0xffff): rows.append(mix(timer=0, loop=loop))
    for slots in ((67, 66), (66, 67), (0, 67), (67, 0)):
        for delta in (0, 1, 0x7fff, 0x8000, 0xffff): rows.append(mix(slots=slots, first=table(delta=delta)))
    rng = random.Random(0x7cc87cea)
    obj = lambda: table(**{k: (rng.randrange(24) if k == 'cursor' else 0x80 | rng.randrange(128) if k == 'mode' else rng.randrange(256) if k in ('c0c', 'r0d')
                               else rng.randrange(2**32) if k == 'control' else rng.choice((0, 1, 0x8000, 0xffff, rng.randrange(65536))) if k == 'delta' else rng.randrange(65536)) for k in OBJECT})
    for _ in range(4096):
        rows.append(mix(rng.choice((0, 1, 1)), rng.choice((0, 1, 1)), rng.choice((0, 1, rng.randrange(65536))), rng.randrange(65536), tuple(rng.sample(range(68), 2)), obj(), obj()))
    return rows
