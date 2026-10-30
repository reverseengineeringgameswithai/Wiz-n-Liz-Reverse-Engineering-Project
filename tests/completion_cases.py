"""Authored walks of the spell's completion: the FF31C0 anchor's 7B42/7B58/7B8A
handlers with 13294, 7B58's completion (D269, 7E18, recipe 8652, 7F08, 6F02,
95EE, 1324E), 7F08's sparkle and 6F02's door and sign."""
import random

ANCHOR = ('x', 'y', 'flags', 'mode', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'target', 'countdown', 'control', 'slot', 'walks', 'phase',
          'direction', 'tcount', 'reload', 'level', 'scope')
# The ordinary anchor (slot 58) a few walks before 13294; the fade-in left level 14.
ANCHOR_DEFAULT = (164, 270, 0x800, 0x81, 919, 916, 921, 5, 5, 0, 3, 0xffff0690, 58, 1, 0, 0, 0, 0, 14, 0)
assert len(ANCHOR) == len(ANCHOR_DEFAULT) == 20


def anchor(**changes):
    assert not changes.keys() - set(ANCHOR), changes.keys() - set(ANCHOR)
    return tuple((dict(zip(ANCHOR, ANCHOR_DEFAULT)) | changes).values())


def frames(rng, prefix=''):
    """A presentation cycle that never meets its target (target 0, frames >= 1)."""
    lo = rng.randrange(1, 65000); hi = lo + rng.randrange(0, 12)
    return {prefix + 'w08': lo, prefix + 'w0a': hi, prefix + 'w06': rng.randrange(lo, hi + 1), prefix + 'target': 0}


def anchor_corpus():
    rows = []
    # 7B42 reaches 13294 on walk countdown + 1; 7B58 then waits on the new fade.
    for countdown in (0, 1, 2, 3, 0x12c, 0x7fff, 0x8000, 0x8001, 0xffff):
        for walks in sorted({1, 2, (countdown + 1) & 0x1ff or 1, countdown & 0x1ff or 1, 512}): rows.append(anchor(countdown=countdown, walks=walks))
    for level in (0, 2, 14, 0x8000, 0xffff): rows.append(anchor(countdown=0, walks=3, level=level, scope=0x1234))
    # 7B58 and 7B8A wait while FF0B90 is nonzero, then complete (stop) or reveal.
    for phase in (1, 2):
        for direction in (0, 1, 0xffff, 0x8000):
            for walks in (1, 2, 7): rows.append(anchor(phase=phase, direction=direction, walks=walks, tcount=3, reload=1, level=6))
    for mode in (0, 0x7f, 0x80, 0x85, 0x87, 0xff): rows.append(anchor(mode=mode, walks=7, countdown=2))
    rng = random.Random(0x7b427b8a)
    for _ in range(3072):
        rows.append(anchor(x=rng.randrange(65536), y=rng.randrange(65536), flags=rng.randrange(65536), mode=rng.randrange(256), c0c=rng.randrange(256),
                           r0d=rng.randrange(256), countdown=rng.choice((rng.randrange(8), rng.randrange(65536))), control=rng.choice((0xffff0690, 0xffff0838, rng.randrange(2**32))),
                           slot=rng.randrange(68), walks=rng.randrange(1, 513), phase=rng.randrange(3), direction=rng.choice((0, 0, 1, 0xffff, rng.randrange(65536))),
                           tcount=rng.randrange(65536), reload=rng.randrange(65536), level=rng.randrange(65536), scope=rng.randrange(65536), **frames(rng)))
    return rows


TABLE = ('x', 'y', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'countdown', 'toggle', 'delta', 'cursor', 'mode', 'flags', 'target', 'control')


def table(**changes):
    base = dict(x=0xac, y=0xfa, w06=0x284, w08=0x284, w0a=0x289, c0c=5, r0d=5, countdown=0x0e, toggle=0, delta=0xffff, cursor=0, mode=0x81, flags=0, target=0x21e, control=0xffff0690)
    return tuple((base | changes).values())


COMPLETION = ('x', 'y', 'flags', 'mode', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'target', 'countdown', 'control', 'slot', 'slot_a', 'slot_b',
              *(f'a_{k}' for k in TABLE), *(f'b_{k}' for k in TABLE), 'record_a', 'entry_a', 'record_b', 'entry_b',
              'flags_a8', 'pair_request', 'two_player', 'gate_a6', 'gate_a4', 'origin_x', 'origin_y', 'message', 'priority', 'row', 'tile_hi', 'tile_lo', 'depth',
              'direction', 'tcount', 'reload', 'level', 'scope')
# The ordinary completion at 1447: the anchor (slot 58), FF31AC slot 67 (fruit
# 6), FF31B0 slot 66 (fruit 5), FF0690 +3C/+3E (352, 224), the fade-out done.
COMPLETION_DEFAULT = (164, 270, 0x800, 0x81, 919, 916, 921, 5, 5, 0, 0xffff, 0xffff0690, 58, 67, 66,
                      *table(), *table(x=0xb4, w06=0x27e, w08=0x27e, w0a=0x283, delta=1), 1, 1, 0, 0,
                      0, 0, 0, 0, 0, 352, 224, 0, 0, 12, 0, 0xe000, 20, 0, 0, 0, 0, 0)
assert len(COMPLETION) == len(COMPLETION_DEFAULT) == 67


def completion(**changes):
    assert not changes.keys() - set(COMPLETION), changes.keys() - set(COMPLETION)
    return tuple((dict(zip(COMPLETION, COMPLETION_DEFAULT)) | changes).values())


def fruit_frame(fruit): return 0x260 + 6 * fruit


def completion_corpus():
    rows = []
    # Every fruit pair (and some out of the table): 8652 for {5, 6}, another
    # recipe's effect stops, no entry branches to 9288.
    for a in range(15):
        for b in range(15): rows.append(completion(a_w08=fruit_frame(a), b_w08=fruit_frame(b)))
    for w08 in (0x25f, 0x260, 0x265, 0x266, 0x284, 0x289, 0xffff): rows.append(completion(a_w08=w08))
    # Each path out of the recipe and each allocation exhausting.
    for changes in (dict(flags_a8=1), dict(pair_request=1), dict(pair_request=0xffff), dict(two_player=1), dict(gate_a6=1), dict(gate_a4=1), dict(gate_a4=1, gate_a6=1)):
        rows.append(completion(**changes))
    for depth in range(5): rows.append(completion(depth=depth))
    # Waiting on the fade, the message refused by a held priority, P2's control.
    for direction in (1, 0xffff, 0x8000): rows.append(completion(direction=direction))
    for priority in (0, 1, 2, 0x64, 0x80, 0xff): rows.append(completion(priority=priority, message=1))
    rows.append(completion(control=0xffff0838)); rows.append(completion(control=0xffff0838, priority=0x64))
    for record_a, entry_a, record_b, entry_b in ((0, 0, 1, 1), (15, 15, 0, 15), (3, 7, 4, 7)): rows.append(completion(record_a=record_a, entry_a=entry_a, record_b=record_b, entry_b=entry_b))
    for origin in ((0, 0), (0xfff8, 0xffe8), (0x8000, 0x7ff0)): rows.append(completion(origin_x=origin[0], origin_y=origin[1]))
    rng = random.Random(0x7e187f08)
    obj = lambda: table(**{k: (rng.randrange(24) if k == 'cursor' else 0x80 | rng.randrange(128) if k == 'mode' else rng.randrange(256) if k in ('c0c', 'r0d')
                               else rng.randrange(2**32) if k == 'control' else rng.randrange(65536)) for k in TABLE})
    for _ in range(3072):
        s, sa, sb = rng.sample(range(68), 3); ra, rb = rng.sample(range(16), 2)
        fa, fb = rng.choice(((6, 5), (5, 6))) if rng.random() < 0.6 else (rng.randrange(16), rng.randrange(16))
        a, b = list(obj()), list(obj()); a[3] = fruit_frame(fa) if rng.random() < 0.9 else rng.randrange(65536); b[3] = fruit_frame(fb)
        rows.append(completion(x=rng.randrange(65536), y=rng.randrange(65536), flags=rng.randrange(65536), mode=0x80 | rng.randrange(128), c0c=rng.randrange(256), r0d=rng.randrange(256),
                               countdown=rng.randrange(65536), control=rng.choice((0xffff0690, 0xffff0838)), slot=s, slot_a=sa, slot_b=sb,
                               **{f'a_{k}': v for k, v in zip(TABLE, a)}, **{f'b_{k}': v for k, v in zip(TABLE, b)},
                               record_a=ra, entry_a=rng.randrange(16), record_b=rb, entry_b=rng.randrange(16),
                               flags_a8=rng.choice((0, 0, 0, 0, 1)), pair_request=rng.choice((0, 0, 0, 0, 0xffff)), two_player=rng.choice((0, 0, 0, 0, 1)),
                               gate_a6=rng.choice((0, 0, 0, 0, 1)), gate_a4=rng.choice((0, 0, 0, 0, 1)), origin_x=rng.randrange(65536), origin_y=rng.randrange(65536),
                               message=rng.randrange(5), priority=rng.choice((0, 1, rng.randrange(256))), row=rng.randrange(65536), tile_hi=rng.randrange(65536),
                               tile_lo=rng.randrange(65536), depth=rng.choice((rng.randrange(4), rng.randrange(66))), direction=rng.choice((0, 0, 0, rng.randrange(65536))),
                               tcount=rng.randrange(65536), reload=rng.randrange(65536), level=rng.randrange(65536), scope=rng.randrange(65536), **frames(rng)))
    return rows


SPARKLE = ('x', 'y', 'flags', 'mode', 'frame', 'countdown', 'x_extent', 'y_extent', 'random_hi', 'random_lo', 'slot', 'depth', 'walks')
SPARKLE_DEFAULT = (352, 252, 0, 0x80, 0x21d, 0x40, 0x10, 0x10, 0x1234, 0x5678, 40, 20, 1)


def sparkle(**changes):
    assert not changes.keys() - set(SPARKLE), changes.keys() - set(SPARKLE)
    return tuple((dict(zip(SPARKLE, SPARKLE_DEFAULT)) | changes).values())


def sparkle_corpus():
    rows = []
    # The whole life (64 walks, release on the 65th, inactive afterwards).
    for walks in (1, 2, 64, 65, 66, 96): rows.append(sparkle(walks=walks, depth=60))
    for countdown in (0, 1, 0x7fff, 0x8000, 0xffff): rows.append(sparkle(countdown=countdown, walks=3))
    for depth in (0, 1, 2): rows.append(sparkle(depth=depth, walks=40))
    rng = random.Random(0x7f6a5a9a)
    for _ in range(4096):
        rows.append(sparkle(x=rng.randrange(65536), y=rng.randrange(65536), flags=rng.randrange(65536), mode=0x80 | rng.randrange(128), frame=rng.randrange(65536),
                            countdown=rng.choice((rng.randrange(70), rng.randrange(65536))), x_extent=rng.randrange(65536), y_extent=rng.randrange(65536),
                            random_hi=rng.randrange(65536), random_lo=rng.randrange(65536), slot=rng.randrange(68), depth=rng.choice((rng.randrange(4), rng.randrange(68))),
                            walks=rng.randrange(1, 97)))
    return rows


DOOR = ('x', 'y', 'flags', 'mode', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'target', 'countdown', 'x_extent', 'y_extent', 'phase',
        'sx', 'sy', 'sflags', 'smode', 'sframe', 'cursor', 'bobbing', 'slot', 'sign_slot', 'track_x', 'track_y', 'mask', 'two_player', 'frame3a', 'walks',
        'link_slot', 'link_mode', 'anchor_slot', 'selector', 'camera_x', 'camera_y', 'exit_control', 'actor_mode', 'actor_frame', 'depth')
# The ordinary door just made at 1447 (6F02 with +3C/+3E = 352, 224): the sign
# below it in the pool, P1 away from it, the dormant +1A2 link (53), the FF31C0
# anchor (58), twenty free slots.
DOOR_DEFAULT = (344, 248, 0, 0x80, 0x21d, 0, 0, 0, 0, 0, 0x1e, 0, 0, 0, 0, 0, 0, 0x80, 0x21d, 0, 0, 48, 47, 1402, 283, 1023, 0, 0x25, 1,
                53, 0, 58, 0, 0x1234, 0x5678, 0, 0x81, 0x913, 20)
assert len(DOOR) == len(DOOR_DEFAULT) == 39


def door(**changes):
    assert not changes.keys() - set(DOOR), changes.keys() - set(DOOR)
    return tuple((dict(zip(DOOR, DOOR_DEFAULT)) | changes).values())


def door_corpus():
    rows = []
    # The countdown (31 walks to 5964), the 30-walk puff to 6FCA, then 705C.
    for walks in (1, 30, 31, 32, 60, 61, 62, 63, 96): rows.append(door(walks=walks))
    # Entering once open (7082: the sign released, the door vanishing, the camera
    # words, P1's actor and +1A6), with and without the X mask; two players
    # (contact: no camera words; a miss stops at 7072); an active link (70FE).
    for tx, ty in ((352, 240), (344, 232), (352 + 16 + 16, 240), (352 + 33, 240), (352, 240 + 32 + 12), (352, 240 + 45), (0x8000, 240)):
        rows.append(door(walks=96, track_x=tx, track_y=ty)); rows.append(door(walks=96, track_x=tx, track_y=ty, mask=0x00ff))
    rows.append(door(walks=96, two_player=1)); rows.append(door(walks=30, two_player=1)); rows.append(door(walks=96, two_player=1, track_x=352, track_y=240))
    for link_mode in (0x80, 0x81, 0xff): rows.append(door(walks=96, track_x=352, track_y=240, link_mode=link_mode))
    for depth in (0, 1, 64): rows.append(door(walks=96, track_x=352, track_y=240, depth=depth))
    for x, y in ((0x10c, 0xe0), (0x10b, 0xdf), (0, 0), (0xffff, 0xffff)):
        rows.append(door(phase=2, x=x, y=y, mode=0x81, w06=0xb0, w08=0xa8, w0a=0xb7, c0c=3, r0d=3, target=0x21e, countdown=0xffff, x_extent=16, y_extent=32,
                         track_x=(x + 8) & 0xffff, track_y=(y + 8) & 0xffff, walks=1))
    # The sign already raised, at every cursor; the door already appearing or open.
    for cursor in range(14): rows.append(door(bobbing=1, cursor=cursor, sx=352, sy=204, sframe=0xd2, walks=3))
    rows.append(door(slot=40, sign_slot=41, walks=96)); rows.append(door(slot=40, sign_slot=41, walks=96, track_x=352, track_y=240))
    rows.append(door(phase=1, mode=0x87, w06=0x227, w08=0x21e, w0a=0x227, c0c=3, r0d=3, target=0x21e, countdown=0xffff, walks=40))
    rows.append(door(phase=2, x=352, y=240, mode=0x81, w06=0xb0, w08=0xa8, w0a=0xb7, c0c=3, r0d=3, target=0x21e, countdown=0xffff, x_extent=16, y_extent=32, walks=20))
    rng = random.Random(0x6fb6705c)
    for _ in range(4096):
        phase = rng.randrange(3); s, g, l, a = rng.sample(range(68), 4)
        lo = rng.randrange(65536); hi = (lo + rng.randrange(12)) & 0xffff
        x, y = rng.randrange(65536), rng.randrange(65536)
        near = rng.random() < 0.4
        rows.append(door(x=x, y=y, flags=rng.randrange(65536), mode=0x80 | rng.randrange(128), w06=rng.choice((lo, rng.randrange(65536))),
                         w08=lo, w0a=hi, c0c=rng.randrange(256), r0d=rng.randrange(256), target=rng.choice((lo, hi, rng.randrange(65536))),
                         countdown=rng.choice((rng.randrange(40), rng.randrange(65536))), x_extent=rng.choice((16, rng.randrange(65536))), y_extent=rng.choice((32, rng.randrange(65536))),
                         phase=phase, sx=rng.randrange(65536), sy=rng.randrange(65536), sflags=rng.randrange(65536), smode=0x80 | rng.randrange(128), sframe=rng.randrange(65536),
                         cursor=rng.randrange(14), bobbing=rng.randrange(2), slot=s, sign_slot=g,
                         track_x=(x + rng.randrange(-24, 40)) & 0xffff if near else rng.randrange(65536), track_y=(y + rng.randrange(-24, 56)) & 0xffff if near else rng.randrange(65536),
                         mask=rng.choice((1023, 0xffff, rng.randrange(65536))), two_player=rng.choice((0, 0, 0, 1)), frame3a=rng.randrange(65536), walks=rng.randrange(1, 97),
                         link_slot=l, link_mode=rng.choice((0, 0, 0, 0x80 | rng.randrange(128))), anchor_slot=a, selector=rng.randrange(65536), camera_x=rng.randrange(65536),
                         camera_y=rng.randrange(65536), exit_control=rng.choice((0, rng.randrange(2**32))), actor_mode=rng.randrange(256), actor_frame=rng.randrange(65536),
                         depth=rng.choice((rng.randrange(3), rng.randrange(65)))))
    return rows
