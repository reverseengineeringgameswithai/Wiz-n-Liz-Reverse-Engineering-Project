"""Restricted-execution corpora for the scene between levels: the setup's
[5E86,5E8E) (63A4 and 60E6's doors), the door walks (61F6, 621A, 623C,
FAC4/FAE2) and 6024's exit test; the scene changes into it and, after it, into
the hint screen and the second level."""
import random

SLOTS = 68
# 6090: the records 6040 seeds (x, y, number, state); +A and +C are FFFF, +6 zero.
MOVIE_RECORDS = ((0x1b0, 0xa4, 0, 0), (0x1e0, 0x114, 1, 0), (0x2b0, 0x84, 2, 0), (0x320, 0xa8, 3, 0), (0x2c0, 0x10c, 4, 0),
                 (0x88, 0x54, 5, 0), (0x458, 0xa8, 6, 0), (0x400, 0x64, 7, 0), (0x128, 0x7c, 8, 0xffff))


def records(states=None, markers=None, numbers=None, rows=MOVIE_RECORDS):
    out = []
    for i, (x, y, n, s) in enumerate(rows):
        out += [x, y, numbers[i] if numbers else n, 0, states[i] if states else s, markers[i] if markers else 0xffff, 0xffff]
    return out


def doors_case(two_player=0, stage=0, ff33de=0xa5, recs=None, depth=SLOTS, order=None):
    order = list(range(SLOTS)) if order is None else order
    return (two_player, stage, ff33de, *(recs or records()), depth, *order)


def hub_doors_corpus():
    rows = [doors_case()]  # The movie's setup at 1562: every slot free, 0..67 bottom first.
    # 63A4: stage multiples of eight rewrite +8 (single player); others keep it.
    for stage in (0, 1, 7, 8, 0x10, 0x38, 0x3f, 0x40, 0xfff8, 0xffff, 0x8000):
        rows.append(doors_case(stage=stage, recs=records(states=[0x1234] * 9)))
        rows.append(doors_case(stage=stage, two_player=1, recs=records(states=[0x1234] * 9)))
    # Closed records (+8 negative) add the lock; with two players and +A
    # non-negative the partner (0217, or 0218 with X + 2 and flags 0800 when nonzero).
    for marker in (0, 1, 0x7fff, 0x8000, 0xffff):
        rows.append(doors_case(stage=1, recs=records(states=[0x8000] * 9, markers=[marker] * 9)))
        rows.append(doors_case(stage=1, two_player=0xffff, recs=records(states=[0xffff, 0, 0x8000, 1, 0xfffe, 0x7fff, 0xc000, 2, 0x8001], markers=[marker] * 9)))
    # Every number low byte 0..9 (EXT.W), with high bytes that +22 keeps.
    for high in (0, 0x100, 0xff00, 0x7f00):
        rows.append(doors_case(recs=records(numbers=[high | (i % 10) for i in range(9)])))
        rows.append(doors_case(recs=records(numbers=[high | (9 - i) for i in range(9)])))
    # Exhaustion inside every allocation: F9E2 (door, lock, partner) at FA1E,
    # F994 (numbers) at F9D0.
    for depth in range(0, 40):
        rows.append(doors_case(depth=depth))
        rows.append(doors_case(depth=depth, stage=1, two_player=1, recs=records(states=[0x8000, 0] * 4 + [0x8000], markers=[0, 1] * 4 + [0])))
    rows.append(doors_case(order=list(range(SLOTS - 1, -1, -1))))
    rng = random.Random(0x60e6611e)
    for _ in range(3000):
        order = list(range(SLOTS)); rng.shuffle(order)
        two = rng.choice((0, 0, 1, rng.randrange(65536)))
        recs = []
        for _r in range(9):
            recs += [rng.randrange(65536), rng.randrange(65536), (rng.randrange(256) << 8) | rng.randrange(10), rng.randrange(65536),
                     rng.choice((0, rng.randrange(65536))), rng.choice((0, 0xffff, rng.randrange(65536))), rng.randrange(65536)]
        rows.append(doors_case(two_player=two, stage=rng.choice((0, rng.randrange(8) * 8, rng.randrange(65536))), ff33de=rng.randrange(256), recs=recs,
                               depth=rng.choice((SLOTS, rng.randrange(SLOTS + 1))), order=order))
    return rows


DOOR = ('x', 'y', 'flags', 'mode', 'w06', 'w08', 'w0a', 'c0c', 'r0d', 'target', 'countdown', 'x_extent', 'y_extent', 'number', 'phase',
        'left', 'right', 'left_mode', 'right_mode', 'slot', 'p1x', 'p1y', 'p2x', 'p2y', 'mask', 'two_player', 'walks', 'depth',
        'p1_selector', 'p2_selector', 'requested_x', 'requested_y', 'record', 'direction', 'countdown_t', 'reload', 'level', 'curve0', 'curve1', 'curve2', 'scope',
        'p1_mode', 'p1_frame', 'p2_mode', 'p2_frame', *(f'p1_m{i}' for i in range(7)), *(f'p2_m{i}' for i in range(7)))
# Door 0 as 60E6 leaves it at 1562 (slot 67, numbers 66 and 65, 44 free
# slots), P1 away at (FF80, FF80), the hub's fade-in timer, P1's message
# fields as observed at 1742 and P2's defaults.
DOOR_DEFAULT = (0x1b0, 0xa4, 0, 0x81, 0xb0, 0xa8, 0xb7, 3, 3, 0, 0x3c, 0, 0, 0, 1, 66, 65, 0x80, 0x80, 67, 0xff80, 0xff80, 0xff80, 0xff80, 1023, 0, 1, 44,
                0, 0, 0, 0x30, 0, 0xffff, 0x0a, 1, 0, 0x1356a, 0x1356a, 0x135aa, 0, 0x87, 0x227, 0x87, 0x227,
                0xffffffff, 0xffffffff, 0, 0, 0, 0x0c, 0, 0xffffffff, 0xffffffff, 0, 0, 0, 0, 0)
assert len(DOOR) == len(DOOR_DEFAULT) == 59


def door(**changes):
    assert not changes.keys() - set(DOOR), changes.keys() - set(DOOR)
    return tuple((dict(zip(DOOR, DOOR_DEFAULT)) | changes).values())


OPEN = dict(phase=2, countdown=0xffff, x_extent=0x10, y_extent=0x18)


def hub_door_corpus():
    rows = []
    # The countdown: 61 walks to open; P1 at its tracking in 1742 (01A1, 00BC) then enters.
    for walks in (1, 60, 61, 62, 96): rows.append(door(walks=walks)); rows.append(door(walks=walks, p1x=0x1a1, p1y=0xbc))
    # AC5E's edges against the open door, with and without the X mask.
    for dx, dy in ((0, 0), (0x10, 0x18), (-0x10, -0x0c), (0x21, 0), (0x20, 0), (0, 0x24), (0, 0x25), (-0x11, 0), (0, -0x0d), (0x8000, 0)):
        tx, ty = (0x1b0 + dx) & 0xffff, (0xa4 + dy) & 0xffff
        rows.append(door(**OPEN, p1x=tx, p1y=ty)); rows.append(door(**OPEN, p1x=tx, p1y=ty, mask=0x00ff))
    # Two players: P2's contact (17298 on FF0838) only behind FF33E2; P1 first.
    rows.append(door(**OPEN, p2x=0x1b0, p2y=0xa4)); rows.append(door(**OPEN, p2x=0x1b0, p2y=0xa4, two_player=1))
    rows.append(door(**OPEN, p1x=0x1b0, p1y=0xa4, p2x=0x1b0, p2y=0xa4, two_player=1))
    # Entry details: FF4446/FF4448 at the AND edges, FF3398 from every number
    # (word-sign-extended MULU), both selectors and actors, released numbers.
    for x, y in ((0x114, 0x98), (0x113, 0x97), (0, 0), (0xffff, 0xffff), (0x11c, 0xa0)):
        rows.append(door(**OPEN, x=x, y=y, p1x=x, p1y=y))
    for number in (0, 1, 8, 9, 0x924, 0x925, 0x1000, 0xffff, 0x8000): rows.append(door(**OPEN, number=number, p1x=0x1b0, p1y=0xa4))
    rows.append(door(**OPEN, p1x=0x1b0, p1y=0xa4, left_mode=0, right_mode=0)); rows.append(door(**OPEN, p1x=0x1b0, p1y=0xa4, left=0, right=1, slot=2))
    for depth in (0, 1, 64): rows.append(door(**OPEN, p1x=0x1b0, p1y=0xa4, depth=depth))
    # The puff: FAC4's countdown, FAE2 and FAA4 at frame 0227 (one walk after entry
    # up to the release), including the frame reset after the presentation step.
    vanish = dict(phase=3, mode=0x85, w06=0x21e, w08=0x21e, w0a=0x227, c0c=3, r0d=3, target=0x227, countdown=0, x_extent=0x10, y_extent=0x18)
    for walks in (1, 2, 3, 27, 28, 29, 30, 31, 96): rows.append(door(**vanish, walks=walks))
    rows.append(door(**(vanish | dict(countdown=5)), walks=40)); rows.append(door(**(vanish | dict(c0c=1)), walks=3))
    rows.append(door(**(vanish | dict(phase=4, countdown=0xffff)), walks=40))
    # FAC4 reviving a slot FAA4 just pushed (the original's endless corruption).
    rows.append(door(**(vanish | dict(w06=0x227, c0c=1)), walks=1))
    # A closed door never changes; a seeded callback stops.
    rows.append(door(phase=0, mode=0x80, walks=96, p1x=0x1b0, p1y=0xa4)); rows.append(door(mode=0x85, w06=0, target=0, c0c=1, walks=1))
    rng = random.Random(0x61f6623c)
    for _ in range(4096):
        phase = rng.randrange(5); slot, left, right = rng.sample(range(SLOTS), 3)
        lo = rng.randrange(65536); hi = (lo + rng.randrange(12)) & 0xffff
        x, y = rng.randrange(65536), rng.randrange(65536)
        near = rng.random() < 0.5
        def track(): return ((x + rng.randrange(-24, 40)) & 0xffff, (y + rng.randrange(-16, 48)) & 0xffff) if near else (rng.randrange(65536), rng.randrange(65536))
        (p1x, p1y), (p2x, p2y) = track(), track()
        mode = rng.choice((0x80, 0x81, 0x85, 0x80 | rng.randrange(128)))
        rows.append(door(x=x, y=y, flags=rng.randrange(65536), mode=mode, w06=rng.choice((lo, hi, rng.randrange(65536))), w08=lo, w0a=hi,
                         c0c=rng.randrange(256), r0d=rng.randrange(256), target=rng.choice((lo, hi, rng.randrange(65536))),
                         countdown=rng.choice((rng.randrange(70), rng.randrange(65536))), x_extent=rng.choice((0x10, rng.randrange(65536))),
                         y_extent=rng.choice((0x18, rng.randrange(65536))), number=rng.randrange(65536), phase=phase, left=left, right=right,
                         left_mode=rng.choice((0x80, 0, rng.randrange(256))), right_mode=rng.choice((0x80, 0, rng.randrange(256))), slot=slot,
                         p1x=p1x, p1y=p1y, p2x=p2x, p2y=p2y, mask=rng.choice((1023, 0xffff, rng.randrange(65536))), two_player=rng.choice((0, 0, 1, rng.randrange(65536))),
                         walks=rng.randrange(1, 97), depth=rng.choice((rng.randrange(3), rng.randrange(65))), p1_selector=rng.randrange(65536), p2_selector=rng.randrange(65536),
                         requested_x=rng.randrange(65536), requested_y=rng.randrange(65536), record=rng.randrange(2**32), direction=rng.randrange(65536),
                         countdown_t=rng.randrange(65536), reload=rng.randrange(65536), level=rng.randrange(65536),
                         curve0=rng.choice((0x1356a, 0x135aa, 0x135ea, rng.randrange(2**32))), curve1=rng.choice((0x1356a, rng.randrange(2**32))),
                         curve2=rng.choice((0x135aa, rng.randrange(2**32))), scope=rng.randrange(65536), p1_mode=rng.randrange(256), p1_frame=rng.randrange(65536),
                         p2_mode=rng.randrange(256), p2_frame=rng.randrange(65536),
                         **{f'p{k}_m{i}': (rng.randrange(2**32) if i < 2 else rng.randrange(256) if i < 4 else rng.randrange(65536)) for k in (1, 2) for i in range(7)}))
    return rows


def hub_exit_corpus():
    rows = [(s, d) for s in (0, 1, 0x7fff, 0x8000, 0xfffe, 0xffff) for d in (0, 1, 0xffff, 0x8000, 0x7fff)]
    rng = random.Random(0x6024603e)
    rows += [(rng.choice((0xffff, rng.randrange(65536))), rng.choice((0, rng.randrange(65536)))) for _ in range(256)]
    return rows


SCENE = ('requested_x', 'requested_y', 'p2_anchor_x', 'p2_anchor_y', 'p1_slow', 'p2_slow', 'two_player', 'character', 'seed')
# The movie's change after the first level: FF4446/FF4448 = (0000, 0030) from
# 7126, P2's +A2/+A4 as left, one player, the first character.
SCENE_DEFAULT = (0, 0x30, 0, 0x30, 0, 0, 0, 0, 1)


def scene(**changes):
    assert not changes.keys() - set(SCENE), changes.keys() - set(SCENE)
    return tuple((dict(zip(SCENE, SCENE_DEFAULT)) | changes).values())


def scene_change_corpus():
    rows = [scene(), scene(requested_x=0x98, requested_y=8)]
    # Word wrap of (0114, 00B0) + the anchor; 9952's slow limits; FF33E2 and FF13E0's paths.
    for x, y in ((0xfeec, 0xff50), (0xfeeb, 0xff4f), (0xffff, 0xffff), (0x8000, 0x7fff)): rows.append(scene(requested_x=x, requested_y=y, p2_anchor_x=y, p2_anchor_y=x))
    for slow in ((1, 0), (0, 1), (0x8000, 0xffff)): rows.append(scene(p1_slow=slow[0], p2_slow=slow[1]))
    for two, character in ((1, 0), (0, 1), (0xffff, 0xffff)): rows.append(scene(two_player=two, character=character))
    rng = random.Random(0x98809952)
    for _ in range(1000):
        rows.append(scene(**{k: rng.randrange(65536) for k in SCENE[:4]}, p1_slow=rng.choice((0, rng.randrange(65536))), p2_slow=rng.choice((0, rng.randrange(65536))),
                          two_player=rng.choice((0, 0, rng.randrange(65536))), character=rng.choice((0, 1, rng.randrange(65536))), seed=rng.randrange(65536)))
    return rows


SECOND = ('p2_anchor_x', 'p2_anchor_y', 'p1_slow', 'p2_slow', 'two_player', 'character', 'range', 'state_hi', 'state_lo', 'mirror_hi', 'mirror_lo', 'seed')
# The movie's entry into the second level: P2's +A2/+A4 as the hub left them,
# one player, the first character, FF3402 = 003C and E918's state at the hub's end.
SECOND_DEFAULT = (0, 0x30, 0, 0, 0, 0, 0x3c, 0xf00e, 0xed1f, 0xf00e, 0xed1f, 1)


def second(**changes):
    assert not changes.keys() - set(SECOND), changes.keys() - set(SECOND)
    return tuple((dict(zip(SECOND, SECOND_DEFAULT)) | changes).values())


def second_level_corpus():
    rows = [second()]
    # FF3402: above 000A (signed) keeps FFFF; 0 clears FF33D8; 1..000A and negative words draw E918.
    for r in (0x0b, 0x7fff, 0x0a, 0x09, 1, 2, 0, 0x8000, 0xfffe, 0xffff): rows.append(second(range=r))
    for state in ((0, 0), (0xffff, 0xffff), (0, 1), (0x8000, 0)): rows.append(second(range=7, state_hi=state[0], state_lo=state[1]))
    for slow in ((1, 0), (0, 1), (0x8000, 0xffff)): rows.append(second(p1_slow=slow[0], p2_slow=slow[1]))
    for two, character in ((1, 0), (0, 1), (0xffff, 0xffff)): rows.append(second(two_player=two, character=character))
    for x, y in ((0xfeec, 0xff50), (0xffff, 0xffff)): rows.append(second(p2_anchor_x=x, p2_anchor_y=y))
    rng = random.Random(0x0e2a118c)
    for _ in range(1000):
        rows.append(second(**{k: rng.randrange(65536) for k in ('p2_anchor_x', 'p2_anchor_y', 'state_hi', 'state_lo', 'mirror_hi', 'mirror_lo', 'seed')},
                           p1_slow=rng.choice((0, rng.randrange(65536))), p2_slow=rng.choice((0, rng.randrange(65536))), two_player=rng.choice((0, 0, rng.randrange(65536))),
                           character=rng.choice((0, 1, rng.randrange(65536))), range=rng.choice((0x3c, 0, rng.randrange(1, 11), rng.randrange(65536)))))
    return rows


HINT = ('direction', 'countdown', 'reload', 'level', 'scope', 'hint', 'ending', 'raw', 'a', 'b', 'c', 'seed')
# The movie's hint loop after the fade-in: the timer idle at level 14, FF0F10
# counting from 00F0, no button held.
HINT_DEFAULT = (0, 0, 1, 14, 0, 0xf0, 0, 0xff, 0, 0, 0, 1)


def hint(**changes):
    assert not changes.keys() - set(HINT), changes.keys() - set(HINT)
    return tuple((dict(zip(HINT, HINT_DEFAULT)) | changes).values())


def hint_screen_corpus():
    rows = [hint(), hint(hint=0), hint(hint=1), hint(hint=0x8000), hint(hint=0xffff), hint(raw=0x7f), hint(raw=0x7f, hint=0), hint(raw=0x80),
            hint(direction=0xffff, countdown=3, level=4), hint(direction=1, raw=0x7f), hint(direction=1, hint=0),
            hint(ending=0xffff), hint(ending=1), hint(ending=0xffff, direction=1), hint(ending=0xffff, direction=0xffff, raw=0x7f)]
    for a, b, c in ((0xff, 0, 0), (0, 0xff, 0), (0, 0, 0xff), (0x0f, 0xf0, 0x11)): rows.append(hint(a=a, b=b, c=c))
    rng = random.Random(0x1959e)
    for _ in range(1000):
        rows.append(hint(direction=rng.choice((0, 0, 1, 0xffff, rng.randrange(65536))), countdown=rng.randrange(65536), reload=rng.randrange(65536),
                         level=rng.randrange(65536), scope=rng.randrange(65536), hint=rng.choice((0, 1, 0xf0, rng.randrange(65536))),
                         ending=rng.choice((0, 0, 0xffff, rng.randrange(65536))), raw=rng.randrange(256), a=rng.choice((0, 0xff, rng.randrange(256))),
                         b=rng.choice((0, 0xff, rng.randrange(256))), c=rng.choice((0, 0xff, rng.randrange(256))), seed=rng.randrange(65536)))
    return rows
