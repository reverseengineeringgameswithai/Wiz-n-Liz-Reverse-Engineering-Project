"""Ordinary-recording F9E2/6EC8/6EDC/7772/783A/7B9C/7C26/6A94/6EB6/7DB8/6EF0/7FBE/7154/735E/7568 evidence, the [6886,68D4) setup, group provenance, retained continuity to frame 1066, the 6C00 pickup hits with every later walk of the hit pickups and the 7910 probe hits with every later walk of the objects a delivery creates, through the copy's 79B6/7AD6 first-ingredient path and the FF31B4 table object it makes, and the whole retained world: the setup and every later object loop natively in one pool (genesis_world_pool)."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write
from native_build import PRESETS, verify_executable
from genesis_actor_capture import save, require, block, be
from genesis_actions_capture import check_worker
from genesis_effect_session import fixture_reader
from genesis_movie_actor_capture import MOVIE_SHA256, INPUT_SHA256
from genesis_return_only_evidence import return_only_fields, validate_write as validate_return_only_write
from genesis_mixed_session import private_fields
from genesis_collision_evidence import collision_fields
from rnc_loader_probe import parse_disassembly
from terrain_cases import encode_cases

END, SWITCH = 1066, 630
BASE, LIMIT, STRIDE = 0xffff1b50, 0xffff3008, 78
SLOTS = (LIMIT - BASE) // STRIDE
ANCHOR = 0xff31c0
# Logical FF31B4 / FF31B8: the 6EC8 / 6EDC dormant objects (an 8-byte range).
DORMANT = 0xff31b4
# Logical +1A2 links of the P1/P2 control records (6EB6) and their writer.
LINKS_AT = (0xff0832, 0xff09da)
SOURCES = ('tools/genesis_pair_initializer.py', 'tools/genesis_return_only_evidence.py', 'tools/genesis_mixed_session.py', 'tools/genesis_actor_capture.py',
           'tools/genesis_actions_capture.py', 'tools/genesis_effect_session.py', 'tools/genesis_collision_evidence.py', 're/pair_initializer_step.json',
           're/visibility_pair_step.json', 're/rising_pair_step.json', 're/collision_quad_step.json', 're/setup_prefix_step.json', 're/setup_tail_step.json',
           're/setup_message_step.json', 're/setup_pairs_step.json', 're/pickup_hit_step.json', 're/delivery_step.json', 're/ingredient_step.json',
           'tools/genesis_world_pool.py')
# [6886,68A4): LEA FF0690,A5 then six BSRs; each next PC is its push's write PC.
PREFIX = (0x6886, 0x688c, 0x6890, 0x6894, 0x6898, 0x689c, 0x68a0, 0x68a4)
# [68A4,68BC): BSR 6A94, LEA FF0690,A5, BSR 6EB6, LEA FF0838,A5, BSR 6EB6.
TAIL = (0x68a4, 0x68a8, 0x68ae, 0x68b2, 0x68b8, 0x68bc)
# [68BC,68C4): BSR 7DB8, BSR 6EF0. Marks inside 7DB8/CB72/CB9A/6EF0: entry,
# the two store paths, CB72's refusal, CB9A, the returns and 6EF0's open path.
MESSAGE = (0x68bc, 0x68c0, 0x68c4)
MESSAGE_PCS = (0x7db8, 0x7dec, 0x7e08, 0x7dfa, 0x7e16, 0xcb72, 0xcb8c, 0xcb98, 0xcb9a, 0xcc16, 0x6ef0, 0x6f00, 0x6f02)
MESSAGE_CODE = ((0x7db8, 0x7e18), (0xcb72, 0xcc18))
MESSAGES = {0xd28c: 1, 0xd2a2: 2, 0xffffffff: 0}
# [68C4,68D4): BSR 7FBE, BSR 7154, BSR 735E, BSR 7568. Per initializer: entry,
# the closed gate's RTS and the open path's first instruction; FF3172..FF3178
# are their gate words and FF0874 the P2 control's +3C/+3E (7FBE's origin).
GATED = (0x68c4, 0x68c8, 0x68cc, 0x68d0, 0x68d4)
GATED_PCS = ((0x7fbe, 0x7fc6, 0x7fc8), (0x7154, 0x715c, 0x715e), (0x735e, 0x7366, 0x7368), (0x7568, 0x7570, 0x7572))
GATED_CODE = ((0x7fbe, 0x8040), (0x7154, 0x71ce), (0x735e, 0x73d8), (0x7568, 0x75e2))
CALLERS = (*PREFIX, *TAIL[1:], *MESSAGE[1:], *GATED[1:], 0x1ec50, 0x1ec54, 0x1ec58, 0x20216, 0x2021a, 0x21420, 0x21424, 0x21d8e, 0x21d92)
OTHER = (0xf994, 0xf9a8, 0xf9ce, 0xfa30, 0xfa52, 0xfa78, 0xfaa4, 0xfaba, 0xfa8c, 0xfaa2, 0xf872, 0xf940, 0xf992)
WALK = (0x69a4, 0x69aa, 0x69c2, 0x69ce)
# 78EE service entry and its unsupported overlap-hit target, traced during walks.
SERVICE, HIT = 0x78ee, 0x7910
# Unsupported 7AD6 (reached from callback79B6) and its FB06 object copy, which
# can overwrite a dormant FF31B4/FF31B8 object; traced during walks.
ACTIVATE, COPY = (0x7ad6, 0x7b22), 0xfb06
# 6AF0 pickups: 6BD6 service and its unsupported hit target 6C00 (which also
# copies the pickup into the control's +1A2 object through 6D22/FB06).
PICKUP_SERVICE, PICKUP_HIT = 0x6bd6, 0x6c00
# Inside 6C00: after the link load (A4 = link), the exchange and 6D22 returns,
# the FCB32 request (mailbox FF0A9E..FF0AA4) and the 6CDA/6CF4 callbacks.
PICKUP_LINKED, PICKUP_DONE, SOUND, PICKUP_CALLBACKS = 0x6c48, (0x6cd8, 0x6d8a), 0xfcb32, (0x6cda, 0x6cf4)
# Inside 7910: after the link load (A4 = the link), after 59AE (A6 = the
# sparkle), after the final CLR.B (A6 = the dormant link, A4 = the copy), the
# FF31B0 and dormant-link returns, and the copy's later 79B6 callback.
PROBE_LINKED, PROBE_SPARKLE, PROBE_DONE, PROBE_RETURNS, DELIVERED_CALLBACK = 0x7922, 0x7976, 0x79b2, (0x79b4, 0x7a56), 0x79b6
# 6D8C emitter: 5A9A particle allocation (A6 = the emitter) and E918, whose
# every call is attributed by A6.
PARTICLE, RANDOM = 0x5a9a, 0xe918
EMITTER_PCS = (PARTICLE, RANDOM)
# Traced 6A94/6AF0 marks: entry, return, 6AF0 entry, after F9E2, and 6B3E,
# after 6AF0's last store and before it restores A6 (at 6B42 A6 is the caller's).
PICKUP_TRACE = (0x6a94, 0x6aee, 0x6af0, 0x6afa, 0x6b3e)
LINK_PCS = (0x6eb6, 0x6ebc, 0x6ec0, 0x6ec6)
F9E2_PCS = (0xf9e2, 0xf9e4, 0xf9ea, 0xf9ec, 0xf9ee, 0xf9f4, 0xf9f6, 0xf9fc, 0xfa04, 0xfa0c, 0xfa10, 0xfa14, 0xfa1a, 0xfa1c)
LOOP_PCS = (0xfa1e, 0xfa26, 0xfa2e)
FIRST_PCS = (0x7ba2, 0x7ba8, 0x7bae, 0x7bb4, 0x7bba, 0x7bc0, 0x7bc6, 0x7bcc, 0x7bd2, 0x7bda)
SECOND_PCS = (0x7be0, 0x7be6, 0x7bec, 0x7bf2, 0x7bf8, 0x7bfe, 0x7c04, 0x7c0a, 0x7c10, 0x7c18, 0x7c1e, 0x7c24)
VIS_FIRST_PCS = (0x7c2c, 0x7c32, 0x7c38, 0x7c3e, 0x7c44, 0x7c4a, 0x7c50, 0x7c56, 0x7c5c, 0x7c64)
VIS_SECOND_PCS = (0x7c6a, 0x7c70, 0x7c76, 0x7c7c, 0x7c82, 0x7c88, 0x7c8e, 0x7c94, 0x7c9a, 0x7ca2)
RISING_FIRST_PCS = (0x7778, 0x777e, 0x7782, 0x7788, 0x778e, 0x7794, 0x779a, 0x77a0, 0x77a6, 0x77ac, 0x77b4, 0x77b8, 0x77ba)
RISING_SECOND_PCS = (0x77c0, 0x77c4, 0x77ca, 0x77d0, 0x77d6, 0x77dc, 0x77e2, 0x77e8, 0x77ee, 0x77f4, 0x77fa, 0x7802, 0x7806)
# 783A: probe stores then LEA (A6),A4; three return-only members copy from A4.
QUAD_MEMBER_PCS = ((0x7840, 0x7846, 0x784a, 0x7850, 0x7856, 0x785c, 0x7864, 0x786c, 0x7872, 0x7878, 0x787a),
                   (0x7880, 0x7886, 0x788c, 0x7892, 0x7898, 0x789e), (0x78a4, 0x78aa, 0x78b0, 0x78b6, 0x78bc, 0x78c2),
                   (0x78c8, 0x78ce, 0x78d4, 0x78da, 0x78e0, 0x78e6, 0x78ec))
QUAD_PCS = (0x783a, *(pc for pcs in QUAD_MEMBER_PCS for pc in pcs))
# 6EC8/6EDC: JSR F9E2, MOVE.L A6,FF31B4/FF31B8, MOVE.B #0,(A6), RTS.
DORMANT_B4_PCS = (0x6ec8, 0x6ece, 0x6ed4, 0x6eda)
DORMANT_B8_PCS = (0x6edc, 0x6ee2, 0x6ee8, 0x6eee)
PAIR_PCS = (0x7b9c, *FIRST_PCS, *SECOND_PCS)
RISING_PCS = (0x7772, *RISING_FIRST_PCS, *RISING_SECOND_PCS)
VIS_PCS = (0x7c26, *VIS_FIRST_PCS, *VIS_SECOND_PCS)
LINKS = {0: 0, 0xffff0690: 1, 0xffff0838: 2}
# Native write events report the following PC. Values are the static contract.
F9E2_FIELDS = ((0xf9fc, 0, 1, 0x80), (0xfa04, 0x16, 4, 0x12646), (0xfa0c, 0x46, 4, 0x12646),
               (0xfa10, 0x14, 2, 0), (0xfa14, 0x12, 2, 0), (0xfa1a, 6, 2, 0x21d))
MEMBERS = (((0x7ba8, 0, 1, 0x81), (0x7bae, 6, 2, 916), (0x7bb4, 8, 2, 916), (0x7bba, 10, 2, 921), (0x7bc0, 2, 2, 161),
            (0x7bc6, 4, 2, 270), (0x7bcc, 13, 1, 4), (0x7bd2, 12, 1, 4), (0x7bda, 0x16, 4, 0x12646)),
           ((0x7be6, 0, 1, 0x81), (0x7bec, 6, 2, 919), (0x7bf2, 8, 2, 916), (0x7bf8, 10, 2, 921), (0x7bfe, 2, 2, 164),
            (0x7c04, 4, 2, 270), (0x7c0a, 13, 1, 5), (0x7c10, 12, 1, 5), (0x7c18, 0x16, 4, 0x12646), (0x7c1e, 0x12, 2, 0x800)))
VIS_MEMBERS = (((0x7c32, 0, 1, 0x81), (0x7c38, 6, 2, 892), (0x7c3e, 8, 2, 892), (0x7c44, 10, 2, 901), (0x7c4a, 2, 2, 287),
                (0x7c50, 4, 2, 152), (0x7c56, 13, 1, 5), (0x7c5c, 12, 1, 5), (0x7c64, 0x16, 4, 0x7ca4)),
               ((0x7c70, 0, 1, 0x81), (0x7c76, 6, 2, 902), (0x7c7c, 8, 2, 902), (0x7c82, 10, 2, 911), (0x7c88, 2, 2, 287),
                (0x7c8e, 4, 2, 184), (0x7c94, 13, 1, 5), (0x7c9a, 12, 1, 5), (0x7ca2, 0x16, 4, 0x7ca4)))
# Contracted handler stores (next-PC: offset, width), as in the mixed-session audit.
VISIBILITY_WRITES = {0x7cb2: (0x12, 2), 0x7cc0: (2, 2), 0x7cc6: (4, 2)}
RISING_WRITES = {0x7824: (0x10, 2), 0x782a: (4, 2), 0x7832: (4, 2), 0x7838: (0x10, 2)}


def rising_members(a5):
    # Both store the caller's A5; the second copies the first's X (+0x20) and Y via A4.
    return (((0x777e, 0, 1, 0x81), (0x7782, 0x4a, 4, a5), (0x7788, 2, 2, 0x9e), (0x778e, 4, 2, 0x106), (0x7794, 6, 2, 922), (0x779a, 8, 2, 922),
             (0x77a0, 10, 2, 927), (0x77a6, 12, 1, 5), (0x77ac, 13, 1, 5), (0x77b4, 0x16, 4, 0x7808), (0x77b8, 0x10, 2, 0)),
            ((0x77c4, 0x4a, 4, a5), (0x77ca, 0, 1, 0x81), (0x77d0, 2, 2, 0x9e), (0x77d6, 2, 2, 0xbe), (0x77dc, 4, 2, 0x106), (0x77e2, 6, 2, 928),
             (0x77e8, 8, 2, 928), (0x77ee, 10, 2, 933), (0x77f4, 12, 1, 5), (0x77fa, 13, 1, 5), (0x7802, 0x16, 4, 0x7808), (0x7806, 0x10, 2, 0)))
def quad_members(a5):
    # Only the probe stores A5. Members 1..3 copy X/Y (150/262) through A4,
    # then ADDI.W 0x20 rewrites X, Y or both in place.
    x, y = 0x96, 0x106
    return (((0x7846, 0, 1, 0x80), (0x784a, 0x4a, 4, a5), (0x7850, 2, 2, x), (0x7856, 4, 2, y), (0x785c, 6, 2, 0x390),
             (0x7864, 0x16, 4, 0x12646), (0x786c, 0x46, 4, 0x78ee), (0x7872, 0x1e, 2, 0x38), (0x7878, 0x20, 2, 8)),
            ((0x7886, 0, 1, 0x80), (0x788c, 2, 2, x), (0x7892, 2, 2, x + 0x20), (0x7898, 4, 2, y), (0x789e, 6, 2, 0x391)),
            ((0x78aa, 0, 1, 0x80), (0x78b0, 2, 2, x), (0x78b6, 4, 2, y), (0x78bc, 4, 2, y + 0x20), (0x78c2, 6, 2, 0x392)),
            ((0x78ce, 0, 1, 0x80), (0x78d4, 2, 2, x), (0x78da, 2, 2, x + 0x20), (0x78e0, 4, 2, y), (0x78e6, 4, 2, y + 0x20), (0x78ec, 6, 2, 0x393)))


def dormant_members(identity, store_pc, clear_pc):
    # An absolute store (offset >= 0x100) of value None writes the member's own address.
    return (((store_pc, identity, 4, None), (clear_pc, 0, 1, 0)),)


def probe_fields(b):
    # 783A writes +1E..+21; the remaining private bytes must be verified zero.
    require(b[1] == 0 and b[0x22:0x46] == bytes(36), 'unmodeled collision probe private fields'); return collision_fields(b)


# Per variant: ordered member PC runs, F9E2 return addresses, per-member native
# pool kind/fields and per-member explicit phase inputs (None, gates, collision).
VARIANTS = {
    'return_only': dict(entry=0x7b9c, pcs=PAIR_PCS, member_pcs=(FIRST_PCS, SECOND_PCS), members=MEMBERS, pushes=(0x7ba2, 0x7be0), anchored=True,
                        kinds=(8, 8), fields=(return_only_fields,) * 2, inputs=(None, None), native='wiznliz-return-only',
                        unknown='return-only pair inherits unknown slot state', pool='--pair-pool'),
    'visibility': dict(entry=0x7c26, pcs=VIS_PCS, member_pcs=(VIS_FIRST_PCS, VIS_SECOND_PCS), members=VIS_MEMBERS, pushes=(0x7c2c, 0x7c6a), anchored=False,
                       kinds=(5, 5), fields=(private_fields,) * 2, inputs=('gates', 'gates'), native='wiznliz-private',
                       unknown='visibility pair inherits unknown slot state', pool='--pair-pool', writers=VISIBILITY_WRITES),
    'rising': dict(entry=0x7772, pcs=RISING_PCS, member_pcs=(RISING_FIRST_PCS, RISING_SECOND_PCS), members=rising_members, pushes=(0x7778, 0x77c0), anchored=False,
                   kinds=(5, 5), fields=(private_fields,) * 2, inputs=('gates', 'gates'), native='wiznliz-private',
                   unknown='rising pair inherits unknown slot state', pool='--rising-pair-pool', clobbers='A4', control=True, writers=RISING_WRITES),
    # Mode 80 never animates and the probe's miss path writes nothing, so all
    # four use the return-only presentation/render write audit.
    'quad': dict(entry=0x783a, pcs=QUAD_PCS, member_pcs=QUAD_MEMBER_PCS, members=quad_members, pushes=(0x7840, 0x7880, 0x78a4, 0x78c8), anchored=False,
                 kinds=(7, 8, 8, 8), fields=(probe_fields, return_only_fields, return_only_fields, return_only_fields), inputs=('collision', None, None, None),
                 native='wiznliz-collision', unknown='collision quad inherits unknown slot state', pool='--quad-pool', clobbers='A4', control=True),
    # Dormant objects keep F9E2's 12646/12646 selectors, so they use the
    # return-only fields and write audit; the header field selects the identity.
    'dormant_b4': dict(entry=0x6ec8, pcs=DORMANT_B4_PCS, member_pcs=(DORMANT_B4_PCS[1:],), members=dormant_members(DORMANT, 0x6ed4, 0x6eda), pushes=(0x6ece,),
                       anchored=False, identity=0, kinds=(8,), fields=(return_only_fields,), inputs=(None,), native='wiznliz-return-only',
                       unknown='dormant object inherits unknown slot state', pool='--dormant-pool', header=(0,)),
    'dormant_b8': dict(entry=0x6edc, pcs=DORMANT_B8_PCS, member_pcs=(DORMANT_B8_PCS[1:],), members=dormant_members(DORMANT + 4, 0x6ee8, 0x6eee), pushes=(0x6ee2,),
                       anchored=False, identity=1, kinds=(8,), fields=(return_only_fields,), inputs=(None,), native='wiznliz-return-only',
                       unknown='dormant object inherits unknown slot state', pool='--dormant-pool', header=(1,)),
    # 6EB6 runs differ only by A5; they are compared natively as part of the tail.
    'link_p1': dict(entry=0x6eb6, pcs=LINK_PCS, member_pcs=(LINK_PCS[1:],), members=dormant_members(LINKS_AT[0], 0x6ec0, 0x6ec6), pushes=(0x6ebc,),
                    anchored=False, link=0, a5=0xffff0690, kinds=(8,), fields=(return_only_fields,), inputs=(None,), native='wiznliz-return-only', composed=True),
    'link_p2': dict(entry=0x6eb6, pcs=LINK_PCS, member_pcs=(LINK_PCS[1:],), members=dormant_members(LINKS_AT[1], 0x6ec0, 0x6ec6), pushes=(0x6ebc,),
                    anchored=False, link=1, a5=0xffff0838, kinds=(8,), fields=(return_only_fields,), inputs=(None,), native='wiznliz-return-only', composed=True),
    # 6A94 is a data-driven loop, validated by validate_pickups rather than as straight-line code.
    'pickups': dict(entry=0x6a94, custom='pickups', anchored=False, native='wiznliz-return-only', composed=True)}
# Prefix order of the six initializers and the writer of each retained identity.
PREFIX_ORDER = ('dormant_b4', 'dormant_b8', 'rising', 'quad', 'return_only', 'visibility')
IDENTITY_WRITERS = {ANCHOR: 0x7c24, DORMANT: 0x6ed4, DORMANT + 4: 0x6ee8, LINKS_AT[0]: 0x6ec0, LINKS_AT[1]: 0x6ec0}
CONTRACTED = (set(F9E2_PCS) | set(PAIR_PCS) | set(VIS_PCS) | set(RISING_PCS) | set(QUAD_PCS) | set(DORMANT_B4_PCS) | set(DORMANT_B8_PCS) | set(PREFIX[2:])
              | set(range(0x6a94, 0x6bd6)) | set(LINK_PCS) | {0x68a8, 0x68b2, 0x68bc})


def phase_kind(v): return next((i for i in v['inputs'] if i), None)


def pickup_fields(b):
    """Native Pickup row: return-only-shaped fields, extents and the FF447A record index."""
    require(len(b) == 78 and be(b, 0x16, 4) == 0x12646 and be(b, 0x46, 4) == PICKUP_SERVICE and be(b, 0x1a, 4) == 0 and be(b, 0x14) == 0, 'pickup selectors/service differ')
    require(b[1] == 0 and b[0x22:0x42] == bytes(32), 'unmodeled pickup private fields')
    record = be(b, 0x42, 4) - 0xffff447a; require(0 <= record < 192 and record % 12 == 0, 'pickup record differs')
    link = be(b, 0x4a, 4); require(link in LINKS, 'unmapped pickup control identity')
    return (be(b, 2), be(b, 4), be(b, 18), b[0], be(b, 6), be(b, 8), be(b, 10), b[12], b[13], be(b, 14), be(b, 16), LINKS[link], be(b, 0x1e), be(b, 0x20), record // 12)


def member_info(v, k):
    """Per-member kind, fields, inputs and (for collision consumers) service/hit PCs."""
    if v.get('custom') == 'pickups':
        return dict(kind=9, fields=pickup_fields, inputs='collision', service=PICKUP_SERVICE, hit=PICKUP_HIT, stops_on_hit=True)
    return dict(kind=v['kinds'][k], fields=v['fields'][k], inputs=v['inputs'][k], service=SERVICE, hit=HIT, stops_on_hit=False)
UNREPRESENTED = (1, *range(0x1a, 0x46))


def recipe(walk):
    ranges = [dict(label='object', domain='68K RAM', register='M68K A6', offset=0, length=78),
              dict(label='anchor', domain='68K RAM', offset=ANCHOR & 65535, length=4),
              dict(label='dormant', domain='68K RAM', offset=DORMANT & 65535, length=8),
              dict(label='link0', domain='68K RAM', offset=LINKS_AT[0] & 65535, length=4), dict(label='link1', domain='68K RAM', offset=LINKS_AT[1] & 65535, length=4),
              dict(label='stack', domain='68K RAM', register='M68K A7', offset=0, length=16)]
    if walk:
        # 78EE inputs: P1/P2 control tracking (+42/+44), X mask and P2 gate word.
        ranges += [dict(label='gates', domain='68K RAM', offset=0x31a4, length=4), dict(label='rise', domain='68K RAM', offset=0x31b0, length=4),
                   dict(label='tracking', domain='68K RAM', offset=0x06d2, length=4), dict(label='collision_mask', domain='68K RAM', offset=0x13ae, length=2),
                   dict(label='multiplayer', domain='68K RAM', offset=0x33e2, length=2), dict(label='tracking2', domain='68K RAM', offset=0x087a, length=4),
                   # 6C00 hits: the touched link (A4), the FF447A records, FF312C kinds and the FCB32 mailbox.
                   dict(label='linked', domain='68K RAM', register='M68K A4', offset=0, length=78), dict(label='records', domain='68K RAM', offset=0x447a, length=192),
                   dict(label='kinds', domain='68K RAM', offset=0x312c, length=32), dict(label='mailbox', domain='68K RAM', offset=0x0a9e, length=8),
                   # 7910 deliveries pop from the shared free stack.
                   dict(label='free', domain='68K RAM', offset=0x3008, length=280),
                   # 79B6/7AD6 and 7E18: FF31AC..FF31C7 (with FF31C4/FF31C6), both controls'
                   # +46..+57 and the FF0D60 tilemap; the completion's FF31A8, FF316C..FF3171
                   # and FF0690's +3C/+3E.
                   dict(label='ingredient', domain='68K RAM', offset=0x31ac, length=28), dict(label='message', domain='68K RAM', offset=0x06d6, length=18),
                   dict(label='spell_flags', domain='68K RAM', offset=0x31a8, length=4), dict(label='door_state', domain='68K RAM', offset=0x316c, length=6),
                   dict(label='origin', domain='68K RAM', offset=0x06cc, length=4),
                   # 7082 (entering the door): FF0F00 and the camera words FF444A/FF444C.
                   dict(label='exit', domain='68K RAM', offset=0x0f00, length=4), dict(label='camera', domain='68K RAM', offset=0x444a, length=4),
                   dict(label='message2', domain='68K RAM', offset=0x087e, length=18), dict(label='tilemap', domain='68K RAM', offset=0x0d60, length=4),
                   # 6D8C emitter inputs: FF0690's +00 actor link, that actor's X/Y and the E918 state.
                   dict(label='owner_link', domain='68K RAM', offset=0x0690, length=4), dict(label='owner', domain='68K RAM', offset=0x1ab4, length=6),
                   dict(label='random', domain='68K RAM', offset=0x0bac, length=8)]
    else:
        ranges += [dict(label='allocated', domain='68K RAM', register='M68K A5', offset=0, length=78),
                   dict(label='free', domain='68K RAM', offset=0x3008, length=280),
                   # 6A94's inputs and outputs: kinds, counts, positions, records, FF31AC/FF31B0.
                   dict(label='kinds', domain='68K RAM', offset=0x312c, length=32), dict(label='counts', domain='68K RAM', offset=0x314c, length=32),
                   dict(label='positions', domain='68K RAM', offset=0x4c80, length=64), dict(label='records', domain='68K RAM', offset=0x447a, length=192),
                   dict(label='activation', domain='68K RAM', offset=0x31ac, length=8),
                   # 7DB8/CB72/CB9A/6EF0 inputs and outputs.
                   dict(label='message', domain='68K RAM', offset=0x06d6, length=18), dict(label='two_player', domain='68K RAM', offset=0x33e2, length=2),
                   dict(label='returned', domain='68K RAM', offset=0x31aa, length=2), dict(label='pair_request', domain='68K RAM', offset=0x316c, length=2),
                   dict(label='tilemap', domain='68K RAM', offset=0x0d60, length=4), dict(label='lock', domain='68K RAM', offset=0x010c, length=2),
                   # 7FBE/7154/735E/7568 gates and 7FBE's P2 origin.
                   dict(label='pair_gates', domain='68K RAM', offset=0x3172, length=8), dict(label='p2_origin', domain='68K RAM', offset=0x0874, length=4)]
    pcs = [*CALLERS, *DORMANT_B4_PCS, *DORMANT_B8_PCS, *PICKUP_TRACE, *LINK_PCS, *MESSAGE_PCS, *(pc for pcs in GATED_PCS for pc in pcs), *RISING_PCS, *QUAD_PCS, *PAIR_PCS, *VIS_PCS, *F9E2_PCS, *LOOP_PCS, *OTHER,
           *((*WALK, SERVICE, HIT, PICKUP_SERVICE, PICKUP_HIT, PICKUP_LINKED, *PICKUP_DONE, SOUND, *PICKUP_CALLBACKS, *ACTIVATE, COPY,
              PROBE_LINKED, PROBE_SPARKLE, PROBE_DONE, *PROBE_RETURNS, DELIVERED_CALLBACK, *EMITTER_PCS) if walk else ())]
    return dict(pcs=list(dict.fromkeys(pcs)), registers=True, returns=False, maxEvents=20000, ranges=ranges)


def slot(address):
    require(BASE <= address < LIMIT and (address - BASE) % STRIDE == 0, 'pointer is not a pool slot')
    return (address - BASE) // STRIDE


def address(index): return BASE + STRIDE * index


def free_fields(b):
    require(len(b) == 280 and be(b, 0, 4) == 0, 'free stack extent/sentinel differs')
    head = be(b, 276, 4); require(0xffff300c <= head <= 0xffff311c and head % 4 == 0, 'free stack head differs')
    values = [slot(be(b, i, 4)) for i in range(4, (head & 65535) - 0x3008, 4)]
    require(len(set(values)) == len(values), 'duplicate free slot'); return values


def registers(e, names=('D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5')):
    return tuple(e['registers']['M68K ' + n] for n in names)


def apply(b, fields):
    """Object stores only; absolute identity stores (offset >= 0x100) are checked separately."""
    out = bytearray(b)
    for _pc, offset, width, value in fields:
        if offset < 0x100: out[offset:offset + width] = value.to_bytes(width, 'big')
    return bytes(out)


def split_invocations(events, entry, pcs):
    """Contiguous straight-line runs beginning at entry; no foreign hooked PC may interleave."""
    runs = []; current = None
    for e in events:
        if e['pc'] == entry:
            require(current is None, 'nested/unfinished invocation'); current = [e]
        elif current is not None:
            current.append(e)
            if len(current) == len(pcs):
                require([x['pc'] for x in current] == list(pcs), 'invocation instruction order differs'); runs.append(current); current = None
    require(current is None, 'unfinished invocation'); return runs


def has(e, label): return any(b['label'] == label for b in e['ranges'])


def validate_f9e2(run):
    # A long setup routine may cross a completed-frame boundary; order is global.
    entry, *_, pop, first, _f2, _f3, _f4, _f5, _f6, _restore, ret = run
    sp = entry['registers']['M68K A7']; caller = be(block(entry, 'stack'), 0, 4); with_free = all(has(e, 'free') for e in run)
    require(first['pc'] == 0xf9f6 and pop['pc'] == 0xf9f4, 'allocator boundary differs')
    target = first['registers']['M68K A6']; index = slot(target)
    require(pop['registers']['M68K A0'] == first['registers']['M68K A0'], 'allocator pointer differs')
    if with_free:
        head = be(block(entry, 'free'), 276, 4); entries = block(entry, 'free')
        require(be(entries, (head & 65535) - 0x3008 - 4, 4) == target and pop['registers']['M68K A0'] == head - 4, 'allocator did not pop the top entry')
        require(be(block(first, 'free'), 276, 4) == head - 4 and block(first, 'free')[:276] == entries[:276], 'allocator head/entries differ')
        require(block(ret, 'free') == block(first, 'free'), 'allocator changed the stack after popping')
    residue = block(first, 'object')
    require(block(ret, 'object') == apply(residue, F9E2_FIELDS), 'allocator wrote outside its defaults')
    require(ret['registers']['M68K A7'] == sp and be(block(ret, 'stack'), 0, 4) == caller and ret['registers']['M68K A6'] == target, 'allocator return/A6 differs')
    require(registers(ret) == registers(entry), 'allocator changed a preserved register')
    return dict(frame=entry['frame'], return_frame=ret['frame'], caller=caller, slot=index, entry_a6=entry['registers']['M68K A6'],
                head=be(block(entry, 'free'), 276, 4) if with_free else None, residue=residue.hex())


def representable(residue):
    return all(not residue[i] for i in UNREPRESENTED) and be(residue, 0x4a, 4) in LINKS


def members(v, a5): return v['members'](a5) if callable(v['members']) else v['members']


def validate_pair(events, f9e2, name='return_only'):
    """Every run of one initializer: ordered pops of the top entries, exact
    stores, A6 left on the last member; 7B9C stores it in FF31C0, the others
    leave FF31C0 alone. 7772/783A also leave A4 on the first member."""
    v = VARIANTS[name]; out = []; count = len(v['member_pcs'])
    order = [v['entry']]; starts = []
    for pcs in v['member_pcs']: starts.append(len(order)); order += [*F9E2_PCS, *pcs]
    events = [e for e in events if e['pc'] in v['pcs'] or e['pc'] in F9E2_PCS]
    for i in [i for i, e in enumerate(events) if e['pc'] == v['entry'] and e['registers']['M68K A5'] == v.get('a5', e['registers']['M68K A5'])]:
        run = events[i:i + len(order)]; require([e['pc'] for e in run] == order, f'{name} instruction order differs')
        entry, done = run[0], run[-1]; sp = entry['registers']['M68K A7']
        allocs = [validate_f9e2(run[at:at + 14]) for at in starts]
        require(all(a['head'] is not None for a in allocs), f'{name} allocator lacks free-stack evidence')
        require(tuple(a['caller'] for a in allocs) == v['pushes'], f'{name} allocator callers differ')
        free = free_fields(block(entry, 'free'))
        require(len(free) >= count and [a['slot'] for a in allocs] == free[::-1][:count], f'{name} did not pop the top entries in order')
        # Member m is final where A6 still names it: the next F9E2 entry, or the end.
        ends = [run[at] for at in starts[1:]] + [done]; finals = [block(e, 'object') for e in ends]
        require(all(e['registers']['M68K A6'] == address(a['slot']) for e, a in zip(ends, allocs)), f'{name} A6 ownership differs')
        stores = members(v, entry['registers']['M68K A5'])
        for k, (a, final) in enumerate(zip(allocs, finals)):
            require(final == apply(apply(bytes.fromhex(a['residue']), F9E2_FIELDS), stores[k]), f'{name} member {k} bytes differ')
        anchor = be(block(done, 'anchor'), 0, 4)
        require(anchor == address(allocs[-1]['slot']) if v['anchored'] else anchor == be(block(entry, 'anchor'), 0, 4), f'{name} FF31C0 effect differs')
        dormant = [be(block(e, 'dormant'), 4 * k, 4) for e in (entry, done) for k in (0, 1)]
        want = dormant[:2]
        if 'identity' in v: want[v['identity']] = address(allocs[0]['slot'])
        require(dormant[2:] == want, f'{name} FF31B4/FF31B8 effect differs')
        links = [be(block(e, f'link{k}'), 0, 4) for e in (entry, done) for k in (0, 1)]
        want = links[:2]
        if 'link' in v: want[v['link']] = address(allocs[0]['slot'])
        require(links[2:] == want, f'{name} control +1A2 link effect differs')
        require(done['registers']['M68K A7'] == sp and block(done, 'stack') == block(entry, 'stack'), f'{name} stack differs')
        kept = tuple(n for n in ('D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5') if n != v.get('clobbers'))
        require(registers(done, kept) == registers(entry, kept), f'{name} changed a preserved register')
        if v.get('clobbers'): require(done['registers']['M68K ' + v['clobbers']] == address(allocs[0]['slot']), f'{name} {v["clobbers"]} does not name the first member')
        out.append(dict(variant=name, frame=entry['frame'], return_frame=done['frame'], entry_sequence=entry['sequence'], return_sequence=done['sequence'],
                        caller=be(block(entry, 'stack'), 0, 4), entry_a6=entry['registers']['M68K A6'],
                        entry_sp=sp, entry_registers={'M68K A0': entry['registers']['M68K A0'], 'M68K A5': entry['registers']['M68K A5']},
                        free_before=free, members=allocs, anchor_before=be(block(entry, 'anchor'), 0, 4), dormant_before=dormant[:2], finals=[f.hex() for f in finals],
                        representable=[representable(bytes.fromhex(a['residue'])) for a in allocs]))
    require(len(f9e2) >= count * len(out), f'{name} allocator accounting differs')
    return out


def pickup_stores(regs, kind, count):
    """6AF0 with 6B44/6BB2 for one pickup: object stores (offset < 0x100) and the
    FF447A record stores (absolute; value None = the object's address)."""
    a3 = regs['M68K A3'] & 0xffffff; d0, d1, d2, d3 = (regs[f'M68K D{i}'] & 65535 for i in range(4))
    if (d2 ^ 0x8000) - 0x8000 < 14:
        first = d2 * 6 + 0x260 & 65535
        frames = [(0x6b58, 6, 2, first), (0x6b5c, 8, 2, first), (0x6b60, 10, 2, first), (0x6b64, 10, 2, first + 5 & 65535)]
    else:
        f6, fa, pcs = {0x20d: (0x20d, 0x214, (0x6b7c, 0x6b82, 0x6b88)), 0x205: (0x205, 0x20c, (0x6b90, 0x6b96, 0x6b9c))}.get(d2, (0x1fd, 0x204, (0x6ba4, 0x6baa, 0x6bb0)))
        frames = [(pcs[0], 6, 2, f6), (pcs[1], 8, 2, f6), (pcs[2], 10, 2, fa)]
    cadence = [(0x6bc0, 12, 1, 1), (0x6bc6, 13, 1, 1)] if count == 2 else [(0x6bce, 12, 1, 5), (0x6bd4, 13, 1, 5)]
    head = [(0x6afe, 0x4a, 4, regs['M68K A5']), (0x6b02, 0x42, 4, regs['M68K A3']), (0x6b04, a3, 4, None), (0x6b06, a3 + 4, 4, regs['M68K A0']),
            (0x6b08, a3 + 8, 4, regs['M68K A1']), (0x6b0e, 0, 1, 0x81), (0x6b12, 2, 2, d0), (0x6b16, 4, 2, d1), (0x6b1c, 0x1e, 2, 0x10), (0x6b22, 0x20, 2, 0x10)]
    return head, frames, [(0x6b2e, 0x46, 4, PICKUP_SERVICE), (0x6b32, 0x10, 2, d3)], cadence, [(0x6b3e, 0x16, 4, 0x12646)]


def validate_pickups(events, f9e2):
    """Every 6A94 run: one 6AF0 per FF312C kind other than FFFF in entry order,
    D0/D1 from the next FF4C80 pair (Y + 16), D2/D3 the kind/count, A0/A1 that
    entry, A3 the next FF447A record; exact object bytes, sixteen records and
    FF31AC/FF31B0 cleared at return."""
    marks = set(PICKUP_TRACE) | set(F9E2_PCS); events = [e for e in events if e['pc'] in marks]; out = []
    for i in [i for i, e in enumerate(events) if e['pc'] == 0x6a94]:
        entry = events[i]; sp = entry['registers']['M68K A7']
        kinds = [be(block(entry, 'kinds'), 2 * k) for k in range(16)]; counts = [be(block(entry, 'counts'), 2 * k) for k in range(16)]
        positions = [(be(block(entry, 'positions'), 4 * k), be(block(entry, 'positions'), 4 * k + 2)) for k in range(16)]
        made = [k for k in range(16) if kinds[k] != 0xffff]
        order = [0x6a94, *([0x6af0, *F9E2_PCS, 0x6afa, 0x6b3e] * len(made)), 0x6aee]
        run = events[i:i + len(order)]; require([e['pc'] for e in run] == order, 'pickup pass instruction order differs')
        free = free_fields(block(entry, 'free')); require(len(free) >= len(made), 'pickup pass free stack too short')
        allocs = []; finals = []; registers_at = []; records = bytearray(192)
        for m, k in enumerate(made):
            at = 1 + m * 17; start, alloc_run, after, done = run[at], run[at + 1:at + 15], run[at + 15], run[at + 16]
            regs = start['registers']
            want = {'M68K D0': positions[m][0], 'M68K D1': positions[m][1] + 0x10 & 65535, 'M68K D2': kinds[k], 'M68K D3': counts[k],
                    'M68K A0': 0xffff312c + 2 * k, 'M68K A1': 0xffff314c + 2 * k, 'M68K A3': 0xffff447a + 12 * m, 'M68K A5': entry['registers']['M68K A5']}
            require(all((regs[n] & (65535 if n[5] == 'D' else 0xffffffff)) == value for n, value in want.items()) and regs['M68K A7'] == sp - 4, 'pickup call inputs differ')
            a = validate_f9e2(alloc_run); require(a['caller'] == 0x6afa and a['head'] is not None and a['slot'] == free[-1 - m], 'pickup allocation differs')
            stores = [x for part in pickup_stores(regs, kinds[k], counts[k]) for x in part]
            final = block(done, 'object'); require(done['registers']['M68K A6'] == address(a['slot']), 'pickup ownership differs')
            require(final == apply(apply(bytes.fromhex(a['residue']), F9E2_FIELDS), stores), f'pickup {m} bytes differ')
            # 6B44's MULU.W leaves the product's upper word in D2; MOVE.W restores only the low word.
            d2 = regs['M68K D2']; upper = (kinds[k] * 6 >> 16) if (kinds[k] ^ 0x8000) - 0x8000 < 14 else d2 >> 16
            require(registers(done, ('D0', 'D1', 'D3', 'A0', 'A1', 'A5')) == registers(start, ('D0', 'D1', 'D3', 'A0', 'A1', 'A5')) and done['registers']['M68K D2'] == (upper << 16 | d2 & 65535)
                    and done['registers']['M68K A3'] == regs['M68K A3'] + 12 and done['registers']['M68K A7'] == sp - 12, 'pickup registers differ')
            records[12 * m:12 * m + 12] = address(a['slot']).to_bytes(4, 'big') + want['M68K A0'].to_bytes(4, 'big') + want['M68K A1'].to_bytes(4, 'big')
            allocs.append(a); finals.append(final); registers_at.append({n: regs[n] for n in ('M68K D0', 'M68K D1', 'M68K D2', 'M68K D3', 'M68K A0', 'M68K A1', 'M68K A3', 'M68K A5', 'M68K A6')})
        done = run[-1]
        require(block(done, 'records') == bytes(records) and block(done, 'activation') == bytes(8), 'pickup pass records/FF31AC/FF31B0 differ')
        require(done['registers']['M68K A7'] == sp and done['registers']['M68K A5'] == entry['registers']['M68K A5'], 'pickup pass stack/A5 differs')
        out.append(dict(variant='pickups', frame=entry['frame'], return_frame=done['frame'], entry_sequence=entry['sequence'], return_sequence=done['sequence'],
                        caller=be(block(entry, 'stack'), 0, 4), entry_sp=sp, entry_registers={'M68K A0': entry['registers']['M68K A0'], 'M68K A5': entry['registers']['M68K A5'],
                        'M68K A3': entry['registers']['M68K A3'], 'M68K A6': entry['registers']['M68K A6']},
                        free_before=free, members=allocs, finals=[f.hex() for f in finals], representable=[representable(bytes.fromhex(a['residue'])) for a in allocs],
                        tables=dict(kinds=kinds, counts=counts, positions=positions), entries=made, calls=registers_at))
    require(len(f9e2) >= sum(len(r['members']) for r in out), 'pickup allocator accounting differs')
    return out


def pickup_writes(run):
    """Ordered 6A94 writes (next-PC convention): A3 save, the 48 record clears,
    FF31AC/FF31B0, then per pickup the BSR, A5/A6 saves, F9E2, 6AF0/6B44/6BB2
    stores and their BSR/D2 pushes."""
    sp = run['entry_sp']; out = [(0x6a9c, sp - 2 & 0xffffff, 2, 0x447a), (0x6a9c, sp - 4 & 0xffffff, 2, 0xffff)]
    for r in range(16): out += [(pc, 0xff447a + 12 * r + 4 * j, 4, 0) for j, pc in enumerate((0x6aa2, 0x6aa4, 0x6aa6))]
    out += [(0x6ab2, 0xff31ac, 4, 0), (0x6ab8, 0xff31b0, 4, 0)]
    head = run['members'][0]['head'] if run['members'] else None
    for m, (a, regs, k) in enumerate(zip(run['members'], run['calls'], run['entries'])):
        target = address(a['slot']); a5, a6, a0 = regs['M68K A5'], regs['M68K A6'], regs['M68K A0']
        out += [(0x6ae2, sp - 4 & 0xffffff, 4, 0x6ae2), (0x6af2, sp - 6 & 0xffffff, 2, a5 & 65535), (0x6af2, sp - 8 & 0xffffff, 2, a5 >> 16),
                (0x6af4, sp - 10 & 0xffffff, 2, a6 & 65535), (0x6af4, sp - 12 & 0xffffff, 2, a6 >> 16), (0x6afa, sp - 16 & 0xffffff, 4, 0x6afa),
                (0xf9e4, sp - 18 & 0xffffff, 2, a0 & 65535), (0xf9e4, sp - 20 & 0xffffff, 2, a0 >> 16), (0xf9f4, 0xff311c, 4, head - 4 * (m + 1)),
                *[(pc, target + o & 0xffffff, w, value) for pc, o, w, value in F9E2_FIELDS]]
        first, frames, middle, cadence, last = pickup_stores(regs, run['tables']['kinds'][k], run['tables']['counts'][k])
        obj = lambda fields: [(pc, o if o >= 0x100 else target + o & 0xffffff, w, target if value is None else value) for pc, o, w, value in fields]
        d2 = regs['M68K D2'] & 65535; small = (d2 ^ 0x8000) - 0x8000 < 14
        out += [*obj(first), (0x6b26, sp - 16 & 0xffffff, 4, 0x6b26), *([(0x6b4c, sp - 18 & 0xffffff, 2, d2)] if small else []), *obj(frames),
                *obj(middle), (0x6b36, sp - 16 & 0xffffff, 4, 0x6b36), *obj(cadence), *obj(last)]
    return out


def pair_writes(pair):
    """Ordered writes of one run (next-PC convention): 40 for 7B9C, 38 for 7C26, 43 for 7772, 65 for 783A, 12 for 6EC8/6EDC."""
    v = VARIANTS[pair.get('variant', 'return_only')]; sp = pair['entry_sp']; a0 = pair['entry_registers']['M68K A0']; head = pair['members'][0]['head']
    def alloc(target, head):
        push = sp - 8
        return [(0xf9e4, push + 2 & 0xffffff, 2, a0 & 65535), (0xf9e4, push & 0xffffff, 2, a0 >> 16), (0xf9f4, 0xff311c, 4, head)] + \
               [(pc, target + o & 0xffffff, w, value) for pc, o, w, value in F9E2_FIELDS]
    def member(target, fields):
        return [(pc, o if o >= 0x100 else target + o & 0xffffff, w, target if value is None else value) for pc, o, w, value in fields]
    stores = members(v, pair['entry_registers'].get('M68K A5', 0)); out = []
    for k, (a, push) in enumerate(zip(pair['members'], v['pushes'])):
        target = address(a['slot'])
        out += [(push, sp - 4 & 0xffffff, 4, push), *alloc(target, head - 4 * (k + 1)), *member(target, stores[k])]
    return out + ([(0x7c24, ANCHOR, 4, address(pair['members'][-1]['slot']))] if v['anchored'] else [])


def f9e2_write(w):
    """Contracted F9E2 write form, independent of which call produced it."""
    a6 = w['registers']['M68K A6']
    if w['pc'] == 0xf9e4:
        a0 = w['registers']['M68K A0']
        return w['width'] == 2 and 0xff0000 <= w['address'] < 0xff0200 and w['value'] == (a0 >> 16 if w['address'] % 4 == 0 else a0 & 65535)
    if w['pc'] == 0xf9f4: return (w['address'], w['width']) == (0xff311c, 4) and 0xffff300c <= w['value'] < 0xffff311c
    slot(a6); return any((w['pc'], w['address'], w['width'], w['value']) == (pc, a6 + o & 0xffffff, width, v) for pc, o, width, v in F9E2_FIELDS)


def exception_frames(events):
    """Indices of interrupt stack frames reported at the interrupted PC: a long
    push of that PC then a word push of the old SR below it, written with the
    interrupt mask raised. CPU exception processing, not initializer stores."""
    skip = set(); found = []
    for i, (a, b) in enumerate(zip(events, events[1:])):
        mask = a['registers'].get('M68K SR', 0) >> 8 & 7
        if (a['pc'] == b['pc'] and a['width'] == 4 and a['value'] == a['pc'] and b['width'] == 2 and b['address'] == a['address'] - 2
                and 0xff0000 <= a['address'] < 0xff0200 and mask > (b['value'] >> 8 & 7)):
            skip |= {i, i + 1}; found.append(dict(pc=a['pc'], mask=mask, saved_sr=b['value']))
    return skip, found


def prefix_writes(prefix):
    """The [6886,68A4) block: each BSR's return push, then that run's exact writes."""
    sp = prefix['sp']; out = []
    for ret, run in zip(PREFIX[2:], prefix['runs']): out += [(ret, sp - 4 & 0xffffff, 4, ret), *pair_writes(run)]
    return out


def audit_frame_writes(records, pairs, prefixes=()):
    """Complete write traces for the frames spanned by these runs: each run's
    exact contiguous block (a setup prefix's runs as one block with its BSR
    pushes), F9E2 forms elsewhere, no foreign group-slot or identity writer."""
    if isinstance(records, dict): records = [records]
    if isinstance(pairs, dict): pairs = [pairs]
    require(all(r['dropped'] == 0 for r in records), 'initializer frame write trace incomplete')
    events = [w for r in records for w in r['events']]; skip, interrupts = exception_frames(events)
    contracted = [w for i, w in enumerate(events) if w['pc'] in CONTRACTED and i not in skip]
    actual = [(w['pc'], w['address'], w['width'], w['value']) for w in contracted]
    kept = list(range(len(actual)))
    composed = {id(run) for prefix in prefixes for run in prefix['runs']}
    blocks = [(tail_writes if prefix.get('kind') == 'tail' else prefix_writes)(prefix) for prefix in prefixes] + [run_writes(pair) for pair in pairs if id(pair) not in composed]
    for want in blocks:
        starts = [i for i, w in enumerate(actual) if w == want[0]]
        require(len(starts) == 1 and actual[starts[0]:starts[0] + len(want)] == want, 'pair write sequence differs')
        kept = [i for i in kept if not starts[0] <= i < starts[0] + len(want)]
    rest = [contracted[i] for i in kept]
    require(all(w['pc'] in F9E2_PCS and f9e2_write(w) for w in rest), 'uncontracted allocator write')
    owned = {address(a['slot']) & 0xffffff for p in pairs for a in p['members']}
    for i, w in enumerate(events):
        hits_pair = any(w['address'] < base + STRIDE and base < w['address'] + w['width'] for base in owned)
        writers = {pc for at, pc in IDENTITY_WRITERS.items() if w['address'] < at + 4 and at < w['address'] + w['width']}
        if hits_pair or writers:
            require(w['pc'] in CONTRACTED and i not in skip and all(w['pc'] == pc for pc in writers), 'foreign writer touched a group slot/identity in its creation frames')
    return dict(frames=[r['frame'] for r in records], writes=sum(r['count'] for r in records), pair_writes=[len(run_writes(p)) for p in pairs],
                prefix_writes=[len(prefix_writes(x)) for x in prefixes if x.get('kind') != 'tail'], tail_writes=[len(tail_writes(x)) for x in prefixes if x.get('kind') == 'tail'],
                other_allocator_writes=len(rest), interrupt_frames=interrupts, complete=True)


def residue_row(residue):
    # Unrepresentable residue stays an unknown free slot; native must then reject.
    # The +08/+0A words, +0C/+0D bytes and +02/+04 position are always
    # representable; 783A keeps the former, 6EC8/6EDC all of them.
    if not representable(residue): return (0,)
    return (9, be(residue, 0x0e), be(residue, 0x10), LINKS[be(residue, 0x4a, 4)], be(residue, 8), be(residue, 10), residue[12], residue[13],
            be(residue, 2), be(residue, 4))


def native_seed(pair, phases):
    """Seeded pool rows; phases is a count or, for objects consuming explicit
    inputs, one gate or collision row per phase. 7772 and 783A add the caller's
    control as an explicit logical header input."""
    rows_in = phases if isinstance(phases, list) else None; count = len(rows_in) if rows_in is not None else phases
    v = VARIANTS[pair.get('variant', 'return_only')]; header = (SLOTS, len(pair['free_before']), count)
    if v.get('control'):
        a5 = pair['entry_registers']['M68K A5']; require(a5 in LINKS, f'unmapped {v["entry"]:X} control identity'); header += (LINKS[a5],)
    header += v.get('header', ())
    free = pair['free_before']; rows = [header, tuple(free)]
    inherited = {a['slot']: residue_row(bytes.fromhex(a['residue'])) for a in pair['members']}
    for i in range(SLOTS): rows.append(inherited.get(i, (0,) if i in free else (1,)))
    return rows + [tuple(g) for g in rows_in or ()]


def collision_inputs(e):
    """78EE inputs at a probe's phase entry: P1 tracking, X mask, P2 gate; P2
    tracking only when the gate selects it (zero coordinates otherwise)."""
    t = block(e, 'tracking'); gate = be(block(e, 'multiplayer'), 0); t2 = block(e, 'tracking2')
    return (be(t, 0), be(t, 2), be(block(e, 'collision_mask'), 0), gate, int(bool(gate)), *((be(t2, 0), be(t2, 2)) if gate else (0, 0)))


def continuity(frames, boundaries, pair, end_ram):
    """Retained groups from creation to END: occupancy, FF31C0/FF31B4/FF31B8 and
    per-walk states. `pair` is one 7B9C pair or a list of runs of any
    initializer. Each phase is (frame, fields by followed slot, shared private
    gates, probe collision inputs, hit, activity by followed slot).
    An unsupported 7910 hit is recorded only inside a retained probe's own
    service; its state must still be unchanged by the walk-level checks. A
    dormant FF31B4/FF31B8 object may be overwritten only by the unsupported
    7AD6 copy (FB06 with A4 = that slot after 7AD6 in the same frame); it is
    then recorded as converted and no longer followed."""
    pairs = pair if isinstance(pair, list) else [pair]
    owned = {}; infos = {}; states = {}; anchor = None; identities = {}; links = {}
    created = max(p['return_frame'] if 'return_frame' in p else p['frame'] for p in pairs)
    for p in pairs:
        v = VARIANTS[p.get('variant', 'return_only')]
        for k, (a, final) in enumerate(zip(p['members'], p['finals'])):
            owned[a['slot']] = (v, k); infos[a['slot']] = member_info(v, k); states[a['slot']] = bytes.fromhex(final)
        if v['anchored']: anchor = address(p['members'][-1]['slot'])
        if 'identity' in v: identities[v['identity']] = address(p['members'][0]['slot'])
        if 'link' in v: links[v['link']] = address(p['members'][0]['slot'])
    def kind(i): return infos[i]['kind']
    def fields(i, b): return infos[i]['fields'](b)
    def consumes(i): return infos[i]['inputs']
    def dormant(i): v = owned[i][0]; return 'identity' in v or 'link' in v
    def identity_bytes(raw): return {k: be(raw, 4 * k, 4) for k in identities}
    def link_bytes(e): return {k: be(block(e, f'link{k}'), 0, 4) for k in links}
    hit_pcs = {HIT, PICKUP_HIT}
    tracked = set(owned); conversions = {}
    def convert(index, es, before, frame):
        """Accept a dormant slot change only as an FB06 copy into it earlier in this
        frame, after unsupported 7AD6 or a 6C00 pickup hit (via 6D22)."""
        copies = [e for e in es if e['pc'] == COPY and e['registers']['M68K A4'] == address(index) and e['sequence'] < before]
        require(dormant(index) and len(copies) == 1, 'retained slot changed outside its phase')
        causes = [e for e in es if (e['pc'] in ACTIVATE or e['pc'] == PICKUP_HIT) and e['sequence'] < copies[0]['sequence']]
        require(causes, 'dormant object copy without 7AD6 or a pickup hit')
        tracked.discard(index)
        conversions[str(index)] = dict(frame=frame, source_slot=slot(copies[0]['registers']['M68K A6']), via='fb06', cause=f'{causes[-1]["pc"]:X}')
    phases = []; walks = 0; updates = 0; counts = Counter(); gate_values = Counter(); collision_values = Counter(); hit_frames = []
    b = boundaries[str(created + 1)]
    for index in owned: require(bytes.fromhex(b['slots'][str(index)]) == states[index], 'pair changed after creation in its frame')
    for frame in range(created + 1, END):
        es = frames.get(frame, [])
        walk = [e for e in es if e['pc'] in (0x69a4, 0x69ce)]
        inside_walk = lambda e: len(walk) == 2 and walk[0]['sequence'] < e['sequence'] < walk[1]['sequence']
        for e in es:
            pc = e['pc']; a5 = e['registers']['M68K A5']; a6 = e['registers']['M68K A6']
            if pc in hit_pcs:
                pooled = BASE <= a6 < LIMIT and (a6 - BASE) % STRIDE == 0
                require(inside_walk(e) and pooled and slot(a6) in tracked and consumes(slot(a6)) == 'collision' and infos[slot(a6)]['hit'] == pc,
                        'unsupported hit outside a retained collision phase')
            if anchor is not None: require(be(block(e, 'anchor'), 0, 4) == anchor, 'FF31C0 changed during continuity')
            if identities: require(identity_bytes(block(e, 'dormant')) == identities, 'FF31B4/FF31B8 changed during continuity')
            if links: require(link_bytes(e) == links, 'control +1A2 link changed during continuity')
            require(pc not in (0xf872, 0xf940), 'pool reset during continuity')
            popped = a6 if pc in (0xf9f6, 0xfa52) else a5 if pc == 0xf9a8 else None
            released = a6 if pc == 0xfaa4 else a5 if pc == 0xfa8c else None
            for value, what in ((popped, 'allocations'), (released, 'releases')):
                if value is not None:
                    require(slot(value) not in tracked, 'retained pair slot was reallocated/released'); counts[what] += 1
        starts = [e for e in es if e['pc'] == 0x69a4]; ends = [e for e in es if e['pc'] == 0x69ce]
        require(len(starts) == len(ends) <= 1, 'object walk cadence differs')
        if starts:
            walks += 1; phase = {}; active = {}; gates = set(); collisions = set(); hit = set()
            inside = [e for e in es if starts[0]['sequence'] < e['sequence'] < ends[0]['sequence']]
            for index in sorted(tracked):
                mine = [e for e in inside if e['registers']['M68K A6'] == address(index)]
                begin = [e for e in mine if e['pc'] == 0x69aa]; done = [e for e in mine if e['pc'] == 0x69c2]
                require(len(begin) == len(done) == 1 and begin[0]['sequence'] < done[0]['sequence'], 'retained slot phase cadence differs')
                if block(begin[0], 'object') != states[index]: convert(index, es, begin[0]['sequence'], frame); continue
                info = infos[index]
                services = [e for e in mine if e['pc'] == info['service'] and begin[0]['sequence'] < e['sequence'] < done[0]['sequence']]
                require(len(services) == (consumes(index) == 'collision'), 'retained slot collision service cadence differs')
                hits = [e for e in mine if e['pc'] == info['hit'] and begin[0]['sequence'] < e['sequence'] < done[0]['sequence']]
                require(len(hits) <= len(services) and (not hits or services[0]['sequence'] < hits[0]['sequence']), 'retained slot hit outside its service')
                if hits: hit.add(index)
                if hits and info['stops_on_hit']:
                    # The unsupported hit rewrites the pickup itself; stop following it here.
                    collisions.add(collision_inputs(begin[0])); tracked.discard(index)
                    conversions[str(index)] = dict(frame=frame, via='hit', cause=f'{info["hit"]:X}'); continue
                updates += 1
                states[index] = block(done[0], 'object'); phase[index] = fields(index, states[index]); active[index] = bool(states[index][0] & 0x80)
                if consumes(index) == 'gates': g = block(begin[0], 'gates'); gates.add((be(block(begin[0], 'rise'), 0, 4), be(g, 2), be(g, 0)))
                if consumes(index) == 'collision': collisions.add(collision_inputs(begin[0]))
            require(len(gates) <= 1, 'gated pair members saw different gate inputs in one walk')
            require(len(collisions) <= 1, 'collision members saw different inputs in one walk')
            gate = gates.pop() if gates else None; collision = collisions.pop() if collisions else None
            if gate is not None: gate_values[str(gate)] += 1
            if collision is not None: collision_values[str(collision[2:])] += 1
            if hit: hit_frames.append(frame)
            phases.append((frame, phase, gate, collision, hit, active))
        b = boundaries[str(frame + 1)]
        if anchor is not None: require(bytes.fromhex(b['anchor']) == anchor.to_bytes(4, 'big'), 'FF31C0 boundary differs')
        if identities: require(identity_bytes(bytes.fromhex(b['dormant'])) == identities, 'FF31B4/FF31B8 boundary differs')
        if links: require({k: be(bytes.fromhex(b['links']), 4 * k, 4) for k in links} == links, 'control +1A2 link boundary differs')
        for index in sorted(tracked):
            if bytes.fromhex(b['slots'][str(index)]) != states[index]: convert(index, es, float('inf'), frame)
    for index in tracked:
        o = (BASE & 65535) + index * STRIDE; require(end_ram[o:o + STRIDE] == states[index], 'retained slot end state differs')
    if anchor is not None: require(be(end_ram, ANCHOR & 65535, 4) == anchor, 'FF31C0 end state differs')
    if identities: require(identity_bytes(end_ram[DORMANT & 65535:(DORMANT & 65535) + 8]) == identities, 'FF31B4/FF31B8 end state differs')
    if links: require({k: be(end_ram, LINKS_AT[k] & 65535, 4) for k in links} == links, 'control +1A2 link end state differs')
    return phases, dict(frames=END - created - 1, walks=walks, updates=updates, **counts, gate_inputs=dict(gate_values),
                        collision_config_inputs=dict(collision_values), unsupported_hit_frames=hit_frames, conversions=conversions,
                        end_rows={str(i): (kind(i), *fields(i, states[i])) for i in sorted(tracked)})


def validate_private_write(w, base, writers=VISIBILITY_WRITES):
    offset = w['address'] - base
    if w['pc'] in writers:
        require(w['registers']['M68K A6'] == base + 0xff000000 and writers[w['pc']] == (offset, w['width']), 'unmodeled private handler writer')
    else: validate_return_only_write(w, base, True)


def audit_continuity_writes(writes, pair, conversions=None):
    """Contracted writer forms for followed slots; no identity writer. A
    converted dormant slot's conversion frame must begin with FB06's complete
    78-byte copy (next PC FB10); later writes to it are outside this scope."""
    pairs = pair if isinstance(pair, list) else [pair]
    owned = {a['slot']: VARIANTS[p.get('variant', 'return_only')] for p in pairs for a in p['members']}
    converted = {int(k): c['frame'] for k, c in (conversions or {}).items()}
    created = max(p['return_frame'] if 'return_frame' in p else p['frame'] for p in pairs)
    complete = []; incomplete = []; checked = Counter(); copies = Counter()
    for record in writes:
        if not created < record['frame'] < END: continue
        (complete if record['dropped'] == 0 else incomplete).append(record['frame'])
        mine = {}
        for w in record['events']:
            require(not (w['address'] < ANCHOR + 4 and ANCHOR < w['address'] + w['width']), 'FF31C0 writer during continuity')
            require(not (w['address'] < DORMANT + 8 and DORMANT < w['address'] + w['width']), 'FF31B4/FF31B8 writer during continuity')
            require(not any(w['address'] < at + 4 and at < w['address'] + w['width'] for at in LINKS_AT), 'control +1A2 link writer during continuity')
            for index, v in owned.items():
                base = address(index) & 0xffffff
                if w['address'] < base + STRIDE and base < w['address'] + w['width']:
                    if index in converted and record['frame'] >= converted[index]: mine.setdefault(index, []).append(w); continue
                    (validate_private_write(w, base, v['writers']) if v.get('writers') else validate_return_only_write(w, base, True)); checked[str(index)] += 1
        for index, ws in mine.items():
            if record['frame'] != converted[index] or conversions[str(index)].get('via', 'fb06') != 'fb06': continue
            base = address(index) & 0xffffff
            require(record['dropped'] == 0 and [(w['pc'], w['address'] - base, w['width']) for w in ws[:STRIDE]] == [(0xfb10, o, 1) for o in range(STRIDE)],
                    'dormant conversion is not one complete FB06 copy')
            copies[str(index)] += STRIDE
    return dict(complete_frames=len(complete), incomplete_frames=incomplete, pair_writes=sum(checked.values()), writes_by_slot=dict(checked),
                conversion_copy_writes=dict(copies),
                scope='Write events are complete only where the native buffer did not drop; boundary and routine continuity cover every frame. A converted slot is audited up to its copy.')


def compare_native(native, pair, phases):
    """Native seeded pool from the run-entry stack and verified inheritance, then
    the retained phases (gated objects consume each phase's observed gates; the
    783A probe consumes each phase's observed 78EE inputs). Native compares
    phases up to the first original 7910 hit of its probe and must reject
    exactly there; later phases are original-only continuity. A dormant member
    converted by unsupported 7AD6 bounds the comparison before its conversion,
    with no native counterpart to reject."""
    v = VARIANTS[pair.get('variant', 'return_only')]; kind = phase_kind(v); after = []; converted = []
    slots = [a['slot'] for a in pair['members']]
    if kind == 'collision':
        first_hit = next((i for i, p in enumerate(phases) if any(s in p[4] for s in slots)), None)
        if first_hit is not None: phases, after = phases[:first_hit], phases[first_hit:]
    gone = next((i for i, p in enumerate(phases) if any(s not in p[1] for s in slots)), None)
    if gone is not None: phases, converted = phases[:gone], phases[gone:]
    sent = phases + after[:1]
    inputs = [p[2] for p in sent] if kind == 'gates' else [p[3] for p in sent] if kind == 'collision' else len(sent)
    rows = native_seed(pair, inputs); data = encode_cases(rows)
    p = subprocess.run([str(native), v['pool']], input=data, capture_output=True, timeout=60)
    identity = dict(command=[str(native), v['pool']], seed_sha256=hashlib.sha256(data).hexdigest())
    if not all(pair['representable']):
        require(p.returncode == 2 and not p.stdout and p.stderr.decode().strip() == v['unknown'], 'native accepted unrepresentable inheritance')
        require(not phases, 'retained pair cannot be unrepresentable'); return identity | dict(outcome='native_rejected_unrepresented_inheritance')
    if after: require(p.returncode == 2 and p.stderr.decode().strip() == 'unsupported collision-hit7910 (primary)', 'native did not reject the first original 7910 hit')
    else: require(p.returncode == 0, 'native pair pool failed: ' + p.stderr.decode())
    lines = [tuple(map(int, l.split())) for l in p.stdout.splitlines()]; require(len(lines) == 1 + len(phases), 'native pair output extent differs')
    free = pair['free_before']; n = len(slots)
    created = [(*v['fields'][k](bytes.fromhex(f)),) for k, f in enumerate(pair['finals'])]
    anchor = (1, slots[-1], 1) if v['anchored'] else ()
    if 'identity' in v: anchor = tuple(x for k in (0, 1, 2) for x in ((1, slots[0], 1) if k == v['identity'] else (0, 0, 0)))
    require(lines[0] == (*(x for s in slots for x in (s, 1)), *anchor, len(free) - n, *free[:-n],
                         *(x for k, c in enumerate(created) for x in (v['kinds'][k], *c))), 'native group initialization differs')
    kinds = dict(zip(slots, v['kinds']))
    for (frame, phase, _gate, _collision, _hit, active), line in zip(phases, lines[1:]):
        # Active objects report an update; dormant ones an inactive observation.
        expect = [(1 if active[i] else 3, i, 1, kinds[i], *phase[i]) for i in sorted(phase) if i in kinds]
        require(line == (len(expect), *(x for e in expect for x in e)), f'native retained group differs at {frame}')
    bounded = dict(rejected_at_frame=after[0][0], original_only_phases=len(after), original_hit_phases=sum(any(s in q[4] for s in slots) for q in after)) if after else {}
    if converted: bounded = dict(converted_at_frame=converted[0][0], original_only_phases=len(converted))
    return identity | dict(outcome='matched', output_sha256=hashlib.sha256(p.stdout).hexdigest(), phases=len(phases)) | bounded


def validate_prefix(events, pairs):
    """Each [6886,68A4) run: LEA FF0690,A5, then the six initializer runs in
    prefix order from one stack, each between its BSR and return marks, with
    consecutive pops from the 6886-entry free stack, falling through to 68A4."""
    out = []; marks = [e for e in events if e['pc'] in PREFIX]; at = lambda e: (e['frame'], e['sequence'])
    for i in [i for i, e in enumerate(marks) if e['pc'] == PREFIX[0]]:
        seq = marks[i:i + len(PREFIX)]; require([e['pc'] for e in seq] == list(PREFIX), 'setup prefix order differs')
        sp = seq[0]['registers']['M68K A7']
        require(all(e['registers']['M68K A7'] == sp for e in seq), 'setup prefix stack differs')
        require(all(e['registers']['M68K A5'] == 0xffff0690 for e in seq[1:]), 'setup prefix A5 differs')
        runs = []
        for name, lo, hi in zip(PREFIX_ORDER, seq[1:], seq[2:]):
            found = [p for p in pairs if p['variant'] == name and at(lo) < (p['frame'], p['entry_sequence']) and (p['return_frame'], p['return_sequence']) < at(hi)]
            require(len(found) == 1 and found[0]['entry_sp'] == sp - 4, f'setup prefix {name} run differs')
            runs.append(found[0])
        free = free_fields(block(seq[0], 'free')); expect = free
        for run in runs:
            require(run['free_before'] == expect, 'setup prefix pops are not consecutive'); expect = expect[:-len(run['members'])]
        out.append(dict(frame=seq[0]['frame'], return_frame=seq[-1]['frame'], sp=sp, free_before=free, runs=runs,
                        slots=[a['slot'] for run in runs for a in run['members']]))
    return out


def compare_prefix(native, prefix):
    """Native --prefix-pool from the 6886-entry stack with every popped slot's
    verified inheritance and FF0690's logical identity, against all twelve
    original members and the FF31B4/FF31B8/FF31C0 identities."""
    runs = prefix['runs']; free = prefix['free_before']; slots = prefix['slots']
    header = (SLOTS, len(free), 0, LINKS[0xffff0690])
    inherited = {a['slot']: residue_row(bytes.fromhex(a['residue'])) for run in runs for a in run['members']}
    rows = [header, tuple(free), *(inherited.get(i, (0,) if i in free else (1,)) for i in range(SLOTS))]; data = encode_cases(rows)
    p = subprocess.run([str(native), '--prefix-pool'], input=data, capture_output=True, timeout=60)
    identity = dict(command=[str(native), '--prefix-pool'], seed_sha256=hashlib.sha256(data).hexdigest())
    if not all(r for run in runs for r in run['representable']):
        require(p.returncode == 2 and not p.stdout and p.stderr.decode().strip().endswith('inherits unknown slot state'), 'native accepted unrepresentable prefix inheritance')
        return identity | dict(outcome='native_rejected_unrepresented_inheritance')
    require(p.returncode == 0, 'native setup prefix failed: ' + p.stderr.decode())
    members = [(VARIANTS[run['variant']]['kinds'][k], *VARIANTS[run['variant']]['fields'][k](bytes.fromhex(f))) for run in runs for k, f in enumerate(run['finals'])]
    identities = (slots[0], slots[1], slots[9])
    want = (*(x for s in slots for x in (s, 1)), *(x for s in identities for x in (1, s, 1)), len(free) - len(slots), *free[:-len(slots)], *(x for m in members for x in m))
    require(tuple(map(int, p.stdout.split())) == want, 'native setup prefix differs')
    return identity | dict(outcome='matched', output_sha256=hashlib.sha256(p.stdout).hexdigest(), members=len(slots))


def validate_tail(events, pairs):
    """Each [68A4,68BC) run: 6A94 between BSR 68A4 and 68A8, then 6EB6 for P1
    (A5 = FF0690) and P2 (A5 = FF0838), from one stack with consecutive pops."""
    out = []; marks = [e for e in events if e['pc'] in TAIL]; at = lambda e: (e['frame'], e['sequence'])
    for i in [i for i, e in enumerate(marks) if e['pc'] == TAIL[0]]:
        seq = marks[i:i + len(TAIL)]
        if [e['pc'] for e in seq] != list(TAIL): continue  # 68A4 is also the prefix's last mark; only full tails count.
        sp = seq[0]['registers']['M68K A7']; require(all(e['registers']['M68K A7'] == sp for e in seq), 'setup tail stack differs')
        require([e['registers']['M68K A5'] for e in seq[2:]] == [0xffff0690, 0xffff0690, 0xffff0838, 0xffff0838], 'setup tail A5 differs')
        runs = []
        for name, lo, hi in (('pickups', seq[0], seq[1]), ('link_p1', seq[2], seq[3]), ('link_p2', seq[4], seq[5])):
            found = [p for p in pairs if p['variant'] == name and at(lo) < (p['frame'], p['entry_sequence']) and (p['return_frame'], p['return_sequence']) < at(hi)]
            require(len(found) == 1 and found[0]['entry_sp'] == sp - 4, f'setup tail {name} run differs')
            runs.append(found[0])
        expect = runs[0]['free_before']
        for run in runs: require(run['free_before'] == expect, 'setup tail pops are not consecutive'); expect = expect[:-len(run['members'])]
        out.append(dict(frame=seq[0]['frame'], return_frame=seq[-1]['frame'], sp=sp, free_before=runs[0]['free_before'], runs=runs,
                        slots=[a['slot'] for run in runs for a in run['members']]))
    return out


def run_writes(run): return pickup_writes(run) if run.get('variant') == 'pickups' else pair_writes(run)


def tail_writes(tail):
    """The [68A4,68BC) block: each BSR's return push, then that run's exact writes."""
    sp = tail['sp']; out = []
    for ret, run in zip((0x68a8, 0x68b2, 0x68bc), tail['runs']):
        out += [(ret, sp - 4 & 0xffffff, 4, ret), *run_writes(run)]
    return out


def compare_tail(native, tail, phases):
    """Native --tail-pool from the 68A4-entry stack, the 6A94-entry tables and
    verified inheritance, then the retained phases with observed 78EE/6BD6
    inputs. Native compares phases up to the first original 6C00 hit of a
    tail pickup and must reject exactly there; later phases are original-only."""
    runs = tail['runs']; free = tail['free_before']; slots = tail['slots']; pickups = [a['slot'] for a in runs[0]['members']]
    first_hit = next((i for i, q in enumerate(phases) if any(s in q[4] for s in pickups)), None)
    gone = next((i for i, q in enumerate(phases) if any(s not in q[1] for s in slots)), None)
    cut = min(x for x in (first_hit, gone, len(phases)) if x is not None)
    compared, after = phases[:cut], phases[cut:]; reject = first_hit is not None and first_hit == cut
    sent = compared + after[:1] if reject else compared
    t = runs[0]['tables']; table = (*t['kinds'], *t['counts'], *(v for xy in t['positions'] for v in xy))
    inherited = {a['slot']: residue_row(bytes.fromhex(a['residue'])) for run in runs for a in run['members']}
    rows = [(SLOTS, len(free), len(sent), LINKS[runs[0]['entry_registers']['M68K A5']]), tuple(free), *(inherited.get(i, (0,) if i in free else (1,)) for i in range(SLOTS)),
            table, *(q[3] for q in sent)]
    data = encode_cases(rows); p = subprocess.run([str(native), '--tail-pool'], input=data, capture_output=True, timeout=60)
    identity = dict(command=[str(native), '--tail-pool'], seed_sha256=hashlib.sha256(data).hexdigest())
    if not all(r for run in runs for r in run['representable']):
        require(p.returncode == 2 and not p.stdout and p.stderr.decode().strip().endswith('inherits unknown slot state'), 'native accepted unrepresentable tail inheritance')
        return identity | dict(outcome='native_rejected_unrepresented_inheritance')
    if reject: require(p.returncode == 2 and p.stderr.decode().strip() == 'unsupported pickup-hit 6C00 (primary)', 'native did not reject the first original 6C00 hit')
    else: require(p.returncode == 0, 'native setup tail failed: ' + p.stderr.decode())
    lines = [tuple(map(int, l.split())) for l in p.stdout.splitlines()]; require(len(lines) == 1 + len(compared), 'native setup tail output extent differs')
    kinds = {**{s: 9 for s in pickups}, slots[-2]: 8, slots[-1]: 8}
    fields = {s: pickup_fields if s in pickups else return_only_fields for s in slots}
    finals = {a['slot']: bytes.fromhex(f) for run in runs for a, f in zip(run['members'], run['finals'])}
    records = []
    for m in range(16):
        records += [1, pickups[m], 1, runs[0]['entries'][m]] if m < len(pickups) else [0, 0, 0, 0]
    want = (*(x for s in slots for x in (s, 1)), 1, slots[-2], 1, 1, slots[-1], 1, *records, len(free) - len(slots), *free[:-len(slots)],
            *(x for s in slots for x in (kinds[s], *fields[s](finals[s]))))
    require(lines[0] == want, 'native setup tail initialization differs')
    for (frame, phase, _gate, _collision, _hits, active), line in zip(compared, lines[1:]):
        expect = [(1 if active[i] else 3, i, 1, kinds[i], *phase[i]) for i in sorted(phase) if i in kinds]
        require(line == (len(expect), *(x for e in expect for x in e)), f'native setup tail differs at {frame}')
    bounded = dict(rejected_at_frame=after[0][0], original_only_phases=len(after)) if reject else dict(bounded_at_frame=after[0][0], original_only_phases=len(after)) if after else {}
    return identity | dict(outcome='matched', output_sha256=hashlib.sha256(p.stdout).hexdigest(), phases=len(compared), members=len(slots)) | bounded


PHASES = {0xfaa4: 1, 0x6cda: 2, 0x6cf4: 3}


def pickup_state(b):
    """A pickup at any phase: the eleven shared fields, control, extents, record
    and phase (collectable while +46 is 6BD6; otherwise its +1A callback)."""
    require(len(b) == 78 and be(b, 0x16, 4) == 0x12646 and b[1] == 0 and be(b, 0x14) == 0 and b[0x22:0x42] == bytes(32), 'unmodeled pickup bytes')
    phase = 0 if be(b, 0x46, 4) == PICKUP_SERVICE else PHASES.get(be(b, 0x1a, 4)) if be(b, 0x46, 4) == 0x12646 else None
    require(phase is not None, 'pickup phase selectors differ')
    record = be(b, 0x42, 4) - 0xffff447a; require(0 <= record < 192 and record % 12 == 0, 'pickup record differs')
    return (be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), be(b, 8), be(b, 10), b[12], b[13], be(b, 14), be(b, 16), be(b, 0x4a, 4), be(b, 0x1e), be(b, 0x20), record // 12, phase)


def link_state(b):
    """(kind, row fields) of a control link: a dormant return-only object, or a
    6D8C emitter carrying a pickup (+10 count, +42 record, +1E/+20 extents)."""
    common = (be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), be(b, 8), be(b, 10), b[12], b[13], be(b, 14), be(b, 16))
    if be(b, 0x16, 4) == 0x6d8c:
        require(be(b, 0x46, 4) == 0x12646 and b[1] == 0 and be(b, 0x14) == 0 and b[0x38:0x42] == bytes(10), 'unmodeled emitter link bytes')
        record = be(b, 0x42, 4) - 0xffff447a; require(0 <= record < 192 and record % 12 == 0, 'emitter record differs')
        return 1, (*common, be(b, 0x36), *(be(b, 0x22 + 2 * h) for h in range(10)), be(b, 0x4a, 4), be(b, 0x1e), be(b, 0x20), record // 12)
    require(be(b, 0x16, 4) == 0x12646 and be(b, 0x46, 4) == 0x12646 and b[0] == 0, 'control link is neither dormant nor a carrying emitter')
    return 0, (*common, be(b, 0x4a, 4))


def link_output(b):
    kind, fields = link_state(b)
    return (kind, *fields) if kind else (0, *fields[:11], fields[11])


def record_entries(raw):
    out = []
    for r in range(16):
        obj, a0 = be(raw, 12 * r, 4), be(raw, 12 * r + 4, 4)
        require(not obj or (0xffff312c <= a0 < 0xffff314c and a0 % 2 == 0), 'record entry pointer differs'); out.append((obj, (a0 - 0xffff312c) // 2 if obj else 16))
    return out


def hit_row(pickup, s, links, records, kinds, inputs, walks=1):
    """The 115-field authored --pickup-hit row for one original walk; holders
    must match the transport's derivation (emitter records, then the pickup's
    record, then any other object)."""
    p = pickup_state(pickup); states = [link_state(b) for _slot, b in links]; entries = record_entries(records)
    emitter_records = {k: f[-1] for k, (kind, f) in enumerate(states) if kind}
    for r, (obj, entry) in enumerate(entries):
        if not obj: require(r != p[14] and r not in emitter_records.values(), 'a held record is absent'); continue
        holder = next((address(links[k][0]) for k, er in emitter_records.items() if er == r), address(s) if r == p[14] else None)
        require(obj == holder if holder else obj not in (address(s), *(address(sl) for sl, _b in links)), 'record holder outside the transport derivation')
    rows = [*p[:15], s, links[0][0], links[1][0], states[0][0], states[1][0]]
    for kind, f in states: rows += f if kind else (*f[:11], 0, *(0,) * 10, f[11], 0, 0, 0)
    rows += [be(kinds, 2 * k) for k in range(16)] + [entry for _obj, entry in entries]
    return (*rows, *inputs, 0, walks, 0, p[15])


def hit_output(pickup, s, links, records, released, sounds):
    """Expected --pickup-hit output from the original's post-walk bytes."""
    holders = {address(s): 1, address(links[0][0]): 2, address(links[1][0]): 3}
    out = (1, int(released), *pickup_state(pickup)[:11], *pickup_state(pickup)[11:])
    for _slot, b in links: out += link_output(b)
    for obj, entry in record_entries(records): out += (holders.get(obj, 4) if obj else 0, entry)
    out += (len(sounds), *(w for q in sounds for w in q), int(released), s if released else 99)
    return out


def pickup_walks(frames, boundaries):
    """Every ordinary 6C00 hit and every later walk of a hit pickup until its
    FAA4 release (or END). Each walk yields the native row and expected output:
    the pickup's 69AA-entry and 69C2-exit bytes, the touched link at 6C48 and
    after the hit, the other link and its records/kinds, the 78EE inputs and the
    FCB32 requests. Consecutive walks must chain: exit equals the next entry.
    An untouched link is supplied as it stood at the frame start and is only
    echoed: it is context, not compared state."""
    hits = sorted({(f, e['registers']['M68K A6']) for f, es in frames.items() for e in es if e['pc'] == PICKUP_HIT})
    followed = {}; walks = []
    for frame in sorted(f for f in frames if f >= SWITCH):
        es = frames[frame]; starts = [e for e in es if e['pc'] == 0x69a4]; ends = [e for e in es if e['pc'] == 0x69ce]
        if not starts: continue
        inside = [e for e in es if starts[0]['sequence'] < e['sequence'] < ends[0]['sequence']]
        for target in sorted({a for f, a in hits if f == frame} | set(followed)):
            s = slot(target); mine = [e for e in inside if e['registers']['M68K A6'] == target]
            begin = [e for e in mine if e['pc'] == 0x69aa]; done = [e for e in mine if e['pc'] == 0x69c2]
            require(len(begin) == len(done) == 1, 'hit pickup walk cadence differs')
            window = [e for e in inside if begin[0]['sequence'] <= e['sequence'] <= done[0]['sequence']]
            entry, exit_ = block(begin[0], 'object'), block(done[0], 'object')
            if target in followed: require(entry == followed[target], 'hit pickup changed between walks')
            link_slots = [slot(be(block(begin[0], f'link{k}'), 0, 4)) for k in (0, 1)]
            before = {k: bytes.fromhex(boundaries[str(frame)]['slots'][str(l)]) for k, l in enumerate(link_slots)}
            after = dict(before); hit = [e for e in window if e['pc'] == PICKUP_HIT]
            if hit:
                linked = [e for e in window if e['pc'] == PICKUP_LINKED]; finished = [e for e in window if e['pc'] in PICKUP_DONE]
                require(len(hit) == len(linked) == len(finished) == 1, 'pickup hit path differs')
                k = 0 if hit[0]['registers']['M68K A5'] == 0xffff0690 else 1; require(hit[0]['registers']['M68K A5'] == (0xffff0690, 0xffff0838)[k], 'hit control differs')
                require(slot(linked[0]['registers']['M68K A4']) == link_slots[k], 'hit link differs from +1A2')
                before[k], after[k] = block(linked[0], 'linked'), block(finished[0], 'linked')
            sounds = [tuple(be(block(e, 'mailbox'), 2 * i) for i in range(4)) for e in window if e['pc'] == SOUND and e['registers']['M68K A6'] == target]
            released = [e for e in window if e['pc'] == 0xfaa4 and e['registers']['M68K A6'] == target]
            links = [(link_slots[j], before[j]) for j in (0, 1)]; links_after = [(link_slots[j], after[j]) for j in (0, 1)]
            row = hit_row(entry, s, links, block(begin[0], 'records'), block(begin[0], 'kinds'), collision_inputs(begin[0]))
            want = hit_output(exit_, s, links_after, block(done[0], 'records'), bool(released), sounds)
            walks.append(dict(frame=frame, slot=s, hit=bool(hit), released=bool(released), row=row, want=want,
                              phase_before=pickup_state(entry)[15], phase_after=pickup_state(exit_)[15], sounds=len(sounds)))
            if released: followed.pop(target, None)
            else: followed[target] = exit_
    return walks


def compare_pickup_walks(native, walks):
    """All hit and post-hit walks in one native --pickup-hit run, one row each."""
    data = encode_cases([w['row'] for w in walks]); p = subprocess.run([str(native), '--pickup-hit'], input=data, capture_output=True, timeout=60)
    require(p.returncode == 0, 'native pickup walks failed: ' + p.stderr.decode())
    got = [tuple(map(int, l.split())) for l in p.stdout.splitlines()]; require(len(got) == len(walks), 'native pickup walk extent differs')
    for w, g in zip(walks, got): require(g == w['want'], f'native pickup walk differs at frame {w["frame"]} slot {w["slot"]}')
    return dict(command=[str(native), '--pickup-hit'], seed_sha256=hashlib.sha256(data).hexdigest(), output_sha256=hashlib.sha256(p.stdout).hexdigest(), outcome='matched',
                walks=len(walks), hits=sum(w['hit'] for w in walks), releases=sum(w['released'] for w in walks))


def sparkle_state(b):
    """A 59AE sparkle: the ten TrailParticle fields (callback FAA4, RTS selectors)."""
    require(len(b) == 78 and be(b, 0x16, 4) == 0x12646 and be(b, 0x46, 4) == 0x12646 and be(b, 0x1a, 4) == 0xfaa4 and be(b, 0x14) == 0, 'unmodeled sparkle bytes')
    return (be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), be(b, 8), be(b, 10), b[12], b[13], be(b, 14))


def delivered_state(b):
    """A 7910 copy: the eleven fields, +4A, +22/+26, extents and record (callback 79B6, RTS selectors)."""
    require(len(b) == 78 and be(b, 0x16, 4) == 0x12646 and be(b, 0x46, 4) == 0x12646 and be(b, 0x1a, 4) == DELIVERED_CALLBACK and b[1] == 0 and be(b, 0x14) == 0,
            'unmodeled delivered copy bytes')
    record = be(b, 0x42, 4) - 0xffff447a; require(0 <= record < 192 and record % 12 == 0, 'delivered copy record differs')
    return (be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), be(b, 8), be(b, 10), b[12], b[13], be(b, 14), be(b, 16), be(b, 0x4a, 4), be(b, 0x22), be(b, 0x26),
            be(b, 0x1e), be(b, 0x20), record // 12)


# FF0690/FF0838 +46 codes in the --ingredient transport's order.
INGREDIENT_MESSAGES = {0xffffffff: 0, 0xd28c: 1, 0xd2a2: 2, 0xd20e: 3, 0xd22f: 4}
# Table-object bytes 7A88 and F76C may write (mode, position, frame, counter,
# countdown, cursor, +32, +36).
TABLE_WRITES = (0, 2, 3, 4, 5, 6, 7, 12, 0x10, 0x11, 0x2e, 0x2f, 0x30, 0x31, 0x32, 0x33, 0x36, 0x37)


def table_state(b, live=True):
    """A 7A88 table object: the eleven fields, +4A, the 7A58 cursor index, +32
    and +36 (handler 7A88, service 12646; a live one keeps callback 79B6)."""
    cursor = be(b, 0x2e, 4)
    require(len(b) == 78 and be(b, 0x16, 4) == 0x7a88 and be(b, 0x46, 4) == 0x12646 and 0x7a58 <= cursor < 0x7a88 and cursor % 2 == 0 and (not live or be(b, 0x1a, 4) == DELIVERED_CALLBACK),
            'unmodeled table object bytes')
    return (be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), be(b, 8), be(b, 10), b[12], b[13], be(b, 14), be(b, 16), be(b, 0x4a, 4), (cursor - 0x7a58) // 2, be(b, 0x32), be(b, 0x36))


def cb9a_vram(writes, frame):
    """The VRAM word address of the CB9A row clear the frame's write trace reports, or None."""
    record, = [r for r in writes if r['frame'] == frame]; require(record['dropped'] == 0, f'write trace incomplete at {frame}')
    device = [(w['address'], w['width'], w['value']) for w in record['events'] if any(lo <= w['pc'] < hi for lo, hi in MESSAGE_CODE) and 0xc00000 <= w['address'] < 0xc00008]
    if not device: return None
    words = [(a, v) for a, w, v in device for a, v in (((a, v >> 16), (a + 2, v & 65535)) if w == 4 else ((a, v),))]
    require(len(words) == 30 and words[0] == (0xc00004, 0x8004) and words[-1] == (0xc00004, 0x8014) and words[1][0] == 0xc00004 and words[2][0] == 0xc00006
            and words[3:29] == [(0xc00000, 1)] * 26, 'CB9A VDP sequence differs')
    command = words[1][1] << 16 | words[2][1]; require(command & 0xc000fffc == 0x40000000, 'CB9A VDP command differs')
    return (command >> 16 & 0x3fff) | (command & 3) << 14


def walk_windows(frame, es):
    """(begin, done, window) of every 69AA..69C2 walk inside the frame's object loop."""
    starts = [e for e in es if e['pc'] == 0x69a4]; ends = [e for e in es if e['pc'] == 0x69ce]
    if not starts: return []
    require(len(starts) == len(ends) == 1, f'object loop cadence differs at {frame}')
    inside = [e for e in es if starts[0]['sequence'] < e['sequence'] < ends[0]['sequence']]
    marks = [i for i, e in enumerate(inside) if e['pc'] in (0x69aa, 0x69c2)]
    require([inside[i]['pc'] for i in marks] == [0x69aa, 0x69c2] * (len(marks) // 2), f'object walk marks differ at {frame}')
    return [(inside[a], inside[b], inside[a:b + 1]) for a, b in zip(marks[0::2], marks[1::2])]


def probe_walks(frames, boundaries, writes=None):
    """Every ordinary 7910 hit walk of a 78EE probe and every later walk of the
    objects a delivery creates, to the sparkle's FAA4 release, the copy's 79B6
    callback or END. A hit yields the --probe-hit row and expected output: the
    probe's 69AA-entry/69C2-exit bytes, the touched link at 7922 and (after a
    delivery) at 79B2, the other link at the frame start (context, echoed),
    FF31B0, the 78EE inputs, the free stack at entry and exit (a delivery pops
    its top two), the sparkle at 7976, the copy at 79B2 and the FCB32 requests.
    A later walk yields a --delivered row; consecutive walks must chain, and
    bytes the native types do not represent must not change. The copy's walk
    that reaches 79B6 yields an --ingredient row (FF31AC..FF31BF, the control's
    message fields, the tilemap and the records at entry; the FF31B4 object
    after FB06 at the FAA4 call; the CB9A row clear from the write trace); the
    FF31B4 object is then followed as a table object (wiznliz-table-motion
    --scheduled rows with FF31BC at each walk's entry). A delivered link must
    stay byte-identical until its next 6C00 use (6C48)."""
    hits = []; later = []; followed = {}; dormant = []; activations = []
    for frame in sorted(f for f in frames if f >= SWITCH):
        for begin, done, window in walk_windows(frame, frames[frame]):
            target = begin['registers']['M68K A6']; s = slot(target); hit = [e for e in window if e['pc'] == HIT]
            entry, exit_ = block(begin, 'object'), block(done, 'object')
            free_before, free_after = free_fields(block(begin, 'free')), free_fields(block(done, 'free'))
            if hit:
                require(len(hit) == 1 and s not in followed, 'probe hit path differs')
                k = 0 if hit[0]['registers']['M68K A5'] == 0xffff0690 else 1; require(hit[0]['registers']['M68K A5'] == (0xffff0690, 0xffff0838)[k], 'probe hit control differs')
                link_slots = [slot(be(block(begin, f'link{j}'), 0, 4)) for j in (0, 1)]
                before = {j: bytes.fromhex(boundaries[str(frame)]['slots'][str(l)]) for j, l in enumerate(link_slots)}; after = dict(before)
                linked = [e for e in window if e['pc'] == PROBE_LINKED]; sparkles = [e for e in window if e['pc'] == PROBE_SPARKLE]; finished = [e for e in window if e['pc'] == PROBE_DONE]
                returns = [e for e in window if e['pc'] in PROBE_RETURNS and e['registers']['M68K A6'] == target]
                sounds = [tuple(be(block(e, 'mailbox'), 2 * i) for i in range(4)) for e in window if e['pc'] == SOUND and e['registers']['M68K A6'] == target]
                rise = be(block(begin, 'rise'), 0, 4); created = []
                require(len(linked) <= 1 and len(sparkles) == len(finished) == len(sounds) <= len(linked) and len(returns) == 1, 'probe hit marks differ')
                if linked:
                    require(slot(linked[0]['registers']['M68K A4']) == link_slots[k], 'probe hit link differs from +1A2'); before[k] = block(linked[0], 'linked')
                if finished:
                    sparkle, link_done, copy = block(sparkles[0], 'object'), block(finished[0], 'object'), block(finished[0], 'linked')
                    ss, cs = slot(sparkles[0]['registers']['M68K A6']), slot(finished[0]['registers']['M68K A4'])
                    require(slot(finished[0]['registers']['M68K A6']) == link_slots[k] and free_before[-2:] == [cs, ss] and free_after == free_before[:-2], 'delivery pops differ')
                    require(copy[0] == 0x87 and link_done[0] == 0 and copy[1:] == link_done[1:], 'delivery copy differs from its link')
                    after[k] = link_done; created = [(0, ss, sparkle), (1, cs, copy)]
                    followed[ss] = (0, sparkle); followed[cs] = (1, copy); dormant.append(dict(frame=frame, slot=link_slots[k], state=link_done))
                else: require(free_after == free_before, 'probe hit free stack changed')
                # The row names the top two free slots; with fewer entries (no
                # delivery is then possible) unused slots fill the unpushed places.
                picks = [*reversed(free_before), *(i for i in range(SLOTS) if i not in (s, *link_slots, *free_before))]
                links = [(link_slots[j], before[j]) for j in (0, 1)]; states = [link_state(b) for _l, b in links]
                row = [*probe_fields(entry)[:11], be(entry, 0x4a, 4), be(entry, 0x1e), be(entry, 0x20), s, *link_slots, states[0][0], states[1][0]]
                for kind, f in states: row += f if kind else (*f[:11], 0, *(0,) * 10, f[11], 0, 0, 0)
                row += [rise >> 16, rise & 0xffff, *collision_inputs(begin), len(free_before), picks[0], picks[1], 1, 0, 0]
                want = (1, *probe_fields(exit_)[:11], be(exit_, 0x4a, 4), be(exit_, 0x1e), be(exit_, 0x20))
                for j in (0, 1): want += link_output(after[j])
                want += (len(created),)
                for kind, cslot, b in created: want += (kind, cslot, *(delivered_state(b) if kind else sparkle_state(b)))
                want += (len(sounds), *(w for q in sounds for w in q), len(free_after))
                hits.append(dict(frame=frame, slot=s, row=tuple(row), want=want, delivered=bool(created), gated=bool(rise), sounds=len(sounds), created=[c[1] for c in created]))
            elif s in followed and followed[s][0] == 2:
                _kind, previous = followed[s]; require(entry == previous, 'table object changed between walks')
                require(all(entry[i] == exit_[i] for i in range(78) if i not in TABLE_WRITES) and not [e for e in window if e['pc'] == DELIVERED_CALLBACK], 'table walk changed an unrepresented byte')
                loop = be(block(begin, 'ingredient'), 0x10)
                later.append(dict(frame=frame, slot=s, kind=2, mode='--scheduled', row=(*table_state(entry), loop, 1, 4096), want=(6, *table_state(exit_)), released=False, callback=False,
                                  released_in_callback=False))
                followed[s] = (2, exit_)
            elif s in followed:
                kind, previous = followed[s]; require(entry == previous, 'delivered object changed between walks')
                callback = [e for e in window if e['pc'] == DELIVERED_CALLBACK and e['registers']['M68K A6'] == target]
                released = [e for e in window if e['pc'] == 0xfaa4 and e['registers']['M68K A6'] == target]
                fields = delivered_state(entry) if kind else (*sparkle_state(entry), *(0,) * 7)
                row = (kind, *fields, s, len(free_before), 1); mode = '--delivered'
                if callback:
                    require(kind == 1 and len(callback) == 1 and writes is not None, 'delivered callback path differs')
                    g0, g1 = block(begin, 'ingredient'), block(done, 'ingredient'); control = be(entry, 0x4a, 4)
                    label = {0xffff0690: 'message', 0xffff0838: 'message2'}[control]; m0, m1 = block(begin, label), block(done, label)
                    r = fields[16]; holder, entry_index = record_entries(block(begin, 'records'))[r]
                    require(be(g0, 0, 4) == 0 and be(m0, 0, 4) in INGREDIENT_MESSAGES, 'unmodeled first-ingredient inputs')
                    tilemap = be(block(begin, 'tilemap'), 0, 4); t = slot(be(g0, 8, 4))
                    row = (*fields, s, t, slot(holder), entry_index, 0, INGREDIENT_MESSAGES[be(m0, 0, 4)], m0[0x0d], be(m0, 0x10), tilemap >> 16, tilemap & 0xffff,
                           be(g0, 0x10), be(g0, 0x12), len(free_before), 1)
                    mode = '--ingredient'
                    copied, = [e for e in window if e['pc'] == 0xfaa4 and e['registers']['M68K A6'] == target]; table = block(copied, 'linked')
                    require(slot(copied['registers']['M68K A4']) == t and table[0] == 0x81, 'first-ingredient copy differs')
                    after = record_entries(block(done, 'records'))[r]; vram = cb9a_vram(writes, frame)
                    require((vram is not None) == any(e['pc'] == 0xcb9a for e in window) and len(free_after) == len(free_before) + 1 and free_after[-1] == s, 'first-ingredient path differs')
                    want = (1, 1, 1, *table_state(exit_, live=False), *table_state(table), slot(be(g1, 0, 4)), slot(after[0]), after[1], INGREDIENT_MESSAGES[be(m1, 0, 4)], m1[0x0d],
                            be(m1, 0x10), int(vram is not None), *(() if vram is None else (vram,)), be(g1, 0x10), be(g1, 0x12), len(free_after))
                    followed.pop(s); followed[t] = (2, table); activations.append(dict(frame=frame, copy=s, target=t, shown=vram is not None, vram=vram))
                else:
                    require(all(entry[i] == exit_[i] for i in range(78) if i not in (0, 6, 7, 12)), 'delivered walk changed an unrepresented byte')
                    require(len(free_after) == len(free_before) + bool(released) and (not released or free_after[-1] == s), 'delivered walk free stack differs')
                    want = (1, int(bool(released)), *(delivered_state(exit_) if kind else (*sparkle_state(exit_), *(0,) * 7)), len(free_after))
                    if released: followed.pop(s)
                    else: followed[s] = (kind, exit_)
                # A release inside the copy's 79B6 work (7AD6) is unsupported work, not a native release.
                later.append(dict(frame=frame, slot=s, kind=kind, mode=mode, row=row, want=want, released=bool(released) and not callback, callback=bool(callback),
                                  released_in_callback=bool(released) and bool(callback)))
    # Each delivered link stays dormant and unchanged until its next 6C00 use.
    uses = sorted((f, slot(e['registers']['M68K A4'])) for f, es in frames.items() for e in es if e['pc'] == PICKUP_LINKED)
    for d in dormant:
        reuse = next((f for f, l in uses if l == d['slot'] and f > d['frame']), END)
        require(all(bytes.fromhex(boundaries[str(f)]['slots'][str(d['slot'])]) == d['state'] for f in range(d['frame'] + 1, reuse + 1)), 'delivered link changed before reuse')
        d['unchanged_through'] = reuse; del d['state']
    return hits, later, dormant, activations


def compare_probe_walks(native, table, hits, later):
    """Every 7910 hit walk in one native --probe-hit run, every later walk of the
    created objects in one --delivered run, the 79B6 walks in one --ingredient
    run and the FF31B4 table object's walks in one wiznliz-table-motion
    --scheduled run, one row each."""
    out = {}
    for mode, rows in (('--probe-hit', hits), *((m, [w for w in later if w['mode'] == m]) for m in ('--delivered', '--ingredient', '--scheduled'))):
        if not rows: continue
        exe = table if mode == '--scheduled' else native
        data = encode_cases([w['row'] for w in rows]); p = subprocess.run([str(exe), mode], input=data, capture_output=True, timeout=60)
        require(p.returncode == 0, f'native {mode} walks failed: ' + p.stderr.decode())
        got = [tuple(map(int, l.split())) for l in p.stdout.splitlines()]; require(len(got) == len(rows), f'native {mode} walk extent differs')
        for w, g in zip(rows, got): require(g == w['want'], f'native {mode} walk differs at frame {w["frame"]} slot {w["slot"]}')
        out[mode[2:]] = dict(command=[str(exe), mode], seed_sha256=hashlib.sha256(data).hexdigest(), output_sha256=hashlib.sha256(p.stdout).hexdigest(), walks=len(rows))
    return dict(outcome='matched', **out, hits=len(hits), deliveries=sum(h['delivered'] for h in hits), releases=sum(w['released'] for w in later), callbacks=sum(w['callback'] for w in later),
                table_walks=sum(w['kind'] == 2 for w in later))


def message_model(entry):
    """7DB8 then CB72 from the 7DB8-entry state: (selected, final +46 code or None
    when untouched, final +53, final FF31AA, shown)."""
    two = be(block(entry, 'two_player'), 0); returned = be(block(entry, 'returned'), 0); m = block(entry, 'message'); priority = m[0x53 - 0x46]
    kinds = [be(block(entry, 'kinds'), 2 * k) for k in range(16)]
    selected = 0 if two else 2 if returned else 1 if sum(k != 0xffff for k in kinds) >= 2 else 0
    if not selected: return 0, None, priority, returned, False
    shown = not 0x64 < (priority ^ 0x80) - 0x80
    return selected, selected if shown else 0, 0x64 if shown else priority, 0 if selected == 2 else returned, shown


def validate_message(events, writes):
    """Each [68BC,68C4) run: 7DB8 between BSR 68BC and 68C0, 6EF0 between 68C0 and
    68C4, one stack. The model decides +46/+53/FF31AA and whether CB9A runs; RAM
    writes by 7DB8/CB72/CB9A are exactly the model's; CB9A's device words, when
    the trace reports them, are its exact VDP sequence; FF010C is restored."""
    out = []; marks = [e for e in events if e['pc'] in MESSAGE or e['pc'] in MESSAGE_PCS]; at = lambda e: (e['frame'], e['sequence'])
    for i in [i for i, e in enumerate(marks) if e['pc'] == MESSAGE[0]]:
        sp = marks[i]['registers']['M68K A7']; seq = [marks[i]] + [e for e in marks[i + 1:] if e['pc'] in MESSAGE[1:]][:2]
        if [e['pc'] for e in seq] != list(MESSAGE) or any(e['registers']['M68K A7'] != sp for e in seq): continue  # 68BC is also the tail's last mark.
        inner = [e for e in marks if at(seq[0]) < at(e) < at(seq[-1]) and e['pc'] in MESSAGE_PCS]
        entry = inner[0]; require(entry['pc'] == 0x7db8 and entry['registers']['M68K A7'] == sp - 4, 'setup message 7DB8 entry differs')
        selected, code, priority, returned, shown = message_model(entry)
        pcs = [e['pc'] for e in inner]
        require((0x7dec in pcs) == (selected == 1) and (0x7e08 in pcs) == (selected == 2) and (0xcb9a in pcs) == shown and (0xcb8c in pcs) == (bool(selected) and not shown), 'setup message path differs')
        require(0x6ef0 in pcs and 0x6f00 in pcs and 0x6f02 not in pcs, 'setup message 6EF0 path differs')
        done = seq[-1]; m = block(done, 'message'); m0 = block(entry, 'message')
        final = MESSAGES.get(be(m, 0, 4)) if code is not None else None
        require((final if code is not None else be(m, 0, 4) == be(m0, 0, 4)) == (code if code is not None else True), 'setup message +46 differs')
        require(m[0x53 - 0x46] == priority and be(block(done, 'returned'), 0) == returned and block(done, 'lock') == block(entry, 'lock'), 'setup message +53/FF31AA/FF010C differ')
        frames = {e['frame'] for e in [seq[0], seq[-1]]}; ws = [w for r in writes if r['frame'] in frames for w in r['events'] if any(lo <= w['pc'] < hi for lo, hi in MESSAGE_CODE)]
        require(all(r['dropped'] == 0 for r in writes if r['frame'] in frames), 'setup message write trace incomplete')
        # The routines' own register saves and returns land just below the fragment's SP.
        stack = (sp - 0x80 & 0xffffff, sp & 0xffffff)
        ram = [(w['pc'], w['address'], w['width'], w['value']) for w in ws if w['address'] >= 0xff0000 and not stack[0] <= w['address'] < stack[1]]
        device = [(w['address'], w['width'], w['value']) for w in ws if 0xc00000 <= w['address'] < 0xc00008]
        want = [(0x7e02, 0xff31aa, 2, 0)] if selected == 2 else []
        if selected: want.append((0x7df4 if selected == 1 else 0x7e10, 0xff06d6, 4, 0xd28c if selected == 1 else 0xd2a2))
        if shown: want += [(0xcb86, 0xff06e3, 1, 0x64), (0xcbb0, 0xff010c, 2, 1), (0xcc06, 0xff010c, 2, be(block(entry, 'lock'), 0))]
        elif selected: want.append((0xcb94, 0xff06d6, 4, 0xffffffff))
        require(ram == want, 'setup message RAM writes differ')
        vram = None
        if device:
            words = [(a, v) for a, w, v in device for a, v in (((a, v >> 16), (a + 2, v & 65535)) if w == 4 else ((a, v),))]
            require(len(words) == 30 and words[0] == (0xc00004, 0x8004) and words[-1] == (0xc00004, 0x8014) and words[1][0] == 0xc00004 and words[2][0] == 0xc00006
                    and words[3:29] == [(0xc00000, 1)] * 26, 'setup message VDP sequence differs')
            command = words[1][1] << 16 | words[2][1]; require(command & 0xc000fffc == 0x40000000, 'setup message VDP command differs')
            vram = (command >> 16 & 0x3fff) | (command & 3) << 14
        require(not device or shown, 'setup message device writes without CB9A')
        out.append(dict(frame=seq[0]['frame'], sp=sp, selected=selected, code=code, priority=priority, returned=returned, shown=shown, ram_writes=len(ram),
                        device_writes=len(device), vram=vram, inputs=dict(two_player=be(block(entry, 'two_player'), 0), returned=be(block(entry, 'returned'), 0),
                        pair_request=be(block(entry, 'pair_request'), 0), tilemap=be(block(entry, 'tilemap'), 0, 4), code_before=INGREDIENT_MESSAGES.get(be(m0, 0, 4)), priority=m0[0x53 - 0x46], row=be(m0, 0x56 - 0x46),
                        kinds=[be(block(entry, 'kinds'), 2 * k) for k in range(16)])))
    return out


def compare_message(native, message):
    """Native --message from the 7DB8-entry inputs against the original's result;
    the VRAM word is compared when the trace reported CB9A's command."""
    x = message['inputs']; row = (x['two_player'], x['returned'], x['pair_request'], x['tilemap'], x['priority'], x['row'], *x['kinds'])
    data = encode_cases([row]); p = subprocess.run([str(native), '--message'], input=data, capture_output=True, timeout=10)
    require(p.returncode == 0, 'native setup message failed: ' + p.stderr.decode())
    got = tuple(map(int, p.stdout.split()))
    want = (1, message['selected'], 3 if message['code'] is None else message['code'], message['priority'], message['returned'], int(message['shown']))
    require(got[:6] == want and (message['vram'] is None or got[6] == message['vram']), 'native setup message differs')
    return dict(command=[str(native), '--message'], seed_sha256=hashlib.sha256(data).hexdigest(), outcome='matched', native_vram=got[6],
                vram_compared=message['vram'] is not None)


def gated_write(pc):
    """Writes reported by the [68C4,68D4) BSRs (their return PCs) or inside the four initializers."""
    return pc in GATED[1:] or any(lo < pc <= hi for lo, hi in GATED_CODE)


def validate_gated(events, writes):
    """Each [68C4,68D4) run: the four BSR marks at one stack, each initializer
    entered at SP - 4 between its BSR and the next mark. The ordinary movie only
    supports closed gates: entry then RTS, no F9E2 call and an unchanged free
    stack. The frame's writes by these PCs are exactly the four return pushes."""
    out = []; at = lambda e: (e['frame'], e['sequence'])
    inner_pcs = {pc for pcs in GATED_PCS for pc in pcs}; marks = [e for e in events if e['pc'] in GATED or e['pc'] in inner_pcs]
    for i in [i for i, e in enumerate(marks) if e['pc'] == GATED[0]]:
        sp = marks[i]['registers']['M68K A7']; seq = [marks[i]] + [e for e in marks[i + 1:] if e['pc'] in GATED[1:]][:4]
        if [e['pc'] for e in seq] != list(GATED) or any(e['registers']['M68K A7'] != sp for e in seq): continue  # 68C4 is also the message step's last mark.
        inner = [e for e in marks if at(seq[0]) < at(e) < at(seq[-1]) and e['pc'] in inner_pcs]
        require([e['pc'] for e in inner] == [pc for entry, ret, _open in GATED_PCS for pc in (entry, ret)], 'gated pair path differs (open gate or interleaving)')
        require(all(e['registers']['M68K A7'] == sp - 4 for e in inner), 'gated pair stack differs')
        gates = [be(block(inner[2 * k], 'pair_gates'), 2 * k) for k in range(4)]
        require(not any(gates) and all(block(e, 'pair_gates') == block(inner[0], 'pair_gates') for e in inner), 'gated pair gate differs from its closed path')
        require(not any(e['pc'] == 0xf9e2 and at(seq[0]) < at(e) < at(seq[-1]) for e in events), 'gated pair step allocated')
        free = free_fields(block(seq[0], 'free')); require(free_fields(block(seq[-1], 'free')) == free, 'gated pair step changed the free stack')
        require(registers(seq[-1]) == registers(seq[0]), 'gated pair step changed a register')
        frames = sorted({seq[0]['frame'], seq[-1]['frame']}); records = [r for r in writes if r['frame'] in frames]
        require(all(r['dropped'] == 0 for r in records), 'gated pair write trace incomplete')
        events_w = [w for r in records for w in r['events']]; skip, interrupts = exception_frames(events_w)
        ws = [(w['pc'], w['address'], w['width'], w['value']) for k, w in enumerate(events_w) if gated_write(w['pc']) and k not in skip]
        require(ws == [(pc, sp - 4 & 0xffffff, 4, pc) for pc in GATED[1:]], 'gated pair writes differ')
        origin = block(inner[0], 'p2_origin')
        out.append(dict(frame=seq[0]['frame'], return_frame=seq[-1]['frame'], sp=sp, a5=seq[0]['registers']['M68K A5'], gates=gates,
                        p2_origin=[be(origin, 0), be(origin, 2)], free_before=free, writes=len(ws), interrupt_frames=interrupts))
    return out


def compare_gated(native, x):
    """Native --pairs-pool from the 68C4-entry gates, caller A5 and free stack:
    every gate closed, so nothing is allocated and the stack is unchanged."""
    require(x['a5'] in LINKS, 'unmapped 68C4 caller identity')
    rows = [(SLOTS, len(x['free_before']), 0, LINKS[x['a5']], LINKS[0xffff0690], *x['gates'], *x['p2_origin']), tuple(x['free_before'])]
    rows += [(0,) if i in x['free_before'] else (1,) for i in range(SLOTS)]
    data = '\n'.join(' '.join(map(str, r)) for r in rows).encode() + b'\n'
    p = subprocess.run([str(native), '--pairs-pool'], input=data, capture_output=True, timeout=10)
    require(p.returncode == 0, 'native gated pairs failed: ' + p.stderr.decode())
    require(tuple(map(int, p.stdout.split())) == (len(x['free_before']), *x['free_before']), 'native gated pairs differ')
    return dict(command=[str(native), '--pairs-pool'], seed_sha256=hashlib.sha256(data).hexdigest(), outcome='matched', allocated=0)


def write_record(frame, drain):
    keep = CONTRACTED
    events = [w for w in drain['events'] if w['type'] == 4 and (w['pc'] in keep or 0xff1b50 <= w['address'] < 0xff3120 or ANCHOR <= w['address'] < ANCHOR + 4
              or DORMANT <= w['address'] < DORMANT + 8 or 0xff31ac <= w['address'] < 0xff31b4 or 0xff31bc <= w['address'] < 0xff31c0 or 0xff447a <= w['address'] < 0xff453a
              or 0xff0bac <= w['address'] < 0xff0bb4
              or any(at <= w['address'] < at + 4 for at in LINKS_AT) or any(lo <= w['pc'] < hi for lo, hi in MESSAGE_CODE) or gated_write(w['pc']))]
    raw = json.dumps(drain['events'], sort_keys=True).encode()
    return dict(frame=frame, count=sum(w['type'] == 4 for w in drain['events']), dropped=drain['dropped'], raw_sha256=hashlib.sha256(raw).hexdigest(), events=events)


def boundary(w):
    """The pool, free-stack head, FF31B4..FF31C3 identities and both +1A2 links at a frame boundary."""
    ram = w.read_bytes('68K RAM', 0x1b50, 0x31c4 - 0x1b50)
    return dict(sha256=hashlib.sha256(ram).hexdigest(), anchor=ram[0x31c0 - 0x1b50:].hex(), head=ram[0x311c - 0x1b50:0x3120 - 0x1b50].hex(),
                dormant=ram[0x31b4 - 0x1b50:0x31bc - 0x1b50].hex(), links=(w.read_bytes('68K RAM', LINKS_AT[0] & 65535, 4) + w.read_bytes('68K RAM', LINKS_AT[1] & 65535, 4)).hex(),
                slots={str(i): ram[i * STRIDE:(i + 1) * STRIDE].hex() for i in range(SLOTS)})


def capture(source, out, ext):
    sys.path.insert(0, str(ext / 'python'))
    from genesis_debug import WorkerClient, ReplaySession
    routines = []; writes = []; boundaries = {}
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'hooked-worker')]) as w:
        s = ReplaySession.from_recording(w, source); identity = s.opened['identity']; save(out / 'capabilities.json', check_worker(w, s, ext))
        require(identity == source['start']['worker_open']['identity'], 'pair loaded identity differs')
        w.request('trace.configure', recipe(False)); w.request('debug.trace.configure', {'mask': 4})
        for frame in range(END):
            if frame == SWITCH: w.request('trace.configure', recipe(True))
            s.seek(frame + 1); t = w.request('trace.drain'); wr = w.request('debug.trace.drain')
            require(t['dropped'] == 0 and t['overflow'] is False and t['error'] is None and t['identity'] == identity, f'pair routine trace loss at {frame}')
            require(wr['identity'] == identity and all(e['frame'] == frame for e in t['events']), 'pair trace frame/identity differs')
            if t['events']: routines.append(dict(frame=frame, events=t['events']))
            writes.append(write_record(frame, wr))
            boundaries[str(frame + 1)] = boundary(w)
        snap = w.request('snapshot'); end_ram = w.read_bytes('68K RAM', 0, 65536)
    # The closed worker's per-seek replay checkpoints are reconstructible from
    # the recording and are not evidence; remove only this owned directory.
    storage = (out / 'hooked-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage')
    removed = dict(files=sum(1 for f in storage.rglob('*') if f.is_file()), bytes=sum(f.stat().st_size for f in storage.rglob('*') if f.is_file()))
    shutil.rmtree(storage)
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'unhooked-worker')]) as w:
        s = ReplaySession.from_recording(w, source); check_worker(w, s, ext); s.seek(END); snap2 = w.request('snapshot')
    for name, value in (('routines.jsonl.gz', routines), ('writes.jsonl.gz', writes)):
        atomic_write(out / name, gzip.compress(('\n'.join(json.dumps(r) for r in value) + '\n').encode(), mtime=0))
    atomic_write(out / 'boundaries.json.gz', gzip.compress(json.dumps(boundaries).encode(), mtime=0)); save(out / 'hooked.json', snap); save(out / 'unhooked.json', snap2); atomic_write(out / 'end.ram', end_ram)
    return identity, removed


def load(read):
    def lines(name): return [json.loads(l) for l in gzip.decompress(read(name)).decode().splitlines() if l]
    return lines('routines.jsonl.gz'), lines('writes.jsonl.gz'), json.loads(gzip.decompress(read('boundaries.json.gz'))), json.loads(read('hooked.json')), json.loads(read('unhooked.json')), read('end.ram')


def validate(routines, writes, boundaries, end_ram):
    events = [e for r in routines for e in r['events']]; frames = {r['frame']: r['events'] for r in routines}
    require(all(a['frame'] < b['frame'] or a['sequence'] < b['sequence'] for a, b in zip(events, events[1:])), 'pair routine order differs')
    require(len(writes) == END and [w['frame'] for w in writes] == list(range(END)), 'pair write record extent differs')
    require(not any(e['pc'] in LOOP_PCS for e in events), 'ordinary allocator exhausted')
    early = [e for e in events if e['frame'] < SWITCH]
    f9e2 = split_invocations([e for e in events if e['pc'] in F9E2_PCS], 0xf9e2, F9E2_PCS)
    allocs = [validate_f9e2(r) for r in f9e2]
    runs = {name: validate_pickups(early, f9e2) if v.get('custom') else validate_pair(early, f9e2, name) for name, v in VARIANTS.items()}
    require(all(runs.values()), 'missing ordinary initializer invocation')
    pairs = sorted((p for r in runs.values() for p in r), key=lambda p: (p['frame'], p['entry_sp'], p['variant']))
    prefixes = validate_prefix(early, pairs); require(len(prefixes) == 1, 'ordinary setup prefix count differs')
    tails = [x | dict(kind='tail') for x in validate_tail(early, pairs)]; require(len(tails) == 1, 'ordinary setup tail count differs')
    messages = validate_message(early, writes); require(len(messages) == 1, 'ordinary setup message count differs')
    gated = validate_gated(early, writes); require(len(gated) == 1, 'ordinary gated pair step count differs')
    walks = pickup_walks(frames, boundaries); require(any(w['hit'] for w in walks), 'no ordinary 6C00 hit')
    probes = probe_walks(frames, boundaries, writes); require(any(h['delivered'] for h in probes[0]), 'no ordinary 7910 delivery')
    a5 = [e for e in events if e['pc'] in (0xf994, 0xf9a8, 0xf9ce)]
    for e, popped, done in zip(a5[0::3], a5[1::3], a5[2::3]):
        require((e['pc'], popped['pc'], done['pc']) == (0xf994, 0xf9a8, 0xf9ce), 'F994 cadence differs')
        require(done['registers']['M68K A6'] == e['registers']['M68K A6'] == popped['registers']['M68K A6'] and done['registers']['M68K A5'] == popped['registers']['M68K A5'], 'F994 does not preserve A6/return A5')
        slot(popped['registers']['M68K A5'])
    require(len(a5) % 3 == 0, 'unfinished F994')
    # Runs whose frame spans touch are audited together over every spanned frame.
    groups = []
    for p in sorted(pairs, key=lambda p: p['frame']):
        if groups and p['frame'] <= groups[-1][1]: groups[-1][1] = max(groups[-1][1], p['return_frame']); groups[-1][2].append(p)
        else: groups.append([p['frame'], p['return_frame'], [p]])
    audits = []
    for lo, hi, group in groups:
        records = writes[lo:hi + 1]
        inside = [x for x in prefixes + tails if all(any(run is p for p in group) for run in x['runs'])]
        audits.append(audit_frame_writes(records, group, inside) if all(r['dropped'] == 0 for r in records) else
                      dict(frames=list(range(lo, hi + 1)), writes=sum(r['count'] for r in records), dropped=sum(r['dropped'] for r in records), complete=False))
    retained = [runs[name][-1] for name in VARIANTS]
    phases, kept = continuity(frames, boundaries, retained, end_ram)
    kept['write_audit'] = audit_continuity_writes(writes, retained, kept['conversions'])
    callers = Counter(hex(a['caller']) for a in allocs)
    require(not any(lo <= a['caller'] < hi for a in allocs for lo, hi in GATED_CODE), 'a gated pair initializer allocated')
    require(not any(e['pc'] in {o for _e, _r, o in GATED_PCS} for e in events), 'a gated pair open path ran')
    observation = dict(f9e2_calls=len(allocs), f9e2_callers=dict(callers), f9e2_frame_crossings=sum(a['frame'] != a['return_frame'] for a in allocs),
                       f9e2_slots=[a['slot'] for a in allocs], f994_calls=len(a5) // 3,
                       fa30_calls=sum(e['pc'] == 0xfa30 for e in events), resets=sum(e['pc'] == 0xf940 for e in events),
                       pair_invocations={name: len(r) for name, r in runs.items()}, pair_frames={name: [p['frame'] for p in r] for name, r in runs.items()},
                       pair_write_audits=audits, continuity=kept,
                       setup_prefixes=[dict(frame=x['frame'], return_frame=x['return_frame'], free_depth=len(x['free_before']), slots=x['slots']) for x in prefixes],
                       setup_tails=[dict(frame=x['frame'], return_frame=x['return_frame'], free_depth=len(x['free_before']), slots=x['slots'],
                                         pickup_entries=x['runs'][0]['entries'], tables=x['runs'][0]['tables']) for x in tails],
                       setup_messages=messages, setup_gated_pairs=gated, pair_gates_at_end=[be(end_ram, 0x3172 + 2 * k) for k in range(4)],
                       pickup_hits=[dict(frame=w['frame'], slot=w['slot'], phase_before=w['phase_before'], phase_after=w['phase_after'], sounds=w['sounds']) for w in walks if w['hit']],
                       pickup_releases=[dict(frame=w['frame'], slot=w['slot']) for w in walks if w['released']],
                       pickup_walks=dict(walks=len(walks), phases=dict(Counter(f"{w['phase_before']}->{w['phase_after']}" for w in walks)),
                                         last_frame={str(s): max(w['frame'] for w in walks if w['slot'] == s) for s in sorted({w['slot'] for w in walks})}),
                       probe_hits=[{k: h[k] for k in ('frame', 'slot', 'delivered', 'gated', 'sounds', 'created')} for h in probes[0]],
                       delivered_walks=dict(walks=len(probes[1]), by_slot={str(s): dict(kind=('sparkle', 'copy', 'table')[next(w['kind'] for w in probes[1] if w['slot'] == s)],
                                            first=min(w['frame'] for w in probes[1] if w['slot'] == s), last=max(w['frame'] for w in probes[1] if w['slot'] == s),
                                            released=[w['frame'] for w in probes[1] if w['slot'] == s and w['released']], callback=[w['frame'] for w in probes[1] if w['slot'] == s and w['callback']],
                                            released_in_callback=[w['frame'] for w in probes[1] if w['slot'] == s and w['released_in_callback']])
                                            for s in sorted({w['slot'] for w in probes[1]})}),
                       delivered_links=probes[2], first_ingredients=probes[3])
    return pairs, retained, phases, observation, prefixes, tails, messages, gated, walks, probes


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('recording', type=Path); p.add_argument('--preset', choices=PRESETS, default='debug'); p.add_argument('--fixture', type=Path); args = p.parse_args(argv)
    ext = ROOT.parent / 'BizHawkOpenSource/Tools/GenesisDebug'; sys.path.insert(0, str(ext / 'python'))
    from genesis_debug.replay import load_recording
    source = load_recording(args.recording); rom = inspect_file(); verify_expected(rom)
    natives = {name: verify_executable(args.preset, v['native']) for name, v in VARIANTS.items()}; native = natives['return_only']
    require(source['rom']['sha256'] == rom['sha256'] and source['input_sha256'] == INPUT_SHA256 and len(source['inputs']) == 5298 and not source['experimental_edits'] and not source['instrumentation'], 'pair recording differs')
    require(source['start']['imported_movie']['source']['sha256'] == MOVIE_SHA256, 'pair movie identity differs')
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/pair-initializer-capture')))
    report = dict(ok=False, preset=args.preset, end=END, switch=SWITCH, recipes=dict(early=recipe(False), walk=recipe(True)), sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in SOURCES},
        movie_sha256=MOVIE_SHA256, input_sha256=INPUT_SHA256, recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(), native_build=json.loads((native.parent / 'provenance.json').read_text()),
        classification='fresh native comparison of captured ordinary movie' if args.fixture else 'fresh ordinary unchanged movie frames 0..1066; no edits; owned workers',
        scope='Every ordinary F9E2 call, every 6EC8, 6EDC, 7772, 783A, 7B9C, 7C26, 6A94 and 6EB6 run, the [6886,68A4) setup prefix and the [68A4,68BC) tail, the [68BC,68C4) message step and the [68C4,68D4) gated-pair step in [0,1066); the latest run of each is followed through every frame to 1066, except a dormant object overwritten by unsupported 7AD6, which is followed to that copy. Native also builds the whole prefix and the tail from their entry stacks; tail pickups stop at their first unsupported 6C00 hit, which native must reject. Native initializes from each run-entry stack, verified inherited fields and (7772/783A) the caller control, then advances only that group; 7808/7CA4 objects consume each walk\'s observed gate words and the 783A probe each walk\'s observed 78EE inputs. Native stops at, and must reject, the probe\'s first unsupported 7910 hit; later walks are original-only continuity. The ordinary gated-pair step has every gate closed; its open paths are compared only by restricted cases. Every 6C00 hit and every later walk of a hit pickup (to its release or END) is compared natively one walk at a time from the original entry state, and consecutive walks must chain; untouched links are context only. Every 7910 hit walk is compared natively (--probe-hit) from the original entry state with the real free stack, and every later walk of a delivery\'s sparkle and copy (to the FAA4 release, the copy\'s 79B6 callback or END) one walk at a time (--delivered), chained; the copy\'s walk into 79B6\'s first-ingredient path and 7AD6 (--ingredient), then every later walk of the FF31B4 table object it makes (wiznliz-table-motion --scheduled); a delivered link must stay unchanged until its next 6C00 use. The retained world (--world-pool) builds the whole [6886,68D4) setup from its entry stack and runs every later object loop to 1066 in that one pool with one carried PickupWorld, private globals and E918 state; its only per-loop inputs are 78EE tracking, the emitter owner\'s position, the count of E918 calls by non-pool code and message-field updates by the non-native message producer. Every walk event, the free stack, records, identities, messages, globals, E918 state, sound requests and row clears are compared after each loop, and pool bytes may change only inside walks. No level-setup caller, second-ingredient path, 7B42, gate producer, P1 actor or whole-machine parity.')
    try:
        if args.fixture:
            parent = json.loads(args.fixture.read_text())
            require(parent['recipes'] == report['recipes'] and parent['sources'] == report['sources'] and parent['recording_sha256'] == report['recording_sha256'], 'pair fixture validation/input contract changed')
            read = fixture_reader(parent, args.fixture.parent); report['identity'] = parent['identity']
            report['reference_report'] = str(args.fixture); report['reference_report_sha256'] = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
        else:
            report['identity'], report['worker_checkpoints_removed'] = capture(source, out, ext)
            read = lambda name: (out / name).read_bytes()
        routines, writes, boundaries, snap, snap2, end_ram = load(read)
        require(report['identity'] == source['start']['worker_open']['identity'], 'pair identity differs')
        require(all(s['identity'] == report['identity'] and s['frame'] == END and not s['experimentalEdits'] for s in (snap, snap2)), 'pair endpoint provenance differs')
        require(snap['canonicalSha256'] == snap2['canonicalSha256'] and snap['hashScope'] == snap2['hashScope'], 'pair hooked/unhooked endpoint differs')
        report['endpoint'] = dict(hooked=snap['canonicalSha256'], unhooked=snap2['canonicalSha256'], scope=snap['hashScope'])
        pairs, retained, phases, report['observation'], prefixes, tails, messages, gated, walks, probes = validate(routines, writes, boundaries, end_ram)
        report['pairs'] = pairs
        report['comparison'] = [dict(variant=p['variant'], frame=p['frame']) | compare_native(natives[p['variant']], p, phases if any(p is r for r in retained) else [])
                                for p in pairs if not VARIANTS[p['variant']].get('composed')]
        report['comparison'] += [dict(variant='setup_prefix', frame=x['frame']) | compare_prefix(natives['dormant_b4'], x) for x in prefixes]
        report['comparison'] += [dict(variant='setup_tail', frame=x['frame']) | compare_tail(natives['pickups'], x, phases if all(any(r is q for q in retained) for r in x['runs']) else [])
                                 for x in tails]
        report['comparison'] += [dict(variant='setup_message', frame=x['frame']) | compare_message(natives['pickups'], x) for x in messages]
        report['comparison'] += [dict(variant='setup_gated_pairs', frame=x['frame']) | compare_gated(natives['pickups'], x) for x in gated]
        report['comparison'] += [dict(variant='pickup_walks', frame=walks[0]['frame']) | compare_pickup_walks(natives['quad'], walks)]
        report['comparison'] += [dict(variant='probe_walks', frame=probes[0][0]['frame']) | compare_probe_walks(natives['quad'], verify_executable(args.preset, 'wiznliz-table-motion'), probes[0], probes[1])]
        from genesis_world_pool import compare_world
        report['comparison'] += [dict(variant='world_pool', frame=prefixes[0]['frame']) | compare_world(natives['quad'], {r['frame']: r['events'] for r in routines}, boundaries, writes,
                                                                                                         prefixes[0], tails[0], messages[0], gated[0])]
        report['ok'] = True
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True
        report['artifacts'] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'observation', 'comparison', 'error')} | {'report': str(out / 'report.json')}, indent=2, default=str))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
