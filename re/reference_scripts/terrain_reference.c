/* Project-owned research transport for pinned Musashi. No emulator code in
 * native libraries. ROM/code, map and records are read-only during execution. */
#include "m68k.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned char rom[1048576], ram[65536];
static unsigned base, record_size, instructions, total_instructions;
static unsigned tile, visits[1048576];
static int running, movement, airborne, controller, scheduling, immediate_continuation, reversal, effect_mode, empty_pool, actions, dispatch, transition, transition_timer, coast_entry, tally, palette, bonus, exit_tally, score;
static int pad_conversion, level_banner, trail_mode, private_mode, table_mode, collision_mode;
static unsigned collision_secondary, collision_queries;
static int return_only_mode;
static int hit_mode;
static int boundary_stop_seen; // The last call() ended at a declared boundary rather than its RTS.
static unsigned hit_stop, hit_exhausted, delivery_created[8], delivery_kinds[8], delivery_count, completion_pops, completion_effect, hub_entries, hub_touched;
static int recipe_stop(unsigned pc);
static int pair_mode;
static unsigned pair_pops, pair_exhausted, tail_pickups, pairs_current;
static unsigned message_vdp[40][2], message_vdp_count, message_lock_ok, message_selected;
static unsigned return_only_presentations, return_only_returns;
static unsigned table_budget, table_work;
static unsigned banner_request[5], banner_texts, banner_numbers, banner_device_writes;
static unsigned score_advances, score_work;
static unsigned bonus_probes, bonus_count, bonus_slots[80], bonus_values[80], bonus_calls;
static unsigned palette_calls;
static unsigned horizontal_steps, airborne_transitions, settle_calls, landings;

static unsigned sample_requests[1024][3], sample_count;
static unsigned sound_requests[1024][4], sound_count, spawned[128], spawn_count, releases;
static void fail(const char *message) { fprintf(stderr, "%s\n", message); exit(2); }
static int code(unsigned a) {
    // 6BD6/6C00 pickup walks: presentation and its callbacks, the service, the
    // hit (6E32/6E5E/6E8A family branches stop), 59BC/5964/FB06, the FCB32
    // selector-mismatch return, 6B44/6BB2 re-dress and the FAA4 release.
    // 78EE/7910 probe walks: presentation, the service, AC5E, the hit (its 7A56
    // RTS), the FCB32 mismatch return, 59AE/59BC, 5964, both allocators (FA1E
    // and F9D0, their exhaustion loops, stop) and FB06.
    if (hit_mode==2) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x78ee && a<0x79b6)
        || (a>=0x7a56 && a<0x7a58) || (a>=0xac5e && a<0xac9c) || (a>=0xfcb32 && a<0xfcb42) || (a>=0xfcb7a && a<0xfcb7e) || (a>=0x59ae && a<0x5a06)
        || (a>=0x5964 && a<0x59ae) || (a>=0xf9e2 && a<0xfa1e) || (a>=0xf994 && a<0xf9d0) || (a>=0xfb06 && a<0xfb1a);
    // Later walks of a 7910 object: presentation, the RTS selectors and the FAA4
    // release; the copy's 79B6 callback stops.
    if (hit_mode==3) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0xfaa4 && a<0xfabc);
    // A copy's walk through callback79B6's first-ingredient path: 6BB2, CB72/CB9A,
    // 7AD6's FF31AC-zero path, FB06, FAA4 and then 7A88 on the released copy;
    // the second-ingredient branch (7A00) stops.
    // A copy's walk through callback79B6's second-ingredient path: CB72/CB9A,
    // 7AD6's FF31AC-nonzero path (FF31B8, FF31B0 and the FF31C0 anchor), FB06,
    // FAA4 and then 7A88 on the released copy; the first path is out of scope.
    if (hit_mode==5) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x79b6 && a<0x7a26)
        || (a>=0x6bb2 && a<0x6bd6) || (a>=0xcb72 && a<0xcc18) || (a>=0x7ad6 && a<0x7b22) || (a>=0xfb06 && a<0xfb1a) || (a>=0xfaa4 && a<0xfabc) || (a>=0x7a88 && a<0x7ad6);
    // Walks of the FF31C0 anchor: 7B42's countdown with 13294, the 7B4E store,
    // 7B58's wait and 7B8A; 7B58's completion (7B60) stops.
    if (hit_mode==6) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x7b42 && a<0x7b60)
        || (a>=0x7b8a && a<0x7b9c) || (a>=0x13294 && a<0x132d2);
    // The anchor's 7B58 walk with FF0B90 zero: CB72/CB9A, 7E18/7ED6 (the FF31A8
    // path at 7EF4 stops), the 83DA lookup, the FCB32 mismatch return, recipe
    // 8652 with 7F08 and 6F02 (6F44 stops), F9E2 (FA1E stops), 95EE (9614 and
    // 9682 stop) and 1324E; 9288, 9182 and the other recipe effects stop.
    if (hit_mode==7) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x7b56 && a<0x7b8a)
        || (a>=0xcb72 && a<0xcc18) || (a>=0x7e18 && a<0x7ef4) || (a>=0x7f08 && a<0x7f6a) || (a>=0x8652 && a<0x867e) || (a>=0x6f02 && a<0x6f44)
        || (a>=0x6f7a && a<0x6fb6) || (a>=0x95ee && a<0x9614) || (a>=0xf9e2 && a<0xfa1e) || (a>=0xfcb32 && a<0xfcb42) || (a>=0xfcb7a && a<0xfcb7e)
        || (a>=0x1324e && a<0x13294);
    // Walks of 7F08's sparkle: 7F6A, E918, 5A9A with F994 (F9D0 stops) and FAA4.
    if (hit_mode==8) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x7f6a && a<0x7fbe)
        || (a>=0xe918 && a<0xe948) || (a>=0x5a9a && a<0x5ae4) || (a>=0xf994 && a<0xf9d0) || (a>=0xfaa4 && a<0xfabc);
    // Walks of 6F02's door and sign: 6FB6, 5964, the 6FCA callback with 4C08,
    // 4C34, the FCB32 mismatch return, 705C's AC5E and its contact path 7082
    // (4CA2 with FAA4 and 59BC, the camera words, P1's actor and +1A6); the
    // two-player test (7072) and an active +1A2 link (70FE) stop.
    if (hit_mode==9) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x6fb4 && a<0x705c)
        || (a>=0x5964 && a<0x59ae) || (a>=0x4c08 && a<0x4c52) || (a>=0x705c && a<0x7072) || (a>=0x7080 && a<0x70fe) || (a>=0x7152 && a<0x7154)
        || (a>=0x4ca2 && a<0x4cbe) || (a>=0x59bc && a<0x5a06) || (a>=0xfaa4 && a<0xfabc) || (a>=0xac5e && a<0xac9c) || (a>=0xfcb32 && a<0xfcb42) || (a>=0xfcb7a && a<0xfcb7e);
    // The scene between levels: the setup's [5E86,5E8E) (63A4, then 60E6's
    // records through 611E with F9E2 and 6334's F994 pair; FA1E and F9D0 stop).
    if (hit_mode==10) return (a>=0x5e86 && a<0x5e8e) || (a>=0x63a4 && a<0x63e2) || (a>=0x60e6 && a<0x61f6) || (a>=0x6334 && a<0x639a)
        || (a>=0xf9e2 && a<0xfa1e) || (a>=0xf994 && a<0xf9d0);
    // Walks of a hub door: the loop's walk body, F76C, 61F6, 621A with AC5E,
    // 623C (17298, FA8C, 630A, 13208), FAC4/FAE2 and the FAA4 release.
    if (hit_mode==11) return (a>=0x5f5e && a<0x5f76) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x61f6 && a<0x630a)
        || (a>=0xac5e && a<0xac9c) || (a>=0x17298 && a<0x172be) || (a>=0xfa8c && a<0xfaa4) || (a>=0x630a && a<0x632a) || (a>=0x13208 && a<0x1324e)
        || (a>=0xfac4 && a<0xfae4) || (a>=0xfaa4 && a<0xfabc);
    // 6024's exit test; its BRA to 5EEA stops.
    if (hit_mode==12) return a>=0x6024 && a<0x6040;
    // The scene change into the hub, in order: 0x488's copy, 17024, F850 (F872,
    // F940, 1720C), [16FF8,17004) with 131C2, 9880 (98DE, 9952, 1737E, 5964),
    // 17284 (17298), [5D6A,5D7E) with 446C and [5ED4,5EDC).
    if (hit_mode==13) return (a>=0x488 && a<0x49e) || (a>=0x17024 && a<0x17058) || (a>=0xf850 && a<0xf8f2) || (a>=0xf940 && a<0xf994) || (a>=0x1720c && a<0x17256)
        || (a>=0x16fb4 && a<0x16fba) || (a>=0x16ff8 && a<0x17004) || (a>=0x131c2 && a<0x13208) || (a>=0x9880 && a<0x99d4) || (a>=0x1737e && a<0x173c6) || (a>=0x5964 && a<0x59ae)
        || (a>=0x17284 && a<0x172be) || (a>=0x5d6a && a<0x5d7e) || (a>=0x446c && a<0x4484) || (a>=0x5ed4 && a<0x5edc);
    // The second level's entry, in order: 16EA4's 17024, F850 (F872, F940,
    // 1720C), [16FB4,16FBA) and [16FF8,17004) with 131C2; E2A's [E44,E52), 9880
    // (98DE, 9952, 1737E, 5964); 118C's [11A6,11EE) with E918 and [1356,1364)
    // with 9952; [774,77C).
    if (hit_mode==14) return (a>=0x17024 && a<0x17058) || (a>=0xf850 && a<0xf8f2) || (a>=0xf940 && a<0xf994) || (a>=0x1720c && a<0x17256)
        || (a>=0x16fb4 && a<0x16fba) || (a>=0x16ff8 && a<0x17004) || (a>=0x131c2 && a<0x13208) || (a>=0x9880 && a<0x99d4) || (a>=0x1737e && a<0x173c6) || (a>=0x5964 && a<0x59ae)
        || (a>=0xe44 && a<0xe52) || (a>=0x11a6 && a<0x11ee) || (a>=0xe918 && a<0xe948) || (a>=0x1356 && a<0x1364) || (a>=0x774 && a<0x77c);
    // The hint screen's loop test: 14E3C, then [1972E,19764) with 13208, or
    // [1975A,19764) once ending.
    if (hit_mode==15) return (a>=0x14e3c && a<0x14e4e) || (a>=0x1972e && a<0x19766) || (a>=0x13208 && a<0x1324e);
    if (hit_mode==4) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x79b6 && a<0x7a00)
        || (a>=0x7a26 && a<0x7a58) || (a>=0x6bb2 && a<0x6bd6) || (a>=0xcb72 && a<0xcc18) || (a>=0x7ad6 && a<0x7ae6) || (a>=0x7b22 && a<0x7b42)
        || (a>=0xfb06 && a<0xfb1a) || (a>=0xfaa4 && a<0xfabc) || (a>=0x7a88 && a<0x7ad6);
    if (hit_mode) return (a>=0x69aa && a<0x69c2) || (a>=0xf76c && a<0xf850) || (a>=0x12646 && a<0x12648) || (a>=0x6b44 && a<0x6d8c)
        || (a>=0xac5e && a<0xac9c) || (a>=0x59bc && a<0x5a06) || (a>=0x5964 && a<0x59ae) || (a>=0xfb06 && a<0xfb1a)
        || (a>=0xfcb32 && a<0xfcb42) || (a>=0xfcb7a && a<0xfcb7e) || (a>=0xfaa4 && a<0xfabc);
    // FA1E onward is the VDP exhaustion loop: reached as a stop boundary only.
    if (pair_mode==8) return (a>=0x68c4 && a<0x68d4) || (a>=0x7fbe && a<0x8040) || (a>=0x7154 && a<0x71ce) || (a>=0x735e && a<0x73d8) || (a>=0x7568 && a<0x75e2) || (a>=0xf9e2 && a<0xfa1e);
    if (pair_mode==7) return (a>=0x68bc && a<0x68c4) || (a>=0x7db8 && a<0x7e18) || (a>=0xcb72 && a<0xcc18) || (a>=0x6ef0 && a<0x6f02);
    if (pair_mode==6) return (a>=0x68a4 && a<0x68bc) || (a>=0x6a94 && a<0x6bd6) || (a>=0x6eb6 && a<0x6ec8) || (a>=0xf9e2 && a<0xfa1e);
    if (pair_mode==5) return (a>=0x6886 && a<0x68a4) || (a>=0x6ec8 && a<0x6ef0) || (a>=0x7772 && a<0x7808) || (a>=0x783a && a<0x78ee) || (a>=0x7b9c && a<0x7ca4) || (a>=0xf9e2 && a<0xfa1e);
    if (pair_mode) return (pair_mode==1 ? a>=0x7b9c && a<0x7c26 : pair_mode==2 ? a>=0x7c26 && a<0x7ca4 : pair_mode==3 ? a>=0x7772 && a<0x7808 : a>=0x783a && a<0x78ee) || (a>=0xf9e2 && a<0xfa1e);
    if (return_only_mode) return (a>=0xf76c && a<0xf850) || (a>=0x69aa && a<0x69c2) || (a>=0x12646 && a<0x12648);
    if (collision_mode) return (a>=0xac5e && a<0xac9c) || (collision_mode>=4 ? a>=0x6bd6 && a<0x6c00 : a>=0x78ee && a<0x7910)
        || (a>=0xf76c && a<0xf850) || (a>=0x69aa && a<0x69c2) || (a>=0x12646 && a<0x12648);
    if (table_mode==4) return a>=0x7cc8 && a<0x7db8; // The whole 7CC8 producer and exchange.
    if (table_mode==3) return (a>=0x7a46 && a<0x7a58) || (a>=0x7cc8 && a<0x7cea);
    if (table_mode) return (a>=0x7a88 && a<0x7ad6) || (a>=0xf76c && a<0xf850)
        || (a>=0x69aa && a<0x69c2) || (a>=0x12646 && a<0x12648);
    if (private_mode) return (a>=0x7808 && a<0x783a) || (a>=0x7ca4 && a<0x7cc8)
        || (a>=0xf76c && a<0xf850) || (a>=0x69aa && a<0x69c2) || (a>=0x12646 && a<0x12648);
    if (trail_mode) return (a>=0x6d8c && a<0x6e32) || (a>=0x5a9a && a<0x5ae4)
        || (a>=0xe918 && a<0xe948) || (a>=0xf994 && a<0xf9d0)
        || (a>=0xf76c && a<0xf850) || (a>=0xfaa4 && a<0xfabc)
        || (a>=0x12646 && a<0x12648) || (a>=0x69aa && a<0x69c2);
    if (level_banner) return (a>=0x63e2 && a<0x644c) || (a>=0x17532 && a<0x17558) || (a>=0x17568 && a<0x175e8);
    if (pad_conversion) return a>=0x14e4e && a<0x14f24;
    return (score && ((a>=0x53f2 && a<0x5458) || (a>=0xadf4 && a<0xae72) || (a>=0xaf28 && a<0xaf5c)))
        || (exit_tally && a>=0x5132 && a<0x51c8)
        || (bonus && ((a>=0x5266 && a<0x52a6) || (a>=0x451a && a<0x4526) || (a>=0x4770 && a<0x47ba)))
        || (palette && ((a>=0x51d0 && a<0x5222) || (a>=0x1324e && a<0x13294)
        || (a>=0x137ce && a<0x137f6) || (a>=0x1372c && a<0x13754)))
        || (tally && ((a >= 0x51c8 && a < 0x51d0) || (a >= 0x5222 && a < 0x5266)
        || (a >= 0x52a6 && a < 0x52b0) || (a >= 0x537c && a < 0x53de)
        || (a >= 0xaf98 && a < 0xafb0) || (a >= 0x4f8c && a < 0x4f8e)))
        || (transition && ((a >= 0x630a && a < 0x6334) || (a >= 0x710e && a < 0x7154) || (a >= 0xa148 && a < 0xa196)
        || (a >= 0x13208 && a < 0x1324e) || (a >= 0x1345a && a < 0x134d6)))
        || (dispatch && a >= 0xf906 && a < 0xf938)
        || (controller && a >= 0x12646 && a < 0x12648)
        || (actions && ((a >= 0x9c56 && a < 0x9d28) || (a >= 0x9d44 && a < 0x9dce)
        || (a >= 0xa196 && a < 0xa1a4) || (a >= 0xf938 && a < 0xf940)
        || (a >= 0xed6e6 && a < 0xed6f6) || (a >= 0xed6fc && a < 0xed716)))
        || (effect_mode && ((a >= 0x80a && a < 0x81c) || (a >= 0x69aa && a < 0x69bc)))
        || (reversal && ((a >= 0xa7a8 && a < 0xa88e) || (a >= 0xa96e && a < 0xaa50)
        || (a >= 0xf994 && a < 0xf9d0) || (a >= 0xfaa4 && a < 0xfabc)))
        || (scheduling && ((a >= 0xf76c && a < 0xf850) || (a >= 0xf8f6 && a < 0xf90c)
        || (a >= 0xa2e8 && a < 0xa2ec) || (a >= 0xa380 && a < 0xa384)
        || (a >= 0xa50e && a < 0xa512) || (a >= 0xa654 && a < 0xa658)
        || (a >= 0xa774 && a < 0xa7a8) || (a >= 0xa93a && a < 0xa96e)))
        || (controller && ((a >= 0xa1be && a < 0xa22c) || (a >= 0xa246 && a < 0xa2e8)
        || (a >= 0xa2ec && a < 0xa380) || (a >= 0xa384 && a < 0xa452)
        || (a >= 0xa460 && a < 0xa50e) || (a >= 0xa512 && a < 0xa590)
        || (a >= 0xa59e && a < 0xa654) || (a >= 0xa6c8 && a < 0xa72a)
        || (a >= 0xa738 && a < 0xa774) || (a >= 0xa88e && a < 0xa8f0)
        || (a >= 0xa8fe && a < 0xa93a) || (a >= 0xaa88 && a < 0xaaea)
        || (a >= 0xfcb32 && a < 0xfcb42) || (a >= 0xfcb7a && a < 0xfcb7e)))
        || (a >= 0x99d4 && a < 0x9a5e) || (a >= 0x9a80 && a < 0x9aae)
        || (a >= 0x9b34 && a < 0x9bac)
        || (movement && ((a >= 0x9a5e && a < 0x9a80) || (a >= 0x9aae && a < 0x9b34)
            || (a >= 0xaa50 && a < 0xaa88) || (a >= 0xacd6 && a < 0xacfa)))
        || (airborne && ((a >= 0x9bac && a < 0x9c56) || (a >= 0xaaea && a < 0xac5e)
            || (a >= 0xa658 && a < 0xa6c8) || (a >= 0xa1a4 && a < 0xa1be)
            || (a >= 0xa22c && a < 0xa246)));
}
static int readable(unsigned a) {
    if (hit_mode==2) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff0832 && a<0xff0836) || (a>=0xff09da && a<0xff09de) || (a>=0xff06d2 && a<0xff06d6)
        || (a>=0xff087a && a<0xff087e) || (a>=0xff13ae && a<0xff13b0) || (a>=0xff33e2 && a<0xff33e4) || (a>=0xff31b0 && a<0xff31b4)
        || (a>=0xff0a9e && a<0xff0aa6) || (a>=0xff0ab6 && a<0xff0ab8) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==3) return (a>=0xff1b50 && a<0xff3120) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==5) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff447a && a<0xff453a) || (a>=0xff31ac && a<0xff31c4) || (a>=0xff06d6 && a<0xff06e8)
        || (a>=0xff087e && a<0xff0890) || (a>=0xff0d60 && a<0xff0d64) || (a>=0xff010c && a<0xff010e) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==6) return (a>=0xff1b50 && a<0xff3008) || (a>=0xff0b90 && a<0xff0b92) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==7) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff447a && a<0xff453a) || (a>=0xff316c && a<0xff316e) || (a>=0xff31a4 && a<0xff31b4)
        || (a>=0xff33e2 && a<0xff33e4) || (a>=0xff06cc && a<0xff06d0) || (a>=0xff06d6 && a<0xff06e8) || (a>=0xff087e && a<0xff0890) || (a>=0xff0d60 && a<0xff0d64)
        || (a>=0xff010c && a<0xff010e) || (a>=0xff0b90 && a<0xff0b92) || (a>=0xff0a9e && a<0xff0aa6) || (a>=0xff0ab6 && a<0xff0ab8) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==8) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff0bac && a<0xff0bb4) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==9) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff0690 && a<0xff0694) || (a>=0xff06ca && a<0xff06cc) || (a>=0xff06d2 && a<0xff06d6)
        || (a>=0xff0832 && a<0xff0836) || (a>=0xff31c0 && a<0xff31c4) || (a>=0xff444a && a<0xff444e) || (a>=0xff13ae && a<0xff13b0)
        || (a>=0xff33e2 && a<0xff33e4) || (a>=0xff0a9e && a<0xff0aa6) || (a>=0xff0ab6 && a<0xff0ab8) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==4) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff447a && a<0xff453a) || (a>=0xff31ac && a<0xff31c0) || (a>=0xff06d6 && a<0xff06e8)
        || (a>=0xff087e && a<0xff0890) || (a>=0xff0d60 && a<0xff0d64) || (a>=0xff010c && a<0xff010e) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==10) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff330c && a<0xff338a) || (a>=0xff33e2 && a<0xff33e4) || (a>=0xff33c4 && a<0xff33c6) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==11) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff0690 && a<0xff0694) || (a>=0xff06d2 && a<0xff06d6) || (a>=0xff0836 && a<0xff083c)
        || (a>=0xff087a && a<0xff087e) || (a>=0xff09de && a<0xff09e0) || (a>=0xff13ae && a<0xff13b0) || (a>=0xff33e2 && a<0xff33e4) || (a>=0xff1ab4 && a<0xff1b50)
        || (a>=0xff4446 && a<0xff444a) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==12) return (a>=0xff0836 && a<0xff0838) || (a>=0xff0b90 && a<0xff0b92) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==13) return (a>=0xff0690 && a<0xff09e0) || (a>=0xff1ab4 && a<0xff3120) || (a>=0xff4446 && a<0xff444a) || (a>=0xff13e0 && a<0xff13e2)
        || (a>=0xff33e2 && a<0xff33e4) || (a>=0xff140a && a<0xff140c) || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || (a>=0xff0f16 && a<0xff0f18) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==14) return (a>=0xff0690 && a<0xff09e0) || (a>=0xff1ab4 && a<0xff3120) || (a>=0xff13e0 && a<0xff13e2) || (a>=0xff33e2 && a<0xff33e4) || (a>=0xff3402 && a<0xff3404)
        || (a>=0xff0bac && a<0xff0bb4) || (a>=0xff140a && a<0xff140c) || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || (a>=0xff0f16 && a<0xff0f18) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode==15) return (a>=0xff06a4 && a<0xff06b2) || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || (a>=0xff0f0e && a<0xff0f12) || (a>=0xffef00 && a<0xfff004);
    if (hit_mode) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff312c && a<0xff316c) || (a>=0xff447a && a<0xff453a) || (a>=0xff0832 && a<0xff0836)
        || (a>=0xff09da && a<0xff09de) || (a>=0xff06d2 && a<0xff06d6) || (a>=0xff087a && a<0xff087e) || (a>=0xff13ae && a<0xff13b0)
        || (a>=0xff33e2 && a<0xff33e4) || (a>=0xff0a9e && a<0xff0aa6) || (a>=0xff0ab6 && a<0xff0ab8) || (a>=0xffef00 && a<0xfff004);
    if (pair_mode==8) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff3172 && a<0xff317a) || (a>=0xff0874 && a<0xff0878) || (a>=0xffef00 && a<0xfff004);
    if (pair_mode==7) return (a>=0xff312c && a<0xff314c) || (a>=0xff316c && a<0xff316e) || (a>=0xff31aa && a<0xff31ac) || (a>=0xff33e2 && a<0xff33e4)
        || (a>=0xff0d60 && a<0xff0d64) || (a>=0xff010c && a<0xff010e) || (a>=0xff06d6 && a<0xff06e8) || (a>=0xffef00 && a<0xfff004);
    if (pair_mode==6) return (a>=0xff1b50 && a<0xff3120) || (a>=0xff312c && a<0xff316c) || (a>=0xff4c80 && a<0xff4cc0) || (a>=0xff447a && a<0xff453a)
        || (a>=0xff31ac && a<0xff31b4) || (a>=0xff0832 && a<0xff0836) || (a>=0xff09da && a<0xff09de) || (a>=0xffef00 && a<0xfff004);
    if (pair_mode) return (a>=0xff1b50 && a<0xff3120) || (pair_mode==5 && a>=0xff31b4 && a<0xff31bc) || (a>=0xff31c0 && a<0xff31c4) || (a>=0xffef00 && a<0xfff004);
    if (return_only_mode) return (a>=0xff1ab4 && a<0xff1b02) || (a>=0xffef00 && a<0xfff004);
    if (collision_mode) return (a>=0xff1ab4 && a<0xff1b02) || (a>=0xff06d2 && a<0xff06d6)
        || (a>=0xff087a && a<0xff087e) || (a>=0xff13ae && a<0xff13b0)
        || (a>=0xff33e2 && a<0xff33e4) || (a>=0xffef00 && a<0xfff004);
    if (table_mode==4) return (a>=0xff31ac && a<0xff31b4) || (a>=0xff31bc && a<0xff31c0) || (a>=0xff1b50 && a<0xff3008) || (a>=0xffef00 && a<0xfff004);
    if (table_mode==3) return (a>=0xff31b0 && a<0xff31b4) || (a>=0xff31bc && a<0xff31c0) || (a>=0xffef00 && a<0xfff004);
    if (table_mode) return (a>=0xff1ab4 && a<0xff1b02) || (a>=0xff31bc && a<0xff31be) || (a>=0xffef00 && a<0xfff004);
    if (private_mode) return (a>=0xff1ab4 && a<0xff1b02) || (a>=0xff31a4 && a<0xff31a8)
        || (a>=0xff31b0 && a<0xff31b4) || (a>=0xffef00 && a<0xfff004);
    if (trail_mode) return (a>=0xff1ab4 && a<0xff1b02) || (a>=0xff2000 && a<0xff24e0)
        || (a>=0xff2800 && a<0xff2806) || (a>=0xff0690 && a<0xff0694)
        || (a>=0xff0bac && a<0xff0bb4) || (a>=0xff3008 && a<0xff3050)
        || (a>=0xff311c && a<0xff3120) || (a>=0xffef00 && a<0xfff004);
    if (level_banner) return (a>=0xff010c && a<0xff010e) || (a>=0xff13e2 && a<0xff13e4)
        || (a>=0xff1452 && a<0xff1454) || (a>=0xff33c4 && a<0xff33c6)
        || (a>=0xff4442 && a<0xff4446) || (a>=0xffef00 && a<0xfff004);
    if (pad_conversion) return (a>=0xff0690 && a<0xff06c0) || (a>=0xffef00 && a<0xfff004);
    if (score && ((a>=0xff06fe && a<0xff0708) || (a>=0xff443e && a<0xff4442))) return 1;
    if (exit_tally && ((a>=0xff070c && a<0xff0710) || (a>=0xff0efe && a<0xff0f00) || (a>=0xff33c8 && a<0xff33ce))) return 1;
    if (bonus && a>=0xff0802 && a<0xff0832) return 1;
    if (palette && ((a>=0xff0ea8 && a<0xff0ec8) || (a>=0xff0dc8 && a<0xff0df8))) return 1;
    if (tally && ((a>=0xff0714 && a<0xff0716) || (a>=0xff0f0e && a<0xff0f10)
        || (a>=0xff340a && a<0xff340c) || (a>=0xff3402 && a<0xff3404)
        || (a>=0xff0104 && a<0xff0106) || (a>=0xff33ce && a<0xff33d0))) return 1;
    return (transition && ((a >= 0xff0b90 && a < 0xff0ba4) || (a >= 0xff0edc && a < 0xff0ee0)
        || (a >= 0xff0732 && a < 0xff0736)))
        || (dispatch && a >= 0xff0836 && a < 0xff0838)
        || (actions && ((a >= 0xff33d8 && a < 0xff33dc) || (a >= 0xff33e0 && a < 0xff33e2)
        || (a >= 0xff0ad6 && a < 0xff0ade)))
        || (reversal && ((a >= 0xff2000 && a < 0xff24e0) || (a >= 0xff3008 && a < 0xff3050)
        || (a >= 0xff311c && a < 0xff3120)))
        || (controller && ((a >= 0xff0a9e && a < 0xff0aa6) || (a >= 0xff0ab6 && a < 0xff0ab8)))
        || (a >= 0xff4d02 && a < 0xff6d02)
        || (a >= 0xff8000 && a < 0xff8000 + record_size)
        || (a >= 0xff4442 && a < 0xff4456)
        || (a >= 0xff13a4 && a < 0xff13b0)
        || (a >= 0xff140e && a < 0xff1410)
        || (a >= 0xff0690 && a < 0xff06a0)
        || (movement && ((a >= 0xff0690 && a < 0xff0700) || (a >= 0xff1ab4 && a < 0xff1b02)))
        || (airborne && a >= 0xff0f16 && a < 0xff0f18)
        || (a >= 0xffef00 && a < 0xfff004);
}
unsigned m68k_read_memory_8(unsigned a) {
    a &= 0xffffff;
    if (a < 8 || code(a)) return rom[a];
    if (table_mode && a>=0x7a58 && a<0x7a88) return rom[a];
    if (level_banner && ((a>=0x644c && a<0x6554) || (a>=0xba2a && a<0xbb2a))) return rom[a];
    if (pair_mode==7 && ((a>=0xd28c && a<0xd2a2) || (a>=0xd2a2 && a<0xd2b7))) return rom[a]; // CB72 reads the two message strings.
    if (hit_mode==4 && ((a>=0x7a58 && a<0x7a88) || a==0xd20e || a==0xd22f)) return rom[a]; // The 7A88 table; CB72 reads a message's priority byte.
    if (hit_mode==5 && ((a>=0x7a58 && a<0x7a88) || a==0xd22f)) return rom[a]; // The 7A88 table; CB72 reads D22F's priority byte.
    if (hit_mode==7 && ((a>=0x83da && a<0x8652) || a==0xd269)) return rom[a]; // The 83DA recipes; CB72 reads D269's priority byte.
    if (hit_mode==9 && a>=0x4c52 && a<0x4c6e) return rom[a]; // 4C34's table.
    if (hit_mode==10 && a>=0x639a && a<0x63a4) return rom[a]; // 6334's number frame offsets.
    if (!readable(a)) { fprintf(stderr, "read %06X\n", a); fail("reference read outside declared fixture"); }
    return ram[a & 65535];
}
unsigned m68k_read_memory_16(unsigned a) {
    if (a & 1) fail("unaligned reference word read");
    return (m68k_read_memory_8(a) << 8) | m68k_read_memory_8(a + 1);
}
unsigned m68k_read_memory_32(unsigned a) {
    return (m68k_read_memory_16(a) << 16) | m68k_read_memory_16(a + 2);
}
void m68k_write_memory_8(unsigned a, unsigned v) {
    a &= 0xffffff;
    if (pair_mode==7 && running && !((a>=0xff31aa && a<0xff31ac) || (a>=0xff06d6 && a<0xff06da) || a==0xff06e3 || (a>=0xff010c && a<0xff010e) || (a>=0xffef00 && a<0xfff004))) fail("setup message write outside FF31AA/+46/+53/FF010C/stack");
    if (pair_mode && pair_mode!=7 && running && !((a>=0xff1b50 && a<0xff3008) || (a>=0xff311c && a<0xff3120) || ((pair_mode==1 || pair_mode==5) && a>=0xff31c0 && a<0xff31c4) || (pair_mode==5 && a>=0xff31b4 && a<0xff31bc)
        || (pair_mode==6 && ((a>=0xff447a && a<0xff453a) || (a>=0xff31ac && a<0xff31b4) || (a>=0xff0832 && a<0xff0836) || (a>=0xff09da && a<0xff09de))) || (a>=0xffef00 && a<0xfff004))) fail("pair write outside pool/head/anchor/stack");
    if (return_only_mode && running && !((a>=0xffef00 && a<0xfff004) || a==0xff1ab4 || a==0xff1ac0 || (a>=0xff1aba && a<0xff1abc))) fail("return-only write outside presentation/stack");
    if (hit_mode==1 && running && !((a>=0xff1b50 && a<0xff3120) || (a>=0xff447a && a<0xff453a) || (a>=0xff0a9e && a<0xff0aa6) || (a>=0xffef00 && a<0xfff004))) fail("pickup hit write outside pool/free stack/records/mailbox/stack");
    if ((hit_mode==2 || hit_mode==3) && running && !((a>=0xff1b50 && a<0xff3120) || (hit_mode==2 && a>=0xff0a9e && a<0xff0aa6) || (a>=0xffef00 && a<0xfff004))) fail("probe hit write outside pool/free stack/mailbox/stack");
    if (hit_mode==4 && running && !((a>=0xff1b50 && a<0xff3120) || (a>=0xff447a && a<0xff453a) || (a>=0xff31ac && a<0xff31b0) || (a>=0xff31bc && a<0xff31c0)
        || (a>=0xff06d6 && a<0xff06e8) || (a>=0xff087e && a<0xff0890) || (a>=0xff010c && a<0xff010e) || (a>=0xffef00 && a<0xfff004))) fail("ingredient write outside pool/records/globals/message/lock/stack");
    if (hit_mode==5 && running && !((a>=0xff1b50 && a<0xff3120) || (a>=0xff447a && a<0xff453a) || (a>=0xff31b0 && a<0xff31b4)
        || (a>=0xff06d6 && a<0xff06e8) || (a>=0xff087e && a<0xff0890) || (a>=0xff010c && a<0xff010e) || (a>=0xffef00 && a<0xfff004))) fail("second ingredient write outside pool/records/FF31B0/message/lock/stack");
    if (hit_mode==6 && running && !((a>=0xff1b50 && a<0xff3008) || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || (a>=0xffef00 && a<0xfff004))) fail("anchor write outside pool/transition/stack");
    if (hit_mode==7 && running && !((a>=0xff1b50 && a<0xff3120) || (a>=0xff447a && a<0xff453a) || (a>=0xff312c && a<0xff314c) || (a>=0xff316c && a<0xff3172)
        || (a>=0xff31a8 && a<0xff31b4) || (a>=0xff31c4 && a<0xff31c8) || (a>=0xff06d6 && a<0xff06e8) || (a>=0xff087e && a<0xff0890) || (a>=0xff010c && a<0xff010e)
        || (a>=0xff0a9e && a<0xff0aa6) || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || (a>=0xffef00 && a<0xfff004))) fail("completion write outside declared state");
    if (hit_mode==8 && running && !((a>=0xff1b50 && a<0xff3120) || (a>=0xff0bac && a<0xff0bb4) || (a>=0xffef00 && a<0xfff004))) fail("sparkle write outside pool/E918/stack");
    if (hit_mode==9 && running && !((a>=0xff1b50 && a<0xff3120) || (a>=0xff0a9e && a<0xff0aa6) || (a>=0xff0f00 && a<0xff0f04) || (a>=0xff444a && a<0xff444e)
        || (a>=0xff0836 && a<0xff0838) || a==0xff1ab4 || (a>=0xff1aba && a<0xff1abc) || (a>=0xff1aca && a<0xff1ace) || (a>=0xff1afe && a<0xff1b02) || (a>=0xffef00 && a<0xfff004)))
        fail("door write outside pool/free stack/mailbox/exit words/P1 actor/stack");
    if (hit_mode==10 && running && !((a>=0xff1b50 && a<0xff3008) || (a>=0xff311c && a<0xff3120) || (a>=0xff330c && a<0xff338a) || a==0xff33de || (a>=0xffef00 && a<0xfff004)))
        fail("hub setup write outside pool/free head/records/FF33DE/stack");
    if (hit_mode==11 && running && !((a>=0xff1b50 && a<0xff3120) || a==0xff0836 || a==0xff0837 || a==0xff09de || a==0xff09df || (a>=0xff06d6 && a<0xff06ea) || (a>=0xff087e && a<0xff0892)
        || (a>=0xff4446 && a<0xff444a) || (a>=0xff3398 && a<0xff339c) || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || a==0xff1ab4 || (a>=0xff1aba && a<0xff1abc)
        || (a>=0xff1aca && a<0xff1ace) || a==0xff1b02 || (a>=0xff1b08 && a<0xff1b0a) || (a>=0xff1b18 && a<0xff1b1c) || (a>=0xffef00 && a<0xfff004)))
        fail("hub door write outside pool/selectors/messages/FF4446/FF3398/timer/actors/stack");
    if (hit_mode==12 && running && !(a>=0xffef00 && a<0xfff004)) fail("hub exit test write outside stack");
    if (hit_mode==13 && running && !((a>=0xff0690 && a<0xff09e0) || (a>=0xff1ab4 && a<0xff3120) || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || (a>=0xff0f16 && a<0xff0f18)
        || (a>=0xff148c && a<0xff1494) || (a>=0xff17ac && a<0xff17b4) || (a>=0xff1aa8 && a<0xff1ab2) || (a>=0xffef00 && a<0xfff004)))
        fail("scene change write outside controls/actors/pool/timer/render lists/stack");
    if (hit_mode==14 && running && !((a>=0xff0690 && a<0xff09e0) || (a>=0xff1ab4 && a<0xff3120) || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || (a>=0xff0f16 && a<0xff0f18)
        || (a>=0xff148c && a<0xff1494) || (a>=0xff17ac && a<0xff17b4) || (a>=0xff1aa8 && a<0xff1ab2) || (a>=0xff0bac && a<0xff0bb4) || (a>=0xff33ce && a<0xff33d0) || (a>=0xff33d8 && a<0xff33da)
        || (a>=0xff33e0 && a<0xff33e2) || (a>=0xff33e4 && a<0xff33e6) || (a>=0xffef00 && a<0xfff004)))
        fail("second level entry write outside controls/actors/pool/timer/render lists/random/globals/stack");
    if (hit_mode==15 && running && !(a==0xff06a6 || (a>=0xff0b90 && a<0xff0ba4) || (a>=0xff0ede && a<0xff0ee0) || (a>=0xff0f0e && a<0xff0f12) || (a>=0xffef00 && a<0xfff004)))
        fail("hint screen write outside +16/timer/FF0F0E/FF0F10/stack");
    if (table_mode==4 && running && !((a>=0xff31bc && a<0xff31c0) || (a>=0xff1b50 && a<0xff3008) || (a>=0xffef00 && a<0xfff004))) fail("spell mix write outside FF31BC/FF31BE/pool/stack");
    if (collision_mode && running && !((a>=0xffef00 && a<0xfff004) || ((collision_mode==3 || collision_mode==5) && (a==0xff1ab4 || a==0xff1ac0 || (a>=0xff1aba && a<0xff1abc))))) fail("collision write outside presentation/stack");
    if ((private_mode || (table_mode && table_mode!=3 && table_mode!=4)) && running && !((a>=0xff1ab4 && a<0xff1b02) || (a>=0xffef00 && a<0xfff004)))
        fail("private write outside object/stack");
    if (table_mode==3 && running && !((a>=0xff31bc && a<0xff31c0) || (a>=0xffef00 && a<0xfff004))) fail("table writer escaped globals/stack");
    if (trail_mode && running && !((a>=0xff1ab4 && a<0xff1b02) || (a>=0xff2000 && a<0xff24e0)
        || (a>=0xff0bac && a<0xff0bb4) || (a>=0xff3008 && a<0xff3050)
        || (a>=0xff311c && a<0xff3120) || (a>=0xffef00 && a<0xfff004))) fail("trail write outside state/pool/random/stack");
    if (level_banner && running && !((a>=0xff4444 && a<0xff4446) || (a>=0xff010c && a<0xff010e) || (a>=0xffef00 && a<0xfff004)))
        fail("banner write outside scratch/lock/stack");
    if (pad_conversion && running && !((a>=0xff06a5 && a<0xff06a8) || (a>=0xff06aa && a<0xff06b2)))
        fail("pad conversion write outside output fields");
    if (!pair_mode && !return_only_mode && !hit_mode && !collision_mode && !table_mode && !private_mode && !trail_mode && !level_banner && !pad_conversion && running && !((score && ((a>=0xff06fe && a<0xff0708) || (a>=0xff070e && a<0xff0710) || (a>=0xff443e && a<0xff4442))) || (exit_tally && a>=0xff070c && a<0xff070e) || (bonus && ((a>=0xff0802 && a<0xff0818) || (a>=0xff0830 && a<0xff0832) || (a>=0xff0104 && a<0xff0106))) || (palette && a>=0xff0dc8 && a<0xff0df8) || (tally && ((a>=0xff0714 && a<0xff0716) || (a>=0xff0f0e && a<0xff0f10)
        || (a>=0xff340a && a<0xff340c) || (a>=0xff3402 && a<0xff3404)))
        || (transition && ((a >= 0xff0b90 && a < 0xff0ba4) || (a >= 0xff0edc && a < 0xff0ee0)
        || (a >= 0xff0732 && a < 0xff0736) || (a >= 0xff33e0 && a < 0xff33e2)))
        || (coast_entry && a >= 0xff0836 && a < 0xff0838)
        || (dispatch && a >= 0xff06d2 && a < 0xff06d6)
        || (actions && ((a >= 0xff33d8 && a < 0xff33dc) || (a >= 0xff0ad6 && a < 0xff0ade)))
        || (reversal && ((a >= 0xff2000 && a < 0xff24e0) || (a >= 0xff3008 && a < 0xff3050)
        || (a >= 0xff311c && a < 0xff3120)))
        || (controller && ((a >= 0xff0a9e && a < 0xff0aa6)
        || (a >= 0xff1ac2 && a < 0xff1ac6) || (a >= 0xff1ace && a < 0xff1ad2)))
        || (a >= 0xff4442 && a < 0xff4446)
        || (!movement && a >= 0xff0692 && a < 0xff0696)
        || (movement && ((a == 0xff1ab4) || (a >= 0xff1ab6 && a < 0xff1ac2)
            || (a >= 0xff1aca && a < 0xff1ace) || (a >= 0xff1ad6 && a < 0xff1ad8)
            || (a >= 0xff1ada && a < 0xff1adc) || (a >= 0xff1ade && a < 0xff1ae0)))
        || (airborne && a >= 0xff1ac6 && a < 0xff1ac8)
        || (a >= 0xffef00 && a < 0xfff004))) fail("reference write outside scratch/state/stack");
    if (a < 0xff0000) fail("reference attempted ROM/device write");
    ram[a & 65535] = (unsigned char)v;
}
void m68k_write_memory_16(unsigned a, unsigned v) {
    if (a & 1) fail("unaligned reference word write");
    if ((pair_mode==7 || hit_mode==4 || hit_mode==5 || hit_mode==7) && running && ((a&0xffffff)==0xc00000 || (a&0xffffff)==0xc00004 || (a&0xffffff)==0xc00006)) {
        // Sink CB9A's VDP words; record them for the sequence check, no VDP emulation.
        if (message_vdp_count>=40) fail("setup message VDP write budget exceeded");
        if ((a&0xffffff)==0xc00000 && m68k_read_memory_16(0xff010c)!=1) message_lock_ok=0;
        message_vdp[message_vdp_count][0]=a&0xffffff;message_vdp[message_vdp_count++][1]=v&0xffff;return;
    }
    if (level_banner && running && ((a&0xffffff)==0xc00000 || (a&0xffffff)==0xc00004 || (a&0xffffff)==0xc00006)) {
        // Execute the original rendering callees, but only sink their writes.
        // No device reads, VDP emulation or rendered-output parity is claimed.
        ++banner_device_writes;return;
    }
    m68k_write_memory_8(a, v >> 8); m68k_write_memory_8(a + 1, v);
}
void m68k_write_memory_32(unsigned a, unsigned v) {
    m68k_write_memory_16(a, v >> 16); m68k_write_memory_16(a + 2, v);
}
static int valid_decimal(unsigned v) {
    for (unsigned i=0;i<8;++i,v>>=4) if ((v&15)>9) return 0;
    return 1;
}
static void hook(unsigned pc) {
    if (pair_mode && pc==0xf9f4) ++pair_pops;
    if (pair_mode==8 && (pc==0x7fbe || pc==0x7154 || pc==0x735e || pc==0x7568)) pairs_current=pc==0x7fbe ? 0 : pc==0x7154 ? 1 : pc==0x735e ? 2 : 3;
    if (pair_mode==7 && pc==0x7dec) message_selected=1;
    if (pair_mode==7 && pc==0x7e08) message_selected=2;
    if (return_only_mode && pc==0xf76c) ++return_only_presentations;
    if (return_only_mode && pc==0x12646) ++return_only_returns;
    if ((hit_mode==4 || hit_mode==5) && pc==0x79b6) ++delivery_count; // The copy's callback ran.
    if (hit_mode==7 && pc==0xf9e2) ++completion_pops;
    if (hit_mode==11 && pc==0x623c) {++hub_entries;hub_touched=m68k_get_reg(NULL,M68K_REG_A5);}
    if (hit_mode==7 && pc==0x7ebe) completion_effect=1; // JSR (A2): the matched recipe's effect.
    if (hit_mode==2 && (pc==0x7976 || pc==0x799c)) { // After 59AE (A6 = sparkle) and F994 (A5 = copy).
        if (delivery_count>=8) fail("probe hit allocation budget exceeded");
        delivery_kinds[delivery_count]=pc==0x799c;delivery_created[delivery_count++]=m68k_get_reg(NULL,pc==0x7976 ? M68K_REG_A6 : M68K_REG_A5)&0xffffff;
    }
    if ((collision_mode || hit_mode) && pc==0xac5e) {
        unsigned control=m68k_get_reg(NULL,M68K_REG_A5);
        if(control!=0xffff0690 && control!=0xffff0838)fail("unsupported collision control identity");
        if(control==0xffff0838 && !collision_secondary)fail("secondary collision input unavailable");
        ++collision_queries;
    }
    if (table_mode && pc==0x7a92 && ++table_work>table_budget) fail("table motion loop budget exhausted");
    if (table_mode && pc==0x7a9e) {
        unsigned cursor=m68k_get_reg(NULL,M68K_REG_A0);
        if (cursor<0x7a58 || cursor>=0x7a88 || (cursor&1)) fail("unsupported table motion cursor");
    }
    if (score && (pc==0xadf4 || pc==0xae4c)) {
        if (!valid_decimal(m68k_get_reg(NULL,M68K_REG_D0)) || !valid_decimal(m68k_read_memory_32(pc==0xadf4 ? 0xff06fe : 0xff0702)))
            fail("unsupported packed score digit");
        if (pc==0xae4c) { if (++score_work>4096) fail("score threshold budget exhausted"); ++score_advances; }
    }
    if (!code(pc)) {
        fprintf(stderr,"reference unsupported code boundary %06x\n",pc);exit(2);
    }
    if (++instructions > (table_mode ? 1100000u : movement ? 16000000u : level_banner ? 2048u : hit_mode==7 ? 3996u : hit_mode==10 ? 2044u : hit_mode==13 || hit_mode==14 ? 15996u : hit_mode ? 1024u : pair_mode==8 ? 508u : pair_mode==6 ? 1996u : pair_mode==5 ? 596u : 256u)) fail("reference instruction budget exceeded");
    if (level_banner && pc==0x17532) {
        const unsigned labels[]={0x647c,0x64e8,0x6497,0x6503,0x64b2,0x651e,0x64cd,0x6539};
        unsigned label=0;while (label<8 && labels[label]!=m68k_get_reg(NULL,M68K_REG_A0)) ++label;
        if (label==8 || ++banner_texts!=1 || banner_numbers) fail("unsupported banner text request");
        banner_request[0]=label;banner_request[1]=m68k_get_reg(NULL,M68K_REG_A1)&65535;
    }
    if (level_banner && pc==0x175d0) {
        if (banner_texts!=1 || ++banner_numbers!=1) fail("unsupported banner number request");
        banner_request[2]=1;banner_request[3]=m68k_get_reg(NULL,M68K_REG_D0)&65535;
        banner_request[4]=m68k_get_reg(NULL,M68K_REG_A1)&65535;
    }
    if (pc == 0xfcb32) {
        if (sound_count >= 1024) fail("sound request budget exceeded");
        for (unsigned i=0;i<4;++i) sound_requests[sound_count][i] = m68k_read_memory_16(0xff0a9e + 2*i);
        ++sound_count;
    }
    if (actions && pc == 0xed6e6) {
        unsigned sample=m68k_get_reg(NULL,M68K_REG_D0);
        if (sample_count >= 1024 || (sample!=0xf0000 && !(score && sample==0xf25ea))) fail("unsupported sample request");
        sample_requests[sample_count][0]=sample==0xf25ea ? 1 : 0; // Logical resource identity.
        sample_requests[sample_count][1]=m68k_get_reg(NULL,M68K_REG_D1)&65535;
        sample_requests[sample_count++][2]=m68k_get_reg(NULL,M68K_REG_D2)&65535;
    }
    if ((reversal || trail_mode || hit_mode==8) && pc == 0xf9ce) {
        if (spawn_count >= 128) fail("reference spawn budget exhausted");
        spawned[spawn_count++] = m68k_get_reg(NULL,M68K_REG_A5) & 0xffffff;
    }
    if ((reversal || trail_mode) && pc == 0xfaa4) ++releases;
    ++visits[pc]; ++total_instructions;
    if (pc == 0x9ac8 || pc == 0x9b04 || pc == 0x9bca || pc == 0x9c18 || pc == 0xa16a || pc == 0xa180) ++horizontal_steps;
    if (pc == 0x9a80) ++settle_calls;
    if (pc == 0xab8a) ++landings;
    if (bonus && pc==0x451e && ((m68k_get_reg(NULL,M68K_REG_A0)&0xffffff)<0xff0802 || (m68k_get_reg(NULL,M68K_REG_A0)&0xffffff)>=0xff0818))
        fail("bonus availability scan escaped table");
    if (bonus && (pc==0x451e || pc==0x477c)) {
        if (++bonus_probes>4096u) fail("bonus selection budget exhausted");
    }
    if (bonus && pc==0x5296) ++bonus_calls;
    if (bonus && pc==0x52a0) {
        unsigned a=m68k_get_reg(NULL,M68K_REG_A1)&0xffffff;
        if (bonus_count>=80 || a<0xff0802 || a>=0xff0818 || (a&1)) fail("bonus selection escaped table");
        bonus_slots[bonus_count]=(a-0xff0802)/2;bonus_values[bonus_count++]=m68k_get_reg(NULL,M68K_REG_D3)&65535;
    }
    if (bonus && pc==0x4770 && (m68k_get_reg(NULL,M68K_REG_D2)!=0 || !m68k_read_memory_16(0xff082e) || m68k_read_memory_16(0xff082e)>11))
        fail("unsupported bonus selection mode/count");
    if (pc == 0x137ce) {
        if (!palette || (m68k_get_reg(NULL,M68K_REG_D0)&65535)!=2 || m68k_get_reg(NULL,M68K_REG_A0)!=0xffff0ea8)
            fail("unsupported palette bank/source");
        ++palette_calls;
    }
    if (pc == 0xaa50) ++airborne_transitions;
    if (pc == 0x9a18) tile = m68k_get_reg(NULL, M68K_REG_D0) & 65535;
}
static void call(unsigned pc) {
    m68k_write_memory_32(0xfff000, 0x100000);
    m68k_set_reg(M68K_REG_SP, 0xfffff000);
    m68k_set_reg(M68K_REG_PC, pc);
    instructions = 0; score_work = 0; table_work = 0; running = 1; immediate_continuation = 0;
    int boundary_stop = 0;
    for (unsigned steps = 0; m68k_get_reg(NULL, M68K_REG_PC) != 0x100000; ++steps) {
        const unsigned current_pc = m68k_get_reg(NULL, M68K_REG_PC);
        if (table_mode==3 && pc==0x7cc8 && current_pc==0x7cea) {boundary_stop=1;break;}
        if (pair_mode && current_pc==0xfa1e) {pair_exhausted=boundary_stop=1;break;} // Never-returning VDP loop.
        if (pair_mode==5 && pc==0x6886 && current_pc==0x68a4) {boundary_stop=1;break;} // Setup continues at 68A4.
        if (pair_mode==6 && pc==0x68a4 && current_pc==0x68bc) {boundary_stop=1;break;} // Setup continues at 68BC.
        if (pair_mode==7 && pc==0x68bc && (current_pc==0x68c4 || current_pc==0x6f02)) {boundary_stop=1;break;} // 68C4, or 6EF0's allocating path.
        if (pair_mode==8 && pc==0x68c4 && current_pc==0x68d4) {boundary_stop=1;break;} // Setup continues at 68D4.
        if (hit_mode && pc==0x69aa && current_pc==0x69c2) {boundary_stop=1;break;} // After the +46 service.
        if (hit_mode==11 && pc==0x5f5e && current_pc==0x5f76) {boundary_stop=1;break;} // The hub walk, after the +46 service.
        if (hit_mode==10 && pc==0x5e86 && current_pc==0x5e8e) {boundary_stop=1;break;} // The setup continues at 5E8E.
        if (hit_mode==10 && (current_pc==0xfa1e || current_pc==0xf9d0)) {hit_stop=current_pc;boundary_stop=1;break;} // Never-returning allocator loops.
        if (hit_mode==12 && current_pc==0x5eea) {hit_stop=current_pc;boundary_stop=1;break;} // The loop continues.
        if (hit_mode==13 && ((pc==0x488 && current_pc==0x49e) || (pc==0x16fb4 && current_pc==0x16fba) || (pc==0x16ff8 && current_pc==0x17004) || (pc==0x5d6a && current_pc==0x5d7e) || (pc==0x5ed4 && current_pc==0x5edc)))
            {boundary_stop=1;break;} // The fragment's caller continues.
        if (hit_mode==14 && ((pc==0x16fb4 && current_pc==0x16fba) || (pc==0x16ff8 && current_pc==0x17004) || (pc==0xe44 && current_pc==0xe52) || (pc==0x11a6 && current_pc==0x11ee)
            || (pc==0x1356 && current_pc==0x1364) || (pc==0x774 && current_pc==0x77c)))
            {boundary_stop=1;break;} // The fragment's caller continues.
        if (hit_mode==15 && current_pc==0x19676) {boundary_stop=1;break;} // The loop continues.
        if (hit_mode==1 && (current_pc==0x6e32 || current_pc==0x6e5e || current_pc==0x6e8a || current_pc==0xcaf0)) {hit_stop=current_pc;boundary_stop=1;break;} // Family branch or seeded callback.
        if ((hit_mode==2 && current_pc==0xcaf0) || (hit_mode==3 && current_pc==0x79b6) || (hit_mode==4 && current_pc==0x7a00)) {hit_stop=current_pc;boundary_stop=1;break;} // Probe or copy callback, second ingredient.
        if (hit_mode==2 && (current_pc==0xfa1e || current_pc==0xf9d0)) {hit_exhausted=current_pc;boundary_stop=1;break;} // Never-returning allocator loops.
        if (hit_mode==6 && current_pc==0x7b60) {hit_stop=current_pc;boundary_stop=1;break;} // 7B58's completion is the completion corpus.
        if (hit_mode==7 && (current_pc==0x7ef4 || current_pc==0x9288 || current_pc==0x9182 || current_pc==0x6f44 || current_pc==0x9614 || current_pc==0x9682
            || current_pc==0xfa1e || recipe_stop(current_pc))) {hit_stop=current_pc;boundary_stop=1;break;} // Paths outside the reconstructed recipe.
        if (hit_mode==8 && current_pc==0xf9d0) {hit_stop=current_pc;boundary_stop=1;break;} // F994's never-returning exhaustion loop.
        if (hit_mode==9 && (current_pc==0x70fe || current_pc==0x7072)) {hit_stop=current_pc;boundary_stop=1;break;} // An active +1A2 link; two players.
        if (hit_mode>=7 && current_pc==0xcaf0) {hit_stop=current_pc;boundary_stop=1;break;} // A seeded presentation callback.
        if ((return_only_mode || collision_mode==3 || collision_mode==5 || table_mode==2 || private_mode==2 || trail_mode==2 || trail_mode==3) && pc==0x69aa && current_pc==0x69c2) {
            boundary_stop=1;break; // Includes real +46 RTS; stop before advancing A6.
        }
        if (effect_mode && (pc == 0x80a || pc == 0x69aa) &&
            (current_pc == 0x81c || current_pc == 0x822 || current_pc == 0x69bc || current_pc == 0x69c2)) {
            boundary_stop = 1; break; // Original active gate, presentation and handler; no fabricated RTS.
        }
        if (scheduling == 2 && pc == 0xf8f6 && (current_pc == 0xf906 || current_pc == 0xf90c)) {
            boundary_stop = 1; break; // Before the later +46 service or inactive tail, no fake RTS.
        }
        if (airborne && !controller && (current_pc == 0xa1be || current_pc == 0xa246)) {
            immediate_continuation = 1; break; // Stop BEFORE the idle instruction; no simulated RTS.
        }
        if (steps > (table_mode ? 1100004u : movement ? 16000004u : level_banner ? 2052u : hit_mode==7 ? 4000u : hit_mode==10 ? 2048u : hit_mode==13 || hit_mode==14 ? 16000u : hit_mode ? 1028u : pair_mode==8 ? 512u : pair_mode==6 ? 2000u : pair_mode==5 ? 600u : 260u)) fail("reference return budget exceeded");
        m68k_execute(1);
    }
    running = 0; boundary_stop_seen = boundary_stop;
    // Exhaustion depth: F9E2 under 6AF0 under 6A94 (tail pickups), or under one BSR (prefix, tail links).
    // 7FBE also saves A5/A6 with MOVEM before its BSRs to F9E2.
    const unsigned exhausted_sp=pair_mode==6 && pair_pops<tail_pickups ? 0xffffefe8u : pair_mode==8 && !pairs_current ? 0xffffefecu : pair_mode>=5 ? 0xffffeff4u : 0xffffeff8u;
    // 6EF0's open path stops at 6F02 inside the BSR from 68C0.
    // 7910's allocators loop inside JSR 59AE/F9E2 or JSR F994, below its two pushes.
    // The completion's stops: inside BSR 7ED6 (7EF4, below 7B72's A6 push, BSR
    // 7E18 and two word pushes), 9288 in 7E18, an effect entered by JSR (A2)
    // (also 9182 and 6F44 after 867A's BRA), FA1E inside F9E2 under 7F08's push
    // and BSR or under 6F02's JSR, and 9614/9682 below 95EE's MOVEM of fifteen
    // registers. F994's loop sits below 7FA8's JSR, 5A9A's JSR and its A0 push.
    // The hub setup's allocators loop inside F9E2 (below 5E8A's BSR, 6110's BSR,
    // 611E's JSR and its A0 push) or F994 (one BSR deeper, through 6334); 6024's
    // BRA to 5EEA leaves the stack as called.
    const unsigned stopped_sp=hit_mode==10 && hit_stop ? (hit_stop==0xfa1e ? 0xffffeff0u : 0xffffefecu) : hit_mode==12 && hit_stop ? 0xfffff000u
        : hit_exhausted ? (hit_exhausted==0xfa1e ? 0xffffefe8u : 0xffffefecu)
        : hit_mode>=7 && hit_stop==0xcaf0 ? 0xffffeffcu
        : hit_mode==7 && hit_stop ? (hit_stop==0x7ef4 ? 0xffffefecu : hit_stop==0x9288 && !completion_effect ? 0xffffeff4u : hit_stop==0x9614 || hit_stop==0x9682 ? 0xffffefb0u
            : hit_stop==0xfa1e ? (completion_pops>1 ? 0xffffefe8u : 0xffffefe0u) : 0xffffeff0u)
        : hit_mode==8 && hit_stop ? 0xffffeff0u
        : (pair_mode==7 && m68k_get_reg(NULL, M68K_REG_PC)==0x6f02) || (hit_mode && hit_stop) ? 0xffffeffcu : 0xfffff000u;
    if (m68k_get_reg(NULL, M68K_REG_SP) != (pair_exhausted ? exhausted_sp : (immediate_continuation || boundary_stop) ? stopped_sp : 0xfffff004u)) fail("reference stack unbalanced");
}
static unsigned load(const char *path, unsigned char *out, unsigned limit) {
    FILE *f = fopen(path, "rb"); if (!f) fail("reference input missing");
    unsigned n = (unsigned)fread(out, 1, limit, f);
    if (ferror(f) || fgetc(f) != EOF) fail("reference input oversized or unreadable");
    fclose(f); return n;
}
static unsigned actor_word(unsigned offset) { return m68k_read_memory_16(0xff1ab4 + offset); }
static void movement_cases(void) {
    unsigned op, x, y, speed, positive, negative, damping, sx, sy, repeats, cases = 0;
    int fields;
    while ((fields = scanf("%u %u %u %u %u %u %u %u %u %u", &op,&x,&y,&speed,&positive,&negative,&damping,&sx,&sy,&repeats)) == 10) {
        if (++cases > 1000000 || op > 7 || x > 65535 || y > 65535 || speed > 65535 || positive > 65535
            || negative > 65535 || damping > 65535 || sx > 65535 || sy > 65535 || !repeats || repeats > 16)
            fail("invalid movement case");
        memset(ram + 0x1ab4, 0xa5, 0x4e);
        m68k_write_memory_16(0xff1ab6,x); m68k_write_memory_16(0xff1ab8,y);
        m68k_write_memory_16(0xff1ad6,speed);
        m68k_write_memory_16(0xff1ada,0x1357); m68k_write_memory_16(0xff1ade,0x2468);
        m68k_write_memory_32(0xff1aca,0xcafe);
        m68k_write_memory_16(0xff06ea,positive); m68k_write_memory_16(0xff06ec,negative);
        m68k_write_memory_16(0xff06f6,damping);
        m68k_write_memory_16(0xff4442,sx); m68k_write_memory_16(0xff4444,sy);
        for (int reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg) m68k_set_reg(reg,0x5a5a0000u+(unsigned)reg);
        m68k_set_reg(M68K_REG_SR,0x2710);m68k_set_reg(M68K_REG_A5,0xffff0690);m68k_set_reg(M68K_REG_A6,0xffff1ab4);
        horizontal_steps=0;airborne_transitions=0;
        const unsigned entries[]={0x9aae,0x9ac8,0x9b04,0x9a5e,0x9a6c,0xacd6,0xace8,0xaa50};
        for (unsigned repeat=0;repeat<repeats;++repeat) call(entries[op]);
        unsigned handler=m68k_read_memory_32(0xff1aca);
        if (handler != 0xcafe && handler != 0xaaea) fail("unmodeled movement handler");
        if (m68k_get_reg(NULL,M68K_REG_D2)!=0x5a5a0002) fail("movement D2 preservation failed");
        printf("%u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u\n",
            actor_word(2),actor_word(4),actor_word(0x22),actor_word(0x26),actor_word(0x2a),handler==0xaaea,
            m68k_read_memory_8(0xff1ab4),actor_word(6),actor_word(8),actor_word(10),
            m68k_read_memory_8(0xff1ac0),m68k_read_memory_8(0xff1ac1),
            m68k_read_memory_16(0xff4442),m68k_read_memory_16(0xff4444),horizontal_steps,airborne_transitions);
    }
    if (fields!=EOF || ferror(stdin)) fail("movement transport failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static const unsigned motion_handlers[] = {0xcafe,0xaaea,0xab04,0xa408,0xa546,0xa6c8,0xa88e,0xa1be,0xa246,0xa2ec,0xa384,0xa4ec,0xa634,0xa27e,0xa7ec,0xa9b2,0x9c90,0x9d26,0x9d88,0x9dcc,0x12646,0x710e,0x7126,0x632a,0x51c8,0x5222,0x5204,0x5132,0x5188};
static unsigned handler_id(void) {
    const unsigned handler = m68k_read_memory_32(0xff1aca);
    for (unsigned i=0;i<sizeof(motion_handlers)/sizeof(motion_handlers[0]);++i)
        if (handler==motion_handlers[i]) return i;
    fail("unmodeled airborne handler"); return 0;
}
static void airborne_cases(void) {
    unsigned f[21], cases=0;
    int fields;
    while ((fields=scanf("%u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u",
            &f[0],&f[1],&f[2],&f[3],&f[4],&f[5],&f[6],&f[7],&f[8],&f[9],&f[10],&f[11],&f[12],&f[13],
            &f[14],&f[15],&f[16],&f[17],&f[18],&f[19],&f[20]))==21) {
        if (++cases>1000000 || f[0]>6 || (f[7]!=1 && f[7]!=2) || !f[20] || f[20]>16 || (f[0] && f[20]!=1))
            fail("invalid airborne case");
        for (unsigned i=1;i<20;++i) if (f[i]>65535 || (i>=14 && i<=16 && f[i]>255)) fail("invalid airborne field");
        memset(ram+0x1ab4,0xa5,0x4e);
        m68k_write_memory_16(0xff1ab6,f[1]);m68k_write_memory_16(0xff1ab8,f[2]);
        m68k_write_memory_16(0xff1ad6,f[3]);m68k_write_memory_16(0xff1ada,f[4]);m68k_write_memory_16(0xff1ade,f[5]);
        m68k_write_memory_16(0xff1ac6,f[6]);m68k_write_memory_32(0xff1aca,motion_handlers[f[7]]);
        m68k_write_memory_16(0xff06ea,f[8]);m68k_write_memory_16(0xff06ec,f[9]);m68k_write_memory_16(0xff06f6,f[10]);
        m68k_write_memory_16(0xff06f0,f[11]);m68k_write_memory_16(0xff06fa,f[12]);m68k_write_memory_16(0xff06fc,f[13]);
        m68k_write_memory_8(0xff06a6,f[14]);m68k_write_memory_8(0xff06ac,f[15]);m68k_write_memory_8(0xff06ad,f[16]);
        m68k_write_memory_16(0xff0f16,f[17]);m68k_write_memory_16(0xff4442,f[18]);m68k_write_memory_16(0xff4444,f[19]);
        for (int reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg) m68k_set_reg(reg,0x5a5a0000u+(unsigned)reg);
        m68k_set_reg(M68K_REG_SR,0x2710);m68k_set_reg(M68K_REG_A5,0xffff0690);m68k_set_reg(M68K_REG_A6,0xffff1ab4);
        horizontal_steps=0;settle_calls=0;landings=0;
        unsigned completed=0,contact=0;
        const unsigned entries[]={0,0x9bac,0x9bca,0x9c18,0xab8a,0xa658,0xa690};
        for (unsigned repeat=0;repeat<f[20];++repeat) {
            call(f[0] ? entries[f[0]] : motion_handlers[handler_id()]);++completed;
            // Only the horizontal helper exposes its returned Z in the contract.
            if (f[0]==1) contact=!!(m68k_get_reg(NULL,M68K_REG_SR)&4);
            if (immediate_continuation || (!f[0] && handler_id()!=1 && handler_id()!=2)) break;
        }
        if (m68k_get_reg(NULL,M68K_REG_D2)!=0x5a5a0002) fail("airborne D2 preservation failed");
        printf("%u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u %u\n",
            actor_word(2),actor_word(4),actor_word(0x22),actor_word(0x26),actor_word(0x2a),handler_id(),
            m68k_read_memory_8(0xff1ab4),actor_word(6),actor_word(8),actor_word(10),
            m68k_read_memory_8(0xff1ac0),m68k_read_memory_8(0xff1ac1),
            m68k_read_memory_16(0xff4442),m68k_read_memory_16(0xff4444),actor_word(0x12),
            horizontal_steps,settle_calls,landings,completed,immediate_continuation,contact);
    }
    if (fields!=EOF || ferror(stdin)) fail("airborne transport failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static const unsigned callbacks[] = {0xcafe,0xa2e8,0xa380,0xa50e,0xa654,0xa774,0xa93a,0xa814,0xa9da,0xf938,0xa196,0xaa50};
static unsigned callback_id(void) {
    unsigned v=m68k_read_memory_32(0xff1ace);
    for (unsigned i=0;i<sizeof(callbacks)/sizeof(callbacks[0]);++i) if (v==callbacks[i]) return i;
    fail("unmodeled presentation callback"); return 0;
}
static void actor_cases(void) {
    unsigned f[131]={0},cases=0;
    for (;;) {
        int first=scanf("%u",&f[0]); if (first==EOF) break;
        if (first!=1) fail("actor transport failure");
        for (unsigned i=1;i<(score ? 77u : exit_tally ? 72u : bonus ? 91u : palette ? 131u : tally ? 67u : transition ? 60u : dispatch ? 47u : actions ? 43u : 35u);++i) if (scanf("%u",&f[i])!=1) fail("incomplete actor case");
        if (++cases>1000000 || !f[0] || f[0]>(exit_tally ? 28u : palette ? 26u : tally ? 25u : transition ? 23u : 20u) || f[15]>11 || !f[34] || f[34]>16) fail("invalid actor case");
        for (unsigned i=1;i<34;++i)
            if (f[i]>65535 || ((i==7 || i==11 || i==12 || (i>=25 && i<=30)) && f[i]>255)) fail("invalid actor field");
        if (actions) {
            for (unsigned i=35;i<43;++i) if (f[i]>65535 || ((i==38 || i==66) && f[i]>255)) fail("invalid action field");
            m68k_write_memory_16(0xff33e0,f[35]);m68k_write_memory_16(0xff33d8,f[36]);m68k_write_memory_16(0xff33da,f[37]);
            m68k_write_memory_8(0xff06a4,f[38]);
            for (unsigned i=0;i<4;++i) m68k_write_memory_16(0xff0ad6+2*i,f[39+i]);
        }
        memset(ram+0x1ab4,0xa5,0x4e);
        if (reversal) {
            memset(ram+0x2000,0xa5,0x4e0);
            m68k_write_memory_32(0xff3008,0);
            for (unsigned i=0;i<16;++i) m68k_write_memory_32(0xff300c+4*i,0xffff2000+78*i);
            m68k_write_memory_32(0xff311c,empty_pool ? 0xffff300c : 0xffff304c);
            m68k_write_memory_32(0xff1afe,0xffff0690);
        }
        if (transition) {
            for (unsigned i=47;i<67;++i) if (f[i]>65535) fail("invalid transition field");
            for (unsigned i=0;i<4;++i) m68k_write_memory_16(0xff0b90+2*i,f[47+i]);
            const unsigned curves[]={0xcafe,0x1356a,0x135aa,0x135ea};
            for (unsigned i=0;i<3;++i) {
                if (f[51+i]>3) fail("invalid transition curve");
                m68k_write_memory_32(0xff0b98+4*i,curves[f[51+i]]);
            }
            m68k_write_memory_16(0xff0edc,f[54]);m68k_write_memory_16(0xff0ede,f[55]);
            m68k_write_memory_16(0xff4446,f[56]);m68k_write_memory_16(0xff4448,f[57]);
            m68k_write_memory_16(0xff0732,f[58]);m68k_write_memory_16(0xff0734,f[59]);
            m68k_write_memory_32(0xff1afe,0xffff0690);
            m68k_write_memory_32(0xff0690,0xffff1ab4);
        }
        if (tally) {
            if (f[66]>255) fail("invalid Start field");
            m68k_write_memory_16(0xff33ce,f[60]);m68k_write_memory_16(0xff0714,f[61]);
            m68k_write_memory_16(0xff0f0e,f[62]);m68k_write_memory_16(0xff340a,f[63]);
            m68k_write_memory_16(0xff3402,f[64]);m68k_write_memory_16(0xff0104,f[65]);
            m68k_write_memory_8(0xff06b1,f[66]);
        }
        if (exit_tally) {
            for (unsigned i=67;i<72;++i) if (f[i]>65535) fail("invalid exit tally field");
            m68k_write_memory_16(0xff0efe,f[67]);m68k_write_memory_16(0xff070e,f[68]);
            m68k_write_memory_16(0xff070c,f[69]);m68k_write_memory_16(0xff33c8,f[70]);m68k_write_memory_16(0xff33cc,f[71]);
        }
        if (bonus) {
            for (unsigned i=67;i<91;++i) if (f[i]>65535) fail("invalid bonus field");
            m68k_write_memory_16(0xff082e,f[67]);m68k_write_memory_16(0xff0830,f[68]);
            for (unsigned i=0;i<11;++i) {m68k_write_memory_16(0xff0802+2*i,f[69+i]);m68k_write_memory_16(0xff0818+2*i,f[80+i]);}
        }
        if (score) {
            if (f[75]>65535) fail("invalid score reward");
            m68k_write_memory_32(0xff06fe,f[72]);m68k_write_memory_32(0xff0702,f[73]);m68k_write_memory_32(0xff06c2,f[74]);
            m68k_write_memory_16(0xff0706,f[75]);m68k_write_memory_32(0xff443e,f[76]);
        }
        score_advances=0;
        bonus_probes=bonus_count=bonus_calls=0;
        if (palette) {
            for (unsigned i=67;i<131;++i) if (f[i]>(i<83 ? 65535u : 255u)) fail("invalid palette field");
            for (unsigned i=0;i<16;++i) m68k_write_memory_16(0xff0ea8+2*i,f[67+i]);
            for (unsigned i=0;i<48;++i) m68k_write_memory_8(0xff0dc8+i,f[83+i]);
        }
        palette_calls=0;
        spawn_count=0;
        if (dispatch) {
            if (f[43]>1 || f[44]>65535 || f[45]>65535 || f[46]>65535) fail("invalid dispatch field");
            m68k_write_memory_32(0xff1afa,f[43] ? 0x12646 : 0xcafe);
            m68k_write_memory_16(0xff0836,f[44]);
            m68k_write_memory_16(0xff06d2,f[45]);m68k_write_memory_16(0xff06d4,f[46]);
        }
        const unsigned actor_offsets[]={2,4,0x22,0x26,0x2a,0x12};
        for (unsigned i=0;i<6;++i) m68k_write_memory_16(0xff1ab4+actor_offsets[i],f[i+1]);
        m68k_write_memory_32(0xff1aca,motion_handlers[f[0]]);
        m68k_write_memory_8(0xff1ab4,f[7]);
        for (unsigned i=0;i<3;++i) m68k_write_memory_16(0xff1aba+i*2,f[8+i]);
        m68k_write_memory_8(0xff1ac0,f[11]);m68k_write_memory_8(0xff1ac1,f[12]);
        m68k_write_memory_16(0xff1ac2,f[13]);m68k_write_memory_16(0xff1ac4,f[14]);
        m68k_write_memory_32(0xff1ace,callbacks[f[15]]);
        const unsigned control_offsets[]={0x5a,0x5c,0x66,0x60,0x6a,0x6c,0x5e,0x62,0x64};
        for (unsigned i=0;i<9;++i) m68k_write_memory_16(0xff0690+control_offsets[i],f[16+i]);
        const unsigned input_offsets[]={0x16,0x17,0x1a,0x1b,0x1c,0x1d};
        for (unsigned i=0;i<6;++i) m68k_write_memory_8(0xff0690+input_offsets[i],f[25+i]);
        m68k_write_memory_16(0xff0f16,f[31]);m68k_write_memory_16(0xff4442,f[32]);m68k_write_memory_16(0xff4444,f[33]);
        // Deliberately inactive sound selector: execute the ORIGINAL mismatch
        // return at FCB32 for both requests. No stub/patch or device emulation.
        // Requests are compared; active sound-driver effects remain out of scope.
        m68k_write_memory_16(0xff0ab6,0);
        for (int reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg) m68k_set_reg(reg,0x5a5a0000u+(unsigned)reg);
        m68k_set_reg(M68K_REG_SR,0x2710);m68k_set_reg(M68K_REG_A5,0xffff0690);m68k_set_reg(M68K_REG_A6,0xffff1ab4);
        horizontal_steps=settle_calls=landings=sound_count=sample_count=0;
        for (unsigned i=0;i<f[34];++i) call(coast_entry ? 0x630a : transition_timer ? 0x1345a : scheduling == 1 ? 0xf76c : scheduling >= 2 ? 0xf8f6 : motion_handlers[handler_id()]);
        if ((m68k_get_reg(NULL,M68K_REG_D2)!=(bonus_calls ? 0 : palette_calls ? 0x5a5a0000u | (((f[82]>>4)&14u)<<2) : 0x5a5a0002u)) || m68k_get_reg(NULL,M68K_REG_A5)!=0xffff0690
            || m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1ab4) fail("actor preserved-register contract failed");
        printf("%u",handler_id());
        for (unsigned i=0;i<6;++i) printf(" %u",actor_word(actor_offsets[i]));
        printf(" %u",m68k_read_memory_8(0xff1ab4));
        for (unsigned i=0;i<3;++i) printf(" %u",actor_word(6+i*2));
        printf(" %u %u %u %u %u %u %u %u %u %u %u %u",m68k_read_memory_8(0xff1ac0),m68k_read_memory_8(0xff1ac1),
            actor_word(0xe),actor_word(0x10),callback_id(),m68k_read_memory_16(0xff4442),m68k_read_memory_16(0xff4444),
            horizontal_steps,settle_calls,landings,sound_count,f[34]);
        for (unsigned i=0;i<sound_count;++i) for (unsigned j=0;j<4;++j) printf(" %u",sound_requests[i][j]);
        if (reversal) {
            printf(" %u",spawn_count);
            for (unsigned i=0;i<spawn_count;++i) {
                unsigned a=spawned[i], h=m68k_read_memory_32(a+0x16);
                if (h!=0xa87c && h!=0xaa40) fail("unknown effect handler");
                if (m68k_read_memory_32(a+0x22)!=0xffff1ab4 || m68k_read_memory_32(a+0x1a)!=0xfaa4
                    || m68k_read_memory_32(a+0x46)!=0x12646 || m68k_read_memory_16(a+0x14)!=0)
                    fail("effect service fields differ");
                unsigned allowed[78]={0};
                allowed[0]=1;
                for (unsigned j=2;j<16;++j) allowed[j]=1;
                for (unsigned j=18;j<30;++j) allowed[j]=1;
                for (unsigned j=34;j<38;++j) allowed[j]=1;
                for (unsigned j=70;j<74;++j) allowed[j]=1;
                for (unsigned j=0;j<78;++j) if (!allowed[j] && ram[(a+j)&65535]!=0xa5)
                    fail("uncontracted effect write");
                printf(" 1 %u %u %u %u %u",h==0xaa40,m68k_read_memory_16(a+2),m68k_read_memory_16(a+4),
                    m68k_read_memory_16(a+0x12),m68k_read_memory_8(a));
                for (unsigned j=6;j<12;j+=2) printf(" %u",m68k_read_memory_16(a+j));
                printf(" %u %u %u",m68k_read_memory_8(a+12),m68k_read_memory_8(a+13),m68k_read_memory_16(a+14));
            }
            if (m68k_read_memory_32(0xff311c)!=(empty_pool ? 0xffff300c : 0xffff304c)-4*spawn_count) fail("allocator stack effect differs");
        }
        if (actions) {
            printf(" %u %u %u",m68k_read_memory_16(0xff33e0),m68k_read_memory_16(0xff33d8),m68k_read_memory_16(0xff33da));
            for (unsigned i=0;i<4;++i) printf(" %u",m68k_read_memory_16(0xff0ad6+2*i));
            printf(" %u",sample_count);
            for (unsigned i=0;i<sample_count;++i) for (unsigned j=0;j<3;++j) printf(" %u",sample_requests[i][j]);
        }
        if (dispatch) printf(" %u %u %u %u",m68k_read_memory_32(0xff1afa)==0x12646,
            m68k_read_memory_16(0xff0836),m68k_read_memory_16(0xff06d2),m68k_read_memory_16(0xff06d4));
        if (transition) {
            for (unsigned i=0;i<4;++i) printf(" %u",m68k_read_memory_16(0xff0b90+2*i));
            for (unsigned i=0;i<3;++i) {
                unsigned curve=m68k_read_memory_32(0xff0b98+4*i);
                if (curve!=0xcafe && curve!=0x1356a && curve!=0x135aa && curve!=0x135ea) fail("unknown transition curve");
                printf(" %u",curve==0xcafe ? 0 : curve==0x1356a ? 1 : curve==0x135aa ? 2 : 3);
            }
            printf(" %u %u %u %u %u %u",m68k_read_memory_16(0xff0edc),m68k_read_memory_16(0xff0ede),
                m68k_read_memory_16(0xff4446),m68k_read_memory_16(0xff4448),m68k_read_memory_16(0xff0732),m68k_read_memory_16(0xff0734));
        }
        if (tally) printf(" %u %u %u %u %u %u",m68k_read_memory_16(0xff33ce),m68k_read_memory_16(0xff0714),m68k_read_memory_16(0xff0f0e),m68k_read_memory_16(0xff340a),m68k_read_memory_16(0xff3402),m68k_read_memory_16(0xff0104));
        if (palette) {
            for (unsigned i=0;i<16;++i) printf(" %u",m68k_read_memory_16(0xff0ea8+2*i));
            for (unsigned i=0;i<48;++i) printf(" %u",m68k_read_memory_8(0xff0dc8+i));
        }
        if (exit_tally) printf(" %u %u %u %u %u",m68k_read_memory_16(0xff0efe),m68k_read_memory_16(0xff070e),m68k_read_memory_16(0xff070c),m68k_read_memory_16(0xff33c8),m68k_read_memory_16(0xff33cc));
        if (score) printf(" %u %u %u %u %u %u",m68k_read_memory_32(0xff06fe),m68k_read_memory_32(0xff0702),m68k_read_memory_32(0xff06c2),m68k_read_memory_16(0xff0706),m68k_read_memory_32(0xff443e),score_advances);
        if (bonus) {
            printf(" %u %u",m68k_read_memory_16(0xff082e),m68k_read_memory_16(0xff0830));
            for (unsigned i=0;i<11;++i) printf(" %u",m68k_read_memory_16(0xff0802+2*i));
            for (unsigned i=0;i<11;++i) printf(" %u",m68k_read_memory_16(0xff0818+2*i));
            printf(" %u %u",bonus_probes,bonus_count);
            for (unsigned i=0;i<bonus_count;++i) printf(" %u %u",bonus_slots[i],bonus_values[i]);
        }
        putchar('\n');
    }
    if (ferror(stdin)) fail("actor transport failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void effect_cases(void) {
    unsigned f[16],cases=0;
    for (;;) {
        int first=scanf("%u",&f[0]); if (first==EOF) break;
        if (first!=1) fail("effect transport failure");
        for (unsigned i=1;i<16;++i) if (scanf("%u",&f[i])!=1) fail("incomplete effect case");
        if (++cases>1000000 || f[0]!=1 || f[12]!=1 || f[1]>1 || !f[15] || f[15]>256) fail("invalid effect case");
        for (unsigned i=0;i<15;++i)
            if (f[i]>65535 || ((i==5 || i==9 || i==10) && f[i]>255)) fail("invalid effect field");
        memset(ram+0x1ab4,0xa5,78);
        m68k_write_memory_8(0xff1ab4,f[5]);
        m68k_write_memory_16(0xff1ab6,f[2]);m68k_write_memory_16(0xff1ab8,f[3]);
        m68k_write_memory_16(0xff1ac6,f[4]);
        for (unsigned i=0;i<3;++i) m68k_write_memory_16(0xff1aba+2*i,f[6+i]);
        m68k_write_memory_8(0xff1ac0,f[9]);m68k_write_memory_8(0xff1ac1,f[10]);m68k_write_memory_16(0xff1ac2,f[11]);
        m68k_write_memory_32(0xff1aca,f[1] ? 0xaa40 : 0xa87c);m68k_write_memory_32(0xff1ace,0xfaa4);
        m68k_write_memory_32(0xff1ad6,0xffff0690);
        m68k_write_memory_16(0xff0692,f[13]);m68k_write_memory_16(0xff0694,f[14]);
        m68k_write_memory_32(0xff311c,0xffff300c);m68k_write_memory_32(0xff300c,0x12345678);
        m68k_set_reg(M68K_REG_SR,0x2710);m68k_set_reg(M68K_REG_A5,0xffff0690);m68k_set_reg(M68K_REG_A6,0xffff1ab4);
        releases=0;
        for (unsigned i=0;i<f[15];++i) call(f[1] ? 0x69aa : 0x80a);
        if (releases>1 || m68k_read_memory_32(0xff311c)!=0xffff300c+4*releases
            || m68k_read_memory_32(0xff300c)!=(releases ? 0xffff1ab4 : 0x12345678)) fail("effect release stack differs");
        printf("1 %u %u %u %u %u",f[1],actor_word(2),actor_word(4),actor_word(18),m68k_read_memory_8(0xff1ab4));
        for (unsigned i=6;i<12;i+=2) printf(" %u",actor_word(i));
        printf(" %u %u %u %u %u\n",m68k_read_memory_8(0xff1ac0),m68k_read_memory_8(0xff1ac1),actor_word(14),releases,f[15]);
    }
    if (ferror(stdin)) fail("effect input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void banner_cases(void) {
    unsigned f[5],cases=0;int fields;
    while ((fields=scanf("%u %u %u %u %u",f,f+1,f+2,f+3,f+4))==5) {
        if (++cases>1000000 || f[0]>3 || f[1]>65535 || f[2]>65535 || f[3]>65535 || f[4]>65535) fail("invalid banner case");
        m68k_write_memory_16(0xff13e2,f[0]);m68k_write_memory_16(0xff33c4,f[1]);
        m68k_write_memory_16(0xff4442,f[3]);m68k_write_memory_16(0xff4444,f[4]);
        m68k_write_memory_16(0xff010c,0xa55a);m68k_write_memory_16(0xff1452,0x2100);
        for (int reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg) m68k_set_reg(reg,0x5a5a0000u+(unsigned)reg);
        m68k_set_reg(M68K_REG_D1,0xabab0000u|f[2]);m68k_set_reg(M68K_REG_SR,0x271f);
        memset(banner_request,0,sizeof banner_request);banner_texts=banner_numbers=banner_device_writes=0;
        call(0x63e2);
        if (banner_texts!=1 || banner_device_writes!=(26+2*banner_numbers)*5 || m68k_read_memory_16(0xff010c)!=0xa55a)
            fail("banner callee effects differ");
        for (int reg=M68K_REG_D2;reg<=M68K_REG_A6;++reg)
            if (reg!=M68K_REG_A0 && reg!=M68K_REG_A1 && m68k_get_reg(NULL,reg)!=0x5a5a0000u+(unsigned)reg) fail("banner retained register differs");
        printf("%u %u",m68k_read_memory_16(0xff4442),m68k_read_memory_16(0xff4444));
        for (unsigned i=0;i<5;++i) printf(" %u",banner_request[i]);puts("");
    }
    if (fields!=EOF || ferror(stdin)) fail("banner transport failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void pad_cases(void) {
    unsigned raw,cases=0;int fields;
    while ((fields=scanf("%u",&raw))==1) {
        if (raw>255 || ++cases>1000000) fail("invalid raw pad byte");
        for (unsigned poison=0;poison<4;++poison) {
            unsigned char before[48];
            memset(ram+0x690,(int)(poison*85),48);ram[0x6a4]=(unsigned char)raw;
            memcpy(before,ram+0x690,48);
            for (int reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg) m68k_set_reg(reg,0x5a5a0000u+(unsigned)reg);
            m68k_set_reg(M68K_REG_SR,0x2700|poison*5);m68k_set_reg(M68K_REG_A5,0xffff0690);
            call(0x14e4e);
            for (int reg=M68K_REG_D1;reg<=M68K_REG_A6;++reg)
                if (m68k_get_reg(NULL,reg)!=(reg==M68K_REG_A5 ? 0xffff0690 : 0x5a5a0000u+(unsigned)reg)) fail("pad register preservation differs");
            for (unsigned i=0;i<48;++i)
                if (!(i>=0x15 && i<0x18) && !(i>=0x1a && i<0x22) && ram[0x690+i]!=before[i]) fail("pad unmodeled byte changed");
            // Four independent initial fill/CCR states; one result row each.
            const unsigned offsets[]={0x14,0x15,0x16,0x17,0x1a,0x1b,0x1c,0x1d,0x1e,0x1f,0x20,0x21};
            for (unsigned i=0;i<12;++i) printf("%u%s",ram[0x690+offsets[i]],i==11 ? "\n" : " ");
        }
    }
    if (fields!=EOF || ferror(stdin)) fail("pad transport failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases*4,total_instructions);
}
static void trail_particle_print(unsigned a) {
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14};
    for(unsigned i=0;i<10;++i) printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(a+offsets[i]) : m68k_read_memory_16(a+offsets[i]));
}
static void trail_cases(void) {
    unsigned f[29],cases=0;int first;
    const unsigned n=trail_mode==3 ? 11 : (trail_mode==4 || trail_mode==5) ? 3 : 29;
    while ((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000) fail("trail case budget/transport failure");
        for(unsigned i=1;i<n;++i) if(scanf("%u",&f[i])!=1) fail("incomplete trail case");
        const unsigned repeats=trail_mode==5 ? 1 : f[n-1];
        if(!repeats || repeats>32) fail("trail repetition budget exhausted");
        memset(ram,0xa5,sizeof ram);spawn_count=releases=0;
        m68k_write_memory_32(0xff3008,0);
        unsigned capacity=trail_mode==5 ? f[2] : n==29 ? f[25] : 0;
        if(capacity>16) fail("trail allocation budget outside range");
        for(unsigned i=0;i<capacity;++i)m68k_write_memory_32(0xff300c+4*i,0xffff2000+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*capacity);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A6,0xffff1ab4);m68k_set_reg(M68K_REG_A5,0xffff0690);m68k_set_reg(M68K_REG_SR,0x2700);
        if(trail_mode==4) {
            m68k_write_memory_32(0xff0bac,f[0]);m68k_write_memory_32(0xff0bb0,f[1]);
            for(unsigned i=0;i<repeats;++i)call(0xe918);
            printf("%u %u %u",m68k_read_memory_32(0xff0bac),m68k_read_memory_32(0xff0bb0),m68k_get_reg(NULL,M68K_REG_D0));
        } else if(trail_mode==5) {
            if(f[0]>65535 || f[1]>65535 || f[2]>1)fail("invalid trail spawn input");
            m68k_set_reg(M68K_REG_D0,f[0]);m68k_set_reg(M68K_REG_D1,f[1]);call(0x5a9a);trail_particle_print(spawned[0]);
        } else if(trail_mode==3) {
            const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14};
            for(unsigned i=0;i<10;++i) {
                const int byte=i==3 || i==7 || i==8;
                if(f[i]>(byte ? 255u : 65535u))fail("trail particle field outside range");
                if(byte)m68k_write_memory_8(0xff1ab4+offsets[i],f[i]);else m68k_write_memory_16(0xff1ab4+offsets[i],f[i]);
            }
            m68k_write_memory_32(0xff1ab4+0x16,0x5ae2);m68k_write_memory_32(0xff1ab4+0x1a,0xfaa4);m68k_write_memory_32(0xff1ab4+0x46,0x12646);
            for(unsigned i=0;i<repeats;++i)call(0x69aa);
            if(releases>1 || m68k_read_memory_32(0xff311c)!=0xffff300c+4*releases) fail("trail release differs");
            trail_particle_print(0xff1ab4);printf(" %u",releases);
        } else {
            const unsigned offsets[]={2,4,0x36,0x22,0x24,0x26,0x28,0x2a,0x2c,0x2e,0x30,0x32,0x34,0,6,8,10,12,13,14,18};
            for(unsigned i=0;i<21;++i) {
                const int byte=i==13 || i==17 || i==18;
                if(f[i]>(byte ? 255u : 65535u))fail("trail emitter field outside range");
                if(byte)m68k_write_memory_8(0xff1ab4+offsets[i],f[i]);else m68k_write_memory_16(0xff1ab4+offsets[i],f[i]);
            }
            if(f[23]>65535 || f[24]>65535)fail("trail owner word outside range");
            m68k_write_memory_32(0xff1ab4+0x16,0x6d8c);m68k_write_memory_32(0xff1ab4+0x1a,0xcafe);m68k_write_memory_32(0xff1ab4+0x46,0x12646);m68k_write_memory_32(0xff1ab4+0x4a,0xffff0690);
            m68k_write_memory_32(0xff0690,f[21] && f[21]==f[22] ? 0xffff2800 : 0xffff2900);
            m68k_write_memory_16(0xff2802,f[23]);m68k_write_memory_16(0xff2804,f[24]);
            m68k_write_memory_32(0xff0bac,f[26]);m68k_write_memory_32(0xff0bb0,f[27]);
            unsigned char before[78];memcpy(before,ram+0x1ab4,78);
            for(unsigned i=0;i<repeats;++i)call(trail_mode==2 ? 0x69aa : 0x6d8c);
            for(unsigned i=0;i<78;++i) if(!(i==0 || (i>=2 && i<16) || (i>=0x22 && i<0x38)) && before[i]!=ram[0x1ab4+i])fail("uncontracted trail emitter write");
            if(m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1ab4 || m68k_get_reg(NULL,M68K_REG_A5)!=0xffff0690)fail("trail owner register changed");
            for(unsigned i=0;i<21;++i)printf("%s%u",i ? " " : "",(i==13 || i==17 || i==18) ? m68k_read_memory_8(0xff1ab4+offsets[i]) : m68k_read_memory_16(0xff1ab4+offsets[i]));
            if(m68k_read_memory_32(0xff311c)!=0xffff300c+4*(capacity-spawn_count))fail("trail allocation count differs");
            printf(" %u %u %u %u %u",f[21],m68k_read_memory_32(0xff0bac),m68k_read_memory_32(0xff0bb0),capacity-spawn_count,spawn_count);
            for(unsigned i=0;i<spawn_count;++i) {
                const unsigned a=spawned[i];
                if(m68k_read_memory_32(a+0x16)!=0x5ae2 || m68k_read_memory_32(a+0x1a)!=0xfaa4 || m68k_read_memory_32(a+0x46)!=0x12646 || m68k_read_memory_16(a+0x14)!=0)fail("trail spawned handlers differ");
                trail_particle_print(a);
            }
        }
        puts("");
    }
    if(ferror(stdin))fail("trail input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void private_cases(void) {
    unsigned f[17],cases=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("private case budget/transport failure");
        for(unsigned i=1;i<17;++i)if(scanf("%u",&f[i])!=1)fail("incomplete private case");
        if(f[0]>1 || !f[16] || f[16]>256 || f[14]>65535 || f[15]>65535)fail("invalid private case");
        memset(ram,0xa5,sizeof ram);
        for(unsigned i=0;i<11;++i) {
            const int byte=i==3 || i==7 || i==8;
            if(f[i+1]>(byte ? 255u : 65535u))fail("private field outside range");
            if(byte)m68k_write_memory_8(0xff1ab4+offsets[i],f[i+1]);else m68k_write_memory_16(0xff1ab4+offsets[i],f[i+1]);
        }
        const unsigned handler=f[0] ? 0x7ca4 : 0x7808;
        m68k_write_memory_32(0xff1ab4+0x4a,f[12]); // Opaque link; never dereferenced.
        m68k_write_memory_32(0xff1ab4+0x16,handler);
        m68k_write_memory_32(0xff1ab4+0x1a,0xcafe); // Unknown invoked callback must reject.
        m68k_write_memory_32(0xff1ab4+0x46,0x12646);
        m68k_write_memory_32(0xff31b0,f[13]);m68k_write_memory_16(0xff31a6,f[14]);m68k_write_memory_16(0xff31a4,f[15]);
        unsigned char before[78];memcpy(before,ram+0x1ab4,78);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A6,0xffff1ab4);m68k_set_reg(M68K_REG_SR,0x2700);
        for(unsigned i=0;i<f[16];++i)call(private_mode==2 ? 0x69aa : handler);
        if(m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1ab4)fail("private object register changed");
        const int invoked=private_mode==1 || (f[4]&128);
        if(m68k_get_reg(NULL,M68K_REG_A5)!=(invoked && !f[0] ? f[12] : 0x5a5a0000u+M68K_REG_A5))fail("private link register differs");
        for(unsigned i=0;i<78;++i) {
            const int presentation=private_mode==2 && (i==0 || i==6 || i==7 || i==12);
            const int effect=!f[0] ? (i==4 || i==5 || i==16 || i==17) : (i==2 || i==3 || i==4 || i==5 || i==18 || i==19);
            if(!presentation && !effect && ram[0x1ab4+i]!=before[i])fail("private uncontracted object field changed");
        }
        printf("5 %u",f[0]);
        for(unsigned i=0;i<11;++i)printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(0xff1ab4+offsets[i]) : m68k_read_memory_16(0xff1ab4+offsets[i]));
        printf(" %u\n",m68k_read_memory_32(0xff1ab4+0x4a));
    }
    if(ferror(stdin))fail("private input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void table_cases(void) {
    unsigned f[18],cases=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("table case budget/transport failure");
        for(unsigned i=1;i<18;++i)if(scanf("%u",&f[i])!=1)fail("incomplete table case");
        if(!f[16] || f[16]>256 || f[13]>65535 || f[14]>65535 || f[15]>65535 || f[17]>65536
            || ((uint64_t)f[15]+1)*f[16]>1048576)fail("invalid table case");
        memset(ram,0xa5,sizeof ram);
        for(unsigned i=0;i<11;++i) {
            const int byte=i==3 || i==7 || i==8;
            if(f[i]>(byte ? 255u : 65535u))fail("table field outside range");
            if(byte)m68k_write_memory_8(0xff1ab4+offsets[i],f[i]);else m68k_write_memory_16(0xff1ab4+offsets[i],f[i]);
        }
        m68k_write_memory_32(0xff1ab4+0x4a,f[11]);
        m68k_write_memory_32(0xff1ab4+0x16,0x7a88);
        m68k_write_memory_32(0xff1ab4+0x1a,0x79b6); // Real unsupported callback boundary.
        m68k_write_memory_32(0xff1ab4+0x46,0x12646);
        m68k_write_memory_32(0xff1ab4+0x2e,0x7a58+2*f[12]);
        m68k_write_memory_16(0xff1ab4+0x32,f[13]);m68k_write_memory_16(0xff1ab4+0x36,f[14]);
        m68k_write_memory_16(0xff31bc,f[15]);table_budget=f[17];
        unsigned char before[78];memcpy(before,ram+0x1ab4,78);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A6,0xffff1ab4);m68k_set_reg(M68K_REG_SR,0x2700);
        for(unsigned i=0;i<f[16];++i)call(table_mode==2 ? 0x69aa : 0x7a88);
        if(m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1ab4 || m68k_read_memory_16(0xff31bc)!=f[15])fail("table input register/global changed");
        const int invoked=table_mode==1 || (f[3]&128);
        if(m68k_get_reg(NULL,M68K_REG_A5)!=(invoked ? f[11] : 0x5a5a0000u+M68K_REG_A5))fail("table link register differs");
        for(unsigned i=0;i<78;++i) {
            const int presentation=table_mode==2 && (i==0 || i==6 || i==7 || i==12);
            const int effect=(i>=2 && i<6) || i==16 || i==17 || (i>=46 && i<52) || i==54 || i==55;
            if(!presentation && !effect && ram[0x1ab4+i]!=before[i])fail("table uncontracted object field changed");
        }
        printf("6");
        for(unsigned i=0;i<11;++i)printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(0xff1ab4+offsets[i]) : m68k_read_memory_16(0xff1ab4+offsets[i]));
        printf(" %u %u %u %u\n",m68k_read_memory_32(0xff1ab4+0x4a),(m68k_read_memory_32(0xff1ab4+0x2e)-0x7a58)/2,actor_word(0x32),actor_word(0x36));
    }
    if(ferror(stdin))fail("table input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void table_writer_cases(void) {
    unsigned kind,rise,count,timer,cases=0;int fields;
    while((fields=scanf("%u %u %u %u",&kind,&rise,&count,&timer))==4) {
        if(++cases>1000000 || kind>1 || count>65535 || timer>65535)fail("invalid table writer case");
        memset(ram,0xa5,sizeof ram);m68k_write_memory_32(0xff31b0,rise);
        m68k_write_memory_16(0xff31bc,count);m68k_write_memory_16(0xff31be,timer);
        m68k_set_reg(M68K_REG_SR,0x2700);call(kind ? 0x7cc8 : 0x7a46);
        if(m68k_read_memory_32(0xff31b0)!=rise)fail("table writer changed rise input");
        printf("%u %u\n",m68k_read_memory_16(0xff31bc),m68k_read_memory_16(0xff31be));
    }
    if(fields!=EOF || ferror(stdin))fail("table writer transport failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void collision_cases(void) {
    unsigned f[22],cases=0;int first;const unsigned fields=collision_mode==1 ? 7 : 22;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid collision case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete collision case");
        memset(ram,0xa5,sizeof ram);
        if(collision_mode==1) {
            for(unsigned i=0;i<7;++i)if(f[i]>65535)fail("invalid overlap word");
            m68k_write_memory_16(0xff1ab6,f[0]);m68k_write_memory_16(0xff1ab8,f[1]);
            m68k_write_memory_16(0xff1ad2,f[2]);m68k_write_memory_16(0xff1ad4,f[3]);
            m68k_write_memory_16(0xff06d2,f[4]);m68k_write_memory_16(0xff06d4,f[5]);m68k_write_memory_16(0xff13ae,f[6]);
        } else {
            for(unsigned i=0;i<11;++i) {
                const int byte=i==3 || i==7 || i==8;
                if(f[i]>(byte ? 255u : 65535u))fail("collision field outside range");
                if(byte)m68k_write_memory_8(0xff1ab4+offsets[i],f[i]);else m68k_write_memory_16(0xff1ab4+offsets[i],f[i]);
            }
            for(unsigned i=12;i<=20;++i)if(f[i]>65535)fail("collision context word outside range");
            if(f[18]>1 || !f[21] || f[21]>256 || (!f[18] && (f[19] || f[20])))fail("invalid collision context/repetition");
            m68k_write_memory_32(0xff1ab4+0x4a,f[11]);m68k_write_memory_32(0xff1ab4+0x16,0x12646);
            m68k_write_memory_32(0xff1ab4+0x1a,0);m68k_write_memory_32(0xff1ab4+0x46,collision_mode>=4 ? 0x6bd6 : 0x78ee);
            if(collision_mode>=4)m68k_write_memory_32(0xff1ab4+0x42,0xffff447a); // A 6AF0 pickup on record 0.
            m68k_write_memory_16(0xff1ad2,f[12]);m68k_write_memory_16(0xff1ad4,f[13]);
            m68k_write_memory_16(0xff06d2,f[14]);m68k_write_memory_16(0xff06d4,f[15]);m68k_write_memory_16(0xff13ae,f[16]);
            m68k_write_memory_16(0xff33e2,f[17]);collision_secondary=f[18];
            m68k_write_memory_16(0xff087a,f[19]);m68k_write_memory_16(0xff087c,f[20]);
        }
        unsigned char before[78];memcpy(before,ram+0x1ab4,78);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A6,0xffff1ab4);m68k_set_reg(M68K_REG_A5,0xffff0690);m68k_set_reg(M68K_REG_SR,0x2700);
        for(unsigned i=0;i<(collision_mode==1 ? 1 : f[21]);++i)call(collision_mode==1 ? 0xac5e : collision_mode==2 ? 0x78ee : collision_mode==4 ? 0x6bd6 : 0x69aa);
        if(m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1ab4)fail("collision object identity changed");
        for(unsigned i=0;i<78;++i)if(!((collision_mode==3 || collision_mode==5) && (i==0 || i==6 || i==7 || i==12)) && ram[0x1ab4+i]!=before[i])fail("collision mutated object");
        if(collision_mode==1) {
            unsigned result=m68k_get_reg(NULL,M68K_REG_D0)&65535;
            if((result!=0 && result!=65535) || !!(m68k_get_reg(NULL,M68K_REG_SR)&4)!=(result==0))fail("overlap result/flags differ");
            printf("%u\n",result!=0);
        } else {
            unsigned a5=(collision_mode==2 || collision_mode==4 || (f[3]&128)) && f[17] ? 0xffff0838 : 0xffff0690;
            if(m68k_get_reg(NULL,M68K_REG_A5)!=a5)fail("collision short-circuit control differs");
            printf(collision_mode>=4 ? "9" : "7");
            for(unsigned i=0;i<11;++i)printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(0xff1ab4+offsets[i]) : m68k_read_memory_16(0xff1ab4+offsets[i]));
            printf(" %u %u %u",m68k_read_memory_32(0xff1ab4+0x4a),actor_word(0x1e),actor_word(0x20));
            if(collision_mode>=4)printf(" %u",(m68k_read_memory_32(0xff1ab4+0x42)-0xffff447a)/12);
            puts("");
        }
    }
    if(ferror(stdin))fail("collision input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"queries\":%u,\"visited\":[",cases,total_instructions,collision_queries);
}
static void return_only_cases(void) {
    unsigned f[13],cases=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid return-only case");
        for(unsigned i=1;i<13;++i)if(scanf("%u",&f[i])!=1)fail("incomplete return-only case");
        if(!f[12] || f[12]>256)fail("return-only repetition budget exhausted");
        memset(ram,0xa5,sizeof ram);
        for(unsigned i=0;i<11;++i) {
            const int byte=i==3 || i==7 || i==8;
            if(f[i]>(byte ? 255u : 65535u))fail("return-only field outside range");
            if(byte)m68k_write_memory_8(0xff1ab4+offsets[i],f[i]);else m68k_write_memory_16(0xff1ab4+offsets[i],f[i]);
        }
        m68k_write_memory_32(0xff1ab4+0x4a,f[11]);m68k_write_memory_32(0xff1ab4+0x16,0x12646);
        m68k_write_memory_32(0xff1ab4+0x1a,0);m68k_write_memory_32(0xff1ab4+0x46,0x12646);
        unsigned char before[78];memcpy(before,ram+0x1ab4,78);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A6,0xffff1ab4);m68k_set_reg(M68K_REG_A5,0x12345678);m68k_set_reg(M68K_REG_SR,0x2700);
        const unsigned presented=return_only_presentations,returned=return_only_returns;
        for(unsigned i=0;i<f[12];++i)call(0x69aa);
        if(m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1ab4 || m68k_get_reg(NULL,M68K_REG_A5)!=0x12345678)fail("return-only identity changed");
        const unsigned active=(f[3]&128) ? f[12] : 0;
        if(return_only_presentations-presented!=active || return_only_returns-returned!=2*active)fail("return-only dispatch cadence differs");
        for(unsigned i=0;i<78;++i)if((!active || !(i==0 || i==6 || i==7 || i==12)) && ram[0x1ab4+i]!=before[i])fail("return-only changed uncontracted field");
        printf("8");
        for(unsigned i=0;i<11;++i)printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(0xff1ab4+offsets[i]) : m68k_read_memory_16(0xff1ab4+offsets[i]));
        printf(" %u\n",m68k_read_memory_32(0xff1ab4+0x4a));
    }
    if(ferror(stdin))fail("return-only input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"presentations\":%u,\"returns\":%u,\"visited\":[",cases,total_instructions,return_only_presentations,return_only_returns);
}
static void pair_print(unsigned a) {
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    for(unsigned i=0;i<11;++i)printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(a+offsets[i]) : m68k_read_memory_16(a+offsets[i]));
    printf(" %u",m68k_read_memory_32(a+0x4a));
}
static int pair_written(unsigned offset) {
    // F9E2: +00 +06 +12 +14 +16 +46. 7B9C/7C26: +00 +02 +04 +06 +08 +0A +0C +0D +16
    // (+12 on 7B9C's second member, already within F9E2's set). 7772 also
    // writes countdown +10 and the control link +4A.
    return offset==0 || (offset>=2 && offset<14) || (offset>=0x12 && offset<0x1a) || (offset>=0x46 && offset<0x4a)
        || (pair_mode==3 && ((offset>=0x10 && offset<0x12) || (offset>=0x4a && offset<0x4e)));
}
static void pair_cases(void) {
    unsigned f[17],cases=0,cycles=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid pair case");
        for(unsigned i=1;i<17;++i)if(scanf("%u",&f[i])!=1)fail("incomplete pair case");
        if(f[0]>68 || f[1]>=68 || f[2]>=68 || f[1]==f[2] || f[4]>255)fail("pair stack outside range");
        for(unsigned j=5;j<17;j+=6)if(f[j]>255 || f[j+1]>65535 || f[j+2]>65535 || f[j+5]>255)fail("pair residue outside range");
        memset(ram,0xa5,sizeof ram);memset(ram+0x1b50,f[4],0x3008-0x1b50);
        unsigned stack[68],n=0;
        for(unsigned i=0;i<68 && n+2<f[0];++i)if(i!=f[1] && i!=f[2])stack[n++]=i;
        if(f[0]>=2)stack[n++]=f[2];
        if(f[0]>=1)stack[n++]=f[1];
        m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<n;++i)m68k_write_memory_32(0xff300c+4*i,0xffff1b50+78*stack[i]);
        m68k_write_memory_32(0xff311c,0xffff300c+4*n);m68k_write_memory_32(0xff31c0,0x13572468);
        for(unsigned j=0;j<2;++j) {
            const unsigned a=0xff1b50+78*f[1+j],*r=f+5+6*j;
            m68k_write_memory_8(a+1,r[0]);m68k_write_memory_16(a+0x0e,r[1]);m68k_write_memory_16(a+0x10,r[2]);
            m68k_write_memory_32(a+0x4a,r[3]);m68k_write_memory_32(a+0x1a,r[4]);
            for(unsigned o=0x1e;o<0x46;++o)m68k_write_memory_8(a+o,r[5]);
        }
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        // f[3] is the consumed caller register: A6 for 7B9C/7C26, A5 for 7772.
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(pair_mode==3 ? M68K_REG_A5 : M68K_REG_A6,f[3]);m68k_set_reg(M68K_REG_SR,0x2700);
        pair_pops=pair_exhausted=0;call(pair_mode==1 ? 0x7b9c : pair_mode==2 ? 0x7c26 : 0x7772);++cycles;
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A5;++reg) {
            if(reg==M68K_REG_A0 || (pair_mode==3 && reg==M68K_REG_A4 && pair_pops))continue;
            if(m68k_get_reg(NULL,reg)!=(pair_mode==3 && reg==M68K_REG_A5 ? f[3] : 0x5a5a0000u+reg))fail("pair changed preserved register");
        }
        if(pair_mode==3 && pair_pops && m68k_get_reg(NULL,M68K_REG_A4)!=0xffff1b50+78*f[1])fail("rising pair A4 differs");
        const unsigned popped=pair_exhausted ? pair_pops : 2;
        if(pair_pops!=popped || popped>n || (pair_exhausted && popped!=(n<2 ? n : 2)) || (!pair_exhausted && n<2))fail("pair allocation count differs");
        if(m68k_read_memory_32(0xff311c)!=0xffff300c+4*(n-popped))fail("pair free head differs"); // Failing test leaves the head.
        if(pair_exhausted ? m68k_get_reg(NULL,M68K_REG_A0)!=0xffff3008 : m68k_get_reg(NULL,M68K_REG_A0)!=0x5a5a0000u+M68K_REG_A0)fail("pair A0 differs");
        const unsigned anchor=m68k_read_memory_32(0xff31c0);
        if(!pair_exhausted && m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1b50+78*f[2])fail("pair A6 differs");
        if(pair_mode==1 && !pair_exhausted ? anchor!=0xffff1b50+78*f[2] : anchor!=0x13572468)fail("pair anchor differs");
        for(unsigned a=0;a<65536;++a) {
            const unsigned o=(a-0x1b50)%78,i=(a-0x1b50)/78;
            const int slot=a>=0x1b50 && a<0x3008 && ((popped>0 && i==f[1]) || (popped>1 && i==f[2])) && pair_written(o);
            const int allowed=slot || (a>=0xef00 && a<0xf004) || (a>=0x311c && a<0x3120) || (a>=0x31c0 && a<0x31c4);
            if(!allowed && ram[a]!=before[a])fail("pair changed uncontracted byte");
        }
        if(pair_exhausted)printf("0 %u\n",popped);
        else {
            printf("1 %u %u",f[1],f[2]);
            if(pair_mode==1)printf(" %u",(anchor-0xffff1b50)/78);
            printf(" %u",(m68k_read_memory_32(0xff311c)-0xffff300c)/4);pair_print(0xff1b50+78*f[1]);pair_print(0xff1b50+78*f[2]);puts("");
        }
    }
    if(ferror(stdin))fail("pair input failure");
    fprintf(stderr,"{\"cases\":%u,\"calls\":%u,\"instructions\":%u,\"visited\":[",cases,cycles,total_instructions);
}
static int quad_written(unsigned member,unsigned offset) {
    // F9E2: +00 +06 +12..+19 +46..+49. 783A: +00 +02..+07 on every member;
    // the probe also +16..+19, extents +1E..+21, service +46..+49 and link +4A..+4D.
    return offset==0 || (offset>=2 && offset<8) || (offset>=0x12 && offset<0x1a) || (offset>=0x46 && offset<0x4a)
        || (!member && ((offset>=0x1e && offset<0x22) || (offset>=0x4a && offset<0x4e)));
}
static void quad_cases(void) {
    unsigned f[47],cases=0,cycles=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid collision quad case");
        for(unsigned i=1;i<47;++i)if(scanf("%u",&f[i])!=1)fail("incomplete collision quad case");
        if(f[0]>68 || f[6]>255)fail("collision quad stack outside range");
        for(unsigned m=0;m<4;++m) {
            const unsigned *r=f+7+10*m;
            if(f[1+m]>=68)fail("collision quad slot outside range");
            for(unsigned k=0;k<m;++k)if(f[1+m]==f[1+k])fail("collision quad slots repeat");
            if(r[0]>255 || r[1]>65535 || r[2]>65535 || r[5]>255 || r[6]>65535 || r[7]>65535 || r[8]>255 || r[9]>255)fail("collision quad residue outside range");
        }
        memset(ram,0xa5,sizeof ram);memset(ram+0x1b50,f[6],0x3008-0x1b50);
        unsigned stack[68],n=0;
        for(unsigned i=0;i<68 && n+4<f[0];++i)if(i!=f[1] && i!=f[2] && i!=f[3] && i!=f[4])stack[n++]=i;
        for(unsigned m=4;m-->0;)if(f[0]>=m+1)stack[n++]=f[1+m];
        m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<n;++i)m68k_write_memory_32(0xff300c+4*i,0xffff1b50+78*stack[i]);
        m68k_write_memory_32(0xff311c,0xffff300c+4*n);m68k_write_memory_32(0xff31c0,0x13572468);
        for(unsigned m=0;m<4;++m) {
            const unsigned a=0xff1b50+78*f[1+m],*r=f+7+10*m;
            m68k_write_memory_8(a+1,r[0]);m68k_write_memory_16(a+0x0e,r[1]);m68k_write_memory_16(a+0x10,r[2]);
            m68k_write_memory_32(a+0x4a,r[3]);m68k_write_memory_32(a+0x1a,r[4]);
            for(unsigned o=0x1e;o<0x46;++o)m68k_write_memory_8(a+o,r[5]);
            m68k_write_memory_16(a+8,r[6]);m68k_write_memory_16(a+10,r[7]);m68k_write_memory_8(a+12,r[8]);m68k_write_memory_8(a+13,r[9]);
        }
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        // f[5] is the caller's A5, stored only in the probe as its control link.
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A5,f[5]);m68k_set_reg(M68K_REG_SR,0x2700);
        pair_pops=pair_exhausted=0;call(0x783a);++cycles;
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A5;++reg) {
            if(reg==M68K_REG_A0 || (reg==M68K_REG_A4 && pair_pops))continue;
            if(m68k_get_reg(NULL,reg)!=(reg==M68K_REG_A5 ? f[5] : 0x5a5a0000u+reg))fail("collision quad changed preserved register");
        }
        if(pair_pops && m68k_get_reg(NULL,M68K_REG_A4)!=0xffff1b50+78*f[1])fail("collision quad A4 differs");
        const unsigned popped=pair_exhausted ? pair_pops : 4;
        if(pair_pops!=popped || popped>n || (pair_exhausted && popped!=(n<4 ? n : 4)) || (!pair_exhausted && n<4))fail("collision quad allocation count differs");
        if(m68k_read_memory_32(0xff311c)!=0xffff300c+4*(n-popped))fail("collision quad free head differs"); // Failing test leaves the head.
        if(pair_exhausted ? m68k_get_reg(NULL,M68K_REG_A0)!=0xffff3008 : m68k_get_reg(NULL,M68K_REG_A0)!=0x5a5a0000u+M68K_REG_A0)fail("collision quad A0 differs");
        if(!pair_exhausted && m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1b50+78*f[4])fail("collision quad A6 differs");
        if(m68k_read_memory_32(0xff31c0)!=0x13572468)fail("collision quad changed FF31C0");
        for(unsigned a=0;a<65536;++a) {
            const unsigned o=(a-0x1b50)%78,i=(a-0x1b50)/78;int slot=0;
            for(unsigned m=0;m<popped;++m)if(a>=0x1b50 && a<0x3008 && i==f[1+m] && quad_written(m,o))slot=1;
            const int allowed=slot || (a>=0xef00 && a<0xf004) || (a>=0x311c && a<0x3120);
            if(!allowed && ram[a]!=before[a])fail("collision quad changed uncontracted byte");
        }
        if(pair_exhausted)printf("0 %u\n",popped);
        else {
            printf("1 %u %u %u %u %u",f[1],f[2],f[3],f[4],(m68k_read_memory_32(0xff311c)-0xffff300c)/4);
            for(unsigned m=0;m<4;++m) {
                const unsigned a=0xff1b50+78*f[1+m];pair_print(a);
                if(!m)printf(" %u %u",m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20));
            }
            puts("");
        }
    }
    if(ferror(stdin))fail("collision quad input failure");
    fprintf(stderr,"{\"cases\":%u,\"calls\":%u,\"instructions\":%u,\"visited\":[",cases,cycles,total_instructions);
}
static int prefix_written(unsigned member,unsigned offset) {
    // 6EC8/6EDC: F9E2's set only (+00 cleared again). 7772: pair set plus +10
    // and +4A. 783A: quad set. 7B9C/7C26: pair set.
    if(member<2)return offset==0 || (offset>=6 && offset<8) || (offset>=0x12 && offset<0x1a) || (offset>=0x46 && offset<0x4a);
    if(member>=4 && member<8)return quad_written(member-4,offset);
    return offset==0 || (offset>=2 && offset<14) || (offset>=0x12 && offset<0x1a) || (offset>=0x46 && offset<0x4a)
        || (member<4 && ((offset>=0x10 && offset<0x12) || (offset>=0x4a && offset<0x4e)));
}
static void prefix_cases(void) {
    enum {members=12,head=14,width=12,fields=head+members*width};
    unsigned f[fields],cases=0,cycles=0;int first;
    const unsigned sentinels[3]={0x11111111,0x22222222,0x13572468},anchors[3]={0xff31b4,0xff31b8,0xff31c0},owners[3]={0,1,9},needed[3]={1,2,10};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid setup prefix case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete setup prefix case");
        if(f[0]>68 || f[1]>255)fail("setup prefix stack outside range");
        for(unsigned m=0;m<members;++m) {
            const unsigned *r=f+head+width*m;
            if(f[2+m]>=68)fail("setup prefix slot outside range");
            for(unsigned k=0;k<m;++k)if(f[2+m]==f[2+k])fail("setup prefix slots repeat");
            if(r[0]>255 || r[1]>65535 || r[2]>65535 || r[5]>255 || r[6]>65535 || r[7]>65535 || r[8]>255 || r[9]>255 || r[10]>65535 || r[11]>65535)fail("setup prefix residue outside range");
        }
        memset(ram,0xa5,sizeof ram);memset(ram+0x1b50,f[1],0x3008-0x1b50);
        unsigned stack[68],n=0;
        for(unsigned i=0;i<68 && n+members<f[0];++i){int member=0;for(unsigned m=0;m<members;++m)member|=i==f[2+m];if(!member)stack[n++]=i;}
        for(unsigned m=members;m-->0;)if(f[0]>=m+1)stack[n++]=f[2+m];
        m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<n;++i)m68k_write_memory_32(0xff300c+4*i,0xffff1b50+78*stack[i]);
        m68k_write_memory_32(0xff311c,0xffff300c+4*n);
        for(unsigned k=0;k<3;++k)m68k_write_memory_32(anchors[k],sentinels[k]);
        for(unsigned m=0;m<members;++m) {
            const unsigned a=0xff1b50+78*f[2+m],*r=f+head+width*m;
            m68k_write_memory_8(a+1,r[0]);m68k_write_memory_16(a+0x0e,r[1]);m68k_write_memory_16(a+0x10,r[2]);
            m68k_write_memory_32(a+0x4a,r[3]);m68k_write_memory_32(a+0x1a,r[4]);
            for(unsigned o=0x1e;o<0x46;++o)m68k_write_memory_8(a+o,r[5]);
            m68k_write_memory_16(a+8,r[6]);m68k_write_memory_16(a+10,r[7]);m68k_write_memory_8(a+12,r[8]);m68k_write_memory_8(a+13,r[9]);
            m68k_write_memory_16(a+2,r[10]);m68k_write_memory_16(a+4,r[11]);
        }
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        pair_pops=pair_exhausted=0;call(0x6886);++cycles;
        // The fragment sets A5 itself; A4 and A6 are left on the probe and the last member.
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A3;++reg) {
            if(reg==M68K_REG_A0)continue;
            if(m68k_get_reg(NULL,reg)!=0x5a5a0000u+reg)fail("setup prefix changed preserved register");
        }
        if(m68k_get_reg(NULL,M68K_REG_A5)!=0xffff0690)fail("setup prefix A5 differs");
        const unsigned popped=pair_exhausted ? pair_pops : members;
        if(pair_pops!=popped || popped>n || (pair_exhausted && popped!=n) || (!pair_exhausted && n<members))fail("setup prefix allocation count differs");
        if(m68k_read_memory_32(0xff311c)!=0xffff300c+4*(n-popped))fail("setup prefix free head differs");
        if(pair_exhausted ? m68k_get_reg(NULL,M68K_REG_A0)!=0xffff3008 : m68k_get_reg(NULL,M68K_REG_A0)!=0x5a5a0000u+M68K_REG_A0)fail("setup prefix A0 differs");
        if(!pair_exhausted && (m68k_get_reg(NULL,M68K_REG_A4)!=0xffff1b50+78*f[6] || m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1b50+78*f[13]))fail("setup prefix A4/A6 differ");
        for(unsigned k=0;k<3;++k)
            if(m68k_read_memory_32(anchors[k])!=(popped>=needed[k] ? 0xffff1b50+78*f[2+owners[k]] : sentinels[k]))fail("setup prefix identity differs");
        for(unsigned a=0;a<65536;++a) {
            const unsigned o=(a-0x1b50)%78,i=(a-0x1b50)/78;int slot=0;
            for(unsigned m=0;m<popped;++m)if(a>=0x1b50 && a<0x3008 && i==f[2+m] && prefix_written(m,o))slot=1;
            const int allowed=slot || (a>=0xef00 && a<0xf004) || (a>=0x311c && a<0x3120) || (a>=0x31b4 && a<0x31bc) || (a>=0x31c0 && a<0x31c4);
            if(!allowed && ram[a]!=before[a]){fprintf(stderr,"case %u address FF%04X popped %u\n",cases,a,popped);fail("setup prefix changed uncontracted byte");}
        }
        if(pair_exhausted)printf("0 %u\n",popped);
        else {
            printf("1");for(unsigned m=0;m<members;++m)printf(" %u",f[2+m]);
            for(unsigned k=0;k<3;++k)printf(" %u",(m68k_read_memory_32(anchors[k])-0xffff1b50)/78);
            printf(" %u",(m68k_read_memory_32(0xff311c)-0xffff300c)/4);
            for(unsigned m=0;m<members;++m) {
                const unsigned a=0xff1b50+78*f[2+m];pair_print(a);
                if(m==4)printf(" %u %u",m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20));
            }
            puts("");
        }
    }
    if(ferror(stdin))fail("setup prefix input failure");
    fprintf(stderr,"{\"cases\":%u,\"calls\":%u,\"instructions\":%u,\"visited\":[",cases,cycles,total_instructions);
}
static int tail_written(int pickup,unsigned offset) {
    // F9E2: +00 +06 +12..+19 +46..+49. 6AF0/6B44/6BB2 also write +02..+0D,
    // countdown +10, extents +1E..+21, the record +42..+45 and link +4A..+4D.
    if(!pickup)return offset==0 || (offset>=6 && offset<8) || (offset>=0x12 && offset<0x1a) || (offset>=0x46 && offset<0x4a);
    return offset==0 || (offset>=2 && offset<14) || (offset>=0x10 && offset<0x1a) || (offset>=0x1e && offset<0x22) || (offset>=0x42 && offset<0x4e);
}
static void tail_cases(void) {
    enum {slots=18,tables=20,head=84,width=12,fields=head+slots*width};
    unsigned f[fields],cases=0,cycles=0;int first;
    const unsigned links[2]={0xff0832,0xff09da},link_sentinels[2]={0x11223344,0x55667788};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid setup tail case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete setup tail case");
        if(f[0]>68 || f[1]>255)fail("setup tail stack outside range");
        for(unsigned i=tables;i<head;++i)if(f[i]>65535)fail("setup tail table outside range");
        unsigned n=0;for(unsigned k=0;k<16;++k)n+=f[tables+k]!=0xffff;
        const unsigned members=n+2;tail_pickups=n;
        for(unsigned m=0;m<slots;++m) {
            const unsigned *r=f+head+width*m;
            if(f[2+m]>=68)fail("setup tail slot outside range");
            for(unsigned k=0;k<m;++k)if(f[2+m]==f[2+k])fail("setup tail slots repeat");
            if(r[0]>255 || r[1]>65535 || r[2]>65535 || r[5]>255 || r[6]>65535 || r[7]>65535 || r[8]>255 || r[9]>255 || r[10]>65535 || r[11]>65535)fail("setup tail residue outside range");
        }
        memset(ram,0xa5,sizeof ram);memset(ram+0x1b50,f[1],0x3008-0x1b50);
        unsigned stack[68],depth=0;
        for(unsigned i=0;i<68 && depth+members<f[0];++i){int member=0;for(unsigned m=0;m<members;++m)member|=i==f[2+m];if(!member)stack[depth++]=i;}
        for(unsigned m=members;m-->0;)if(f[0]>=m+1)stack[depth++]=f[2+m];
        m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<depth;++i)m68k_write_memory_32(0xff300c+4*i,0xffff1b50+78*stack[i]);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        for(unsigned k=0;k<16;++k){m68k_write_memory_16(0xff312c+2*k,f[tables+k]);m68k_write_memory_16(0xff314c+2*k,f[tables+16+k]);
            m68k_write_memory_16(0xff4c80+4*k,f[tables+32+2*k]);m68k_write_memory_16(0xff4c82+4*k,f[tables+33+2*k]);}
        memset(ram+0x447a,0x5a,0xc0);m68k_write_memory_32(0xff31ac,0x24681357);m68k_write_memory_32(0xff31b0,0x13579bdf);
        for(unsigned k=0;k<2;++k)m68k_write_memory_32(links[k],link_sentinels[k]);
        for(unsigned m=0;m<slots;++m) {
            const unsigned a=0xff1b50+78*f[2+m],*r=f+head+width*m;
            m68k_write_memory_8(a+1,r[0]);m68k_write_memory_16(a+0x0e,r[1]);m68k_write_memory_16(a+0x10,r[2]);
            m68k_write_memory_32(a+0x4a,r[3]);m68k_write_memory_32(a+0x1a,r[4]);
            for(unsigned o=0x1e;o<0x46;++o)m68k_write_memory_8(a+o,r[5]);
            m68k_write_memory_16(a+8,r[6]);m68k_write_memory_16(a+10,r[7]);m68k_write_memory_8(a+12,r[8]);m68k_write_memory_8(a+13,r[9]);
            m68k_write_memory_16(a+2,r[10]);m68k_write_memory_16(a+4,r[11]);
        }
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A5,0xffff0690);m68k_set_reg(M68K_REG_SR,0x2700); // The prefix leaves A5 on the P1 control.
        pair_pops=pair_exhausted=0;call(0x68a4);++cycles;
        // 6A94 clobbers D0-D3/D7/A0-A3; A5 ends on the P2 control and A6 on its link.
        for(unsigned reg=M68K_REG_D4;reg<=M68K_REG_D6;++reg)if(m68k_get_reg(NULL,reg)!=0x5a5a0000u+reg)fail("setup tail changed preserved register");
        if(m68k_get_reg(NULL,M68K_REG_A4)!=0x5a5a0000u+M68K_REG_A4)fail("setup tail changed A4");
        const unsigned popped=pair_exhausted ? pair_pops : members;
        if(pair_pops!=popped || popped>depth || (pair_exhausted && popped!=depth) || (!pair_exhausted && depth<members))fail("setup tail allocation count differs");
        if(m68k_read_memory_32(0xff311c)!=0xffff300c+4*(depth-popped))fail("setup tail free head differs");
        if(m68k_get_reg(NULL,M68K_REG_A5)!=(popped>n || !pair_exhausted ? 0xffff0838u : 0xffff0690u))fail("setup tail A5 differs");
        if(!pair_exhausted && m68k_get_reg(NULL,M68K_REG_A6)!=0xffff1b50+78*f[2+members-1])fail("setup tail A6 differs");
        // 6A94 clears the records and both globals before its first pop.
        if(m68k_read_memory_32(0xff31ac) || m68k_read_memory_32(0xff31b0))fail("setup tail FF31AC/FF31B0 not cleared");
        for(unsigned r=0,k=0;r<16;++r) {
            while(k<16 && f[tables+k]==0xffff)++k;
            const int made=r<n && r<popped;
            const unsigned obj=m68k_read_memory_32(0xff447a+12*r),a0=m68k_read_memory_32(0xff447e + 12*r),a1=m68k_read_memory_32(0xff4482+12*r);
            if(made ? obj!=0xffff1b50+78*f[2+r] || a0!=0xffff312c+2*k || a1!=0xffff314c+2*k : obj || a0 || a1)fail("setup tail record differs");
            if(r<n)++k;
        }
        for(unsigned k=0;k<2;++k)if(m68k_read_memory_32(links[k])!=(popped>n+k ? 0xffff1b50+78*f[2+n+k] : link_sentinels[k]))fail("setup tail control link differs");
        for(unsigned a=0;a<65536;++a) {
            const unsigned o=(a-0x1b50)%78,i=(a-0x1b50)/78;int slot=0;
            for(unsigned m=0;m<popped;++m)if(a>=0x1b50 && a<0x3008 && i==f[2+m] && tail_written(m<n,o))slot=1;
            const int allowed=slot || (a>=0xef00 && a<0xf004) || (a>=0x311c && a<0x3120) || (a>=0x447a && a<0x453a) || (a>=0x31ac && a<0x31b4) || (a>=0x0832 && a<0x0836) || (a>=0x09da && a<0x09de);
            if(!allowed && ram[a]!=before[a]){fprintf(stderr,"case %u address FF%04X popped %u\n",cases,a,popped);fail("setup tail changed uncontracted byte");}
        }
        if(pair_exhausted)printf("0 %u\n",popped);
        else {
            printf("1 %u",n);for(unsigned m=0;m<members;++m)printf(" %u",f[2+m]);
            for(unsigned r=0;r<16;++r) {
                const unsigned obj=m68k_read_memory_32(0xff447a+12*r),a0=m68k_read_memory_32(0xff447e + 12*r);
                printf(" %u %u",obj ? (obj-0xffff1b50)/78+1 : 0,a0 ? (a0-0xffff312c)/2 : 0);
            }
            printf(" %u %u %u",m68k_read_memory_32(0xff31b0),m68k_read_memory_32(0xff31ac)!=0,(m68k_read_memory_32(0xff311c)-0xffff300c)/4);
            for(unsigned m=0;m<members;++m) {
                const unsigned a=0xff1b50+78*f[2+m];pair_print(a);
                if(m<n)printf(" %u %u %u",m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20),(m68k_read_memory_32(a+0x42)-0xffff447a)/12);
            }
            puts("");
        }
    }
    if(ferror(stdin))fail("setup tail input failure");
    fprintf(stderr,"{\"cases\":%u,\"calls\":%u,\"instructions\":%u,\"visited\":[",cases,cycles,total_instructions);
}
static void message_cases(void) {
    unsigned f[22],cases=0,cycles=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid setup message case");
        for(unsigned i=1;i<22;++i)if(scanf("%u",&f[i])!=1)fail("incomplete setup message case");
        if(f[0]>65535 || f[1]>65535 || f[2]>65535 || f[4]>255 || f[5]>65535)fail("setup message field outside range");
        for(unsigned k=0;k<16;++k)if(f[6+k]>65535)fail("setup message kind outside range");
        memset(ram,0xa5,sizeof ram);
        m68k_write_memory_16(0xff33e2,f[0]);m68k_write_memory_16(0xff31aa,f[1]);m68k_write_memory_16(0xff316c,f[2]);m68k_write_memory_32(0xff0d60,f[3]);
        m68k_write_memory_32(0xff06d6,0x12345678);m68k_write_memory_8(0xff06e3,f[4]);m68k_write_memory_16(0xff06e4,0x5a5a);m68k_write_memory_16(0xff06e6,f[5]);
        m68k_write_memory_16(0xff010c,0xa55a);
        for(unsigned k=0;k<16;++k)m68k_write_memory_16(0xff312c+2*k,f[6+k]);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A5,0xffff0838);m68k_set_reg(M68K_REG_SR,0x2700); // The tail leaves A5 on the P2 control.
        message_vdp_count=0;message_lock_ok=1;message_selected=0;call(0x68bc);++cycles;
        const int open=m68k_get_reg(NULL,M68K_REG_PC)==0x6f02;
        const unsigned regs[]={M68K_REG_D1,M68K_REG_D3,M68K_REG_D4,M68K_REG_D5,M68K_REG_D6,M68K_REG_A1,M68K_REG_A2,M68K_REG_A3,M68K_REG_A4,M68K_REG_A6};
        for(unsigned i=0;i<10;++i)if(m68k_get_reg(NULL,regs[i])!=0x5a5a0000u+regs[i])fail("setup message changed preserved register");
        if(m68k_get_reg(NULL,M68K_REG_A5)!=(message_selected ? 0xffff0690u : 0xffff0838u))fail("setup message A5 differs");
        if(m68k_read_memory_16(0xff010c)!=0xa55a)fail("setup message lock not restored");
        for(unsigned a=0;a<65536;++a) {
            const int allowed=(a>=0xef00 && a<0xf004) || (a>=0x31aa && a<0x31ac) || (a>=0x06d6 && a<0x06da) || a==0x06e3;
            if(!allowed && ram[a]!=before[a])fail("setup message changed uncontracted byte");
        }
        const unsigned message=m68k_read_memory_32(0xff06d6);
        const unsigned code=message==0xd28c ? 1 : message==0xd2a2 ? 2 : message==0xffffffff ? 0 : message==0x12345678 ? 3 : 99;
        if(code==99)fail("setup message pointer differs");
        unsigned cleared=0,vram=0;
        if(message_vdp_count) {
            // CB9A: register 8004, a VRAM write command, 26 data words of 1, register 8014.
            if(message_vdp_count!=30 || !message_lock_ok || message_vdp[0][0]!=0xc00004 || message_vdp[0][1]!=0x8004 || message_vdp[1][0]!=0xc00004 || message_vdp[2][0]!=0xc00006
               || message_vdp[29][0]!=0xc00004 || message_vdp[29][1]!=0x8014)fail("setup message VDP sequence differs");
            for(unsigned i=3;i<29;++i)if(message_vdp[i][0]!=0xc00000 || message_vdp[i][1]!=1)fail("setup message VDP data differs");
            const unsigned command=message_vdp[1][1]<<16 | message_vdp[2][1];
            if((command&0xc000fffc)!=0x40000000)fail("setup message VDP command differs");
            cleared=1;vram=(command>>16&0x3fff)|(command&3)<<14;
        }
        if(open)printf("0 3\n");
        else printf("1 %u %u %u %u %u %u\n",message_selected,message_selected ? code : 3,m68k_read_memory_8(0xff06e3),m68k_read_memory_16(0xff31aa),cleared,vram);
    }
    if(ferror(stdin))fail("setup message input failure");
    fprintf(stderr,"{\"cases\":%u,\"calls\":%u,\"instructions\":%u,\"visited\":[",cases,cycles,total_instructions);
}
static int pairs_written(int lead,unsigned offset) {
    // F9E2: +00 +06 +12..+19 +46..+49. Both members: +00 +02..+07 +16..+19;
    // the lead also countdown +10, its partner link +36..+39 and control +4A..+4D.
    return offset==0 || (offset>=2 && offset<8) || (offset>=0x12 && offset<0x1a) || (offset>=0x46 && offset<0x4a)
        || (lead && ((offset>=0x10 && offset<0x12) || (offset>=0x36 && offset<0x3a) || (offset>=0x4a && offset<0x4e)));
}
static void pairs_cases(void) {
    enum {slots=8,head=17,width=10,fields=head+slots*width};
    unsigned f[fields],cases=0,cycles=0;int first;
    const unsigned handlers[4]={0x8040,0x71ce,0x73d8,0x75e2};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid setup pairs case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete setup pairs case");
        if(f[0]>68 || f[1]>255)fail("setup pairs stack outside range");
        for(unsigned i=3;i<9;++i)if(f[i]>65535)fail("setup pairs word outside range");
        unsigned open[4],opened=0,members=0;
        for(unsigned i=0;i<4;++i)if(f[3+i])open[opened++]=i;
        members=2*opened;
        for(unsigned m=0;m<slots;++m) {
            const unsigned *r=f+head+width*m;
            if(f[9+m]>=68)fail("setup pairs slot outside range");
            for(unsigned k=0;k<m;++k)if(f[9+m]==f[9+k])fail("setup pairs slots repeat");
            if(r[0]>255 || r[1]>65535 || r[2]>65535 || r[5]>255 || r[6]>65535 || r[7]>65535 || r[8]>255 || r[9]>255)fail("setup pairs residue outside range");
        }
        memset(ram,0xa5,sizeof ram);memset(ram+0x1b50,f[1],0x3008-0x1b50);
        unsigned stack[68],depth=0;
        for(unsigned i=0;i<68 && depth+members<f[0];++i){int member=0;for(unsigned m=0;m<members;++m)member|=i==f[9+m];if(!member)stack[depth++]=i;}
        for(unsigned m=members;m-->0;)if(f[0]>=m+1)stack[depth++]=f[9+m];
        m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<depth;++i)m68k_write_memory_32(0xff300c+4*i,0xffff1b50+78*stack[i]);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        for(unsigned i=0;i<4;++i)m68k_write_memory_16(0xff3172+2*i,f[3+i]);
        m68k_write_memory_16(0xff0874,f[7]);m68k_write_memory_16(0xff0876,f[8]); // FF0838 +3C/+3E.
        for(unsigned m=0;m<slots;++m) {
            const unsigned a=0xff1b50+78*f[9+m],*r=f+head+width*m;
            m68k_write_memory_8(a+1,r[0]);m68k_write_memory_16(a+0x0e,r[1]);m68k_write_memory_16(a+0x10,r[2]);
            m68k_write_memory_32(a+0x4a,r[3]);m68k_write_memory_32(a+0x1a,r[4]);
            for(unsigned o=0x1e;o<0x46;++o)m68k_write_memory_8(a+o,r[5]);
            m68k_write_memory_16(a+8,r[6]);m68k_write_memory_16(a+10,r[7]);m68k_write_memory_8(a+12,r[8]);m68k_write_memory_8(a+13,r[9]);
        }
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_A5,f[2]);m68k_set_reg(M68K_REG_SR,0x2700);
        pair_pops=pair_exhausted=0;pairs_current=0;call(0x68c4);++cycles;
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A3;++reg) {
            if(reg==M68K_REG_A0)continue;
            if(m68k_get_reg(NULL,reg)!=0x5a5a0000u+reg)fail("setup pairs changed preserved register");
        }
        const unsigned popped=pair_exhausted ? pair_pops : members;
        if(pair_pops!=popped || popped>depth || (pair_exhausted && popped!=depth) || (!pair_exhausted && depth<members))fail("setup pairs allocation count differs");
        if(m68k_read_memory_32(0xff311c)!=0xffff300c+4*(depth-popped))fail("setup pairs free head differs");
        if(pair_exhausted ? m68k_get_reg(NULL,M68K_REG_A0)!=0xffff3008 : m68k_get_reg(NULL,M68K_REG_A0)!=0x5a5a0000u+M68K_REG_A0)fail("setup pairs A0 differs");
        // Pairs completed before any exhaustion: the lower pop is the partner.
        const unsigned complete=popped/2;unsigned partner[4],lead[4];
        for(unsigned k=0;k<complete;++k){const unsigned x=f[9+2*k],y=f[9+2*k+1];partner[k]=x<y ? x : y;lead[k]=x<y ? y : x;}
        if(!pair_exhausted) {
            // 7154/735E/7568 load A5 = FF0690 and keep A4/A6 on their pair; 7FBE restores A5/A6.
            int fixed=0;for(unsigned k=0;k<opened;++k)fixed|=open[k]!=0;
            if(m68k_get_reg(NULL,M68K_REG_A5)!=(fixed ? 0xffff0690u : f[2]))fail("setup pairs A5 differs");
            const unsigned a4=opened ? 0xffff1b50+78*partner[opened-1] : 0x5a5a0000u+M68K_REG_A4;
            const unsigned a6=opened && open[opened-1] ? 0xffff1b50+78*lead[opened-1] : 0x5a5a0000u+M68K_REG_A6;
            if(m68k_get_reg(NULL,M68K_REG_A4)!=a4 || m68k_get_reg(NULL,M68K_REG_A6)!=a6)fail("setup pairs A4/A6 differ");
        }
        for(unsigned k=0;k<complete;++k) {
            const unsigned p=0xff1b50+78*partner[k],l=0xff1b50+78*lead[k];
            if(m68k_read_memory_32(p+0x16)!=0x12646 || m68k_read_memory_32(p+0x46)!=0x12646 || m68k_read_memory_32(l+0x46)!=0x12646)fail("setup pairs selectors differ");
        }
        for(unsigned a=0;a<65536;++a) {
            const unsigned o=(a-0x1b50)%78,i=(a-0x1b50)/78;int slot=0;
            for(unsigned m=0;m<popped;++m)if(a>=0x1b50 && a<0x3008 && i==f[9+m] && pairs_written(m/2<complete && i==lead[m/2],o))slot=1;
            const int allowed=slot || (a>=0xef00 && a<0xf004) || (a>=0x311c && a<0x3120);
            if(!allowed && ram[a]!=before[a]){fprintf(stderr,"case %u address FF%04X popped %u\n",cases,a,popped);fail("setup pairs changed uncontracted byte");}
        }
        if(pair_exhausted)printf("0 %u\n",popped);
        else {
            unsigned mask=0;for(unsigned k=0;k<opened;++k)mask|=1u<<open[k];
            printf("1 %u",mask);for(unsigned k=0;k<opened;++k)printf(" %u %u",partner[k],lead[k]);
            printf(" %u",(m68k_read_memory_32(0xff311c)-0xffff300c)/4);
            for(unsigned k=0;k<opened;++k) {
                const unsigned l=0xff1b50+78*lead[k],handler=m68k_read_memory_32(l+0x16),link=m68k_read_memory_32(l+0x36);
                unsigned code=4;for(unsigned h=0;h<4;++h)if(handler==handlers[h])code=h;
                if(code==4 || link<0xffff1b50 || link>=0xffff3008 || (link-0xffff1b50)%78)fail("setup pairs lead handler/link differs");
                pair_print(0xff1b50+78*partner[k]);pair_print(l);printf(" %u %u",code,(link-0xffff1b50)/78);
            }
            puts("");
        }
    }
    if(ferror(stdin))fail("setup pairs input failure");
    fprintf(stderr,"{\"cases\":%u,\"calls\":%u,\"instructions\":%u,\"visited\":[",cases,cycles,total_instructions);
}
static void hit_fields(unsigned a) {
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    for(unsigned i=0;i<11;++i)printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(a+offsets[i]) : m68k_read_memory_16(a+offsets[i]));
}
static unsigned hit_record(unsigned a) {
    const unsigned r=m68k_read_memory_32(a+0x42);
    if(r<0xffff447a || r>=0xffff453a || (r-0xffff447a)%12)fail("pickup hit record pointer differs");
    return (r-0xffff447a)/12;
}
static void pickup_hit_cases(void) {
    // pickup x y flags mode w06 w08 w0a c0c r0d target count, control, extents,
    // record; slots s l1 l2; link kinds; per link the eleven fields, +36, ten
    // history words, owner, extents, record; sixteen kinds; sixteen record
    // entries (16 = absent); 78EE inputs; free depth; walks; the walk after
    // which both trackers leave (Y + 4000, 0 = never); the pickup's starting
    // phase (0 collectable, 1 vanishing, 2 swapped out, 3 swapped in).
    enum {fields=115,link=20,width=26};
    unsigned f[fields],cases=0,walks=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid pickup hit case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete pickup hit case");
        for(unsigned i=0;i<11;++i)if(f[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("pickup field outside range");
        if(f[12]>65535 || f[13]>65535 || f[14]>15)fail("pickup extents/record outside range");
        const unsigned s=f[15],l1=f[16],l2=f[17];
        if(s>=68 || l1>=68 || l2>=68 || s==l1 || s==l2 || l1==l2 || f[18]>1 || f[19]>1)fail("pickup hit slots/link kinds invalid");
        for(unsigned k=0;k<2;++k) {
            const unsigned *r=f+link+width*k;
            for(unsigned i=0;i<11;++i)if(r[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("pickup hit link field outside range");
            for(unsigned i=11;i<22;++i)if(r[i]>65535)fail("pickup hit link word outside range");
            if(r[23]>65535 || r[24]>65535 || r[25]>15)fail("pickup hit link word outside range");
        }
        for(unsigned i=72;i<88;++i)if(f[i]>65535)fail("pickup hit kind outside range");
        for(unsigned i=88;i<104;++i)if(f[i]>16)fail("pickup hit record entry outside range");
        for(unsigned i=104;i<111;++i)if(f[i]>65535)fail("pickup hit collision word outside range");
        if(f[108]>1 || (!f[108] && (f[109] || f[110])) || f[111]>64 || !f[112] || f[112]>64 || f[113]>64 || f[114]>3)fail("pickup hit context invalid");
        const unsigned rp=f[14],re[2]={f[link+25],f[link+width+25]};
        if(f[88+rp]==16)fail("pickup hit record absent");
        for(unsigned k=0;k<2;++k)if(f[18+k] && f[88+re[k]]==16)fail("pickup hit emitter record absent");
        if(f[18] && f[19] && re[0]==re[1])fail("pickup hit emitter records shared");
        unsigned o=0;while(o==s || o==l1 || o==l2)++o; // The holder of every other record.
        memset(ram,0xa5,sizeof ram);sound_count=0;hit_stop=0;
        const unsigned ps=0xffff1b50+78*s,pl[2]={0xffff1b50+78*l1,0xffff1b50+78*l2};
        memset(ram+(ps&65535),0,78);
        for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(ps+offsets[i],f[i]);else m68k_write_memory_16(ps+offsets[i],f[i]);}
        m68k_write_memory_32(ps+0x4a,f[11]);m68k_write_memory_16(ps+0x1e,f[12]);m68k_write_memory_16(ps+0x20,f[13]);
        m68k_write_memory_32(ps+0x42,0xffff447a+12*rp);m68k_write_memory_32(ps+0x16,0x12646);
        const unsigned callbacks[4]={0xcaf0,0xfaa4,0x6cda,0x6cf4}; // A collectable callback stops at CAF0.
        m68k_write_memory_32(ps+0x46,f[114] ? 0x12646 : 0x6bd6);m68k_write_memory_32(ps+0x1a,callbacks[f[114]]);
        for(unsigned k=0;k<2;++k) {
            const unsigned a=pl[k],*r=f+link+width*k;memset(ram+(a&65535),0,78);
            for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(a+offsets[i],r[i]);else m68k_write_memory_16(a+offsets[i],r[i]);}
            m68k_write_memory_32(a+0x4a,r[22]);m68k_write_memory_32(a+0x46,0x12646);
            if(f[18+k]) { // A carrying 6D8C emitter.
                m68k_write_memory_32(a+0x16,0x6d8c);m68k_write_memory_16(a+0x36,r[11]);
                for(unsigned h=0;h<10;++h)m68k_write_memory_16(a+0x22+2*h,r[12+h]);
                m68k_write_memory_16(a+0x1e,r[23]);m68k_write_memory_16(a+0x20,r[24]);m68k_write_memory_32(a+0x42,0xffff447a+12*r[25]);
            } else m68k_write_memory_32(a+0x16,0x12646);
        }
        m68k_write_memory_32(0xff0832,pl[0]);m68k_write_memory_32(0xff09da,pl[1]);
        for(unsigned k=0;k<16;++k)m68k_write_memory_16(0xff312c+2*k,f[72+k]);
        for(unsigned r=0;r<16;++r) {
            const unsigned a=0xff447a+12*r;
            if(f[88+r]==16){m68k_write_memory_32(a,0);m68k_write_memory_32(a+4,0);m68k_write_memory_32(a+8,0);continue;}
            // An emitter's record names it even when a vanishing pickup still points there.
            const unsigned obj=(f[18] && r==re[0]) ? pl[0] : (f[19] && r==re[1]) ? pl[1] : r==rp ? ps : 0xffff1b50+78*o;
            m68k_write_memory_32(a,obj);m68k_write_memory_32(a+4,0xffff312c+2*f[88+r]);m68k_write_memory_32(a+8,0xffff314c+2*f[88+r]);
        }
        m68k_write_memory_16(0xff06d2,f[104]);m68k_write_memory_16(0xff06d4,f[105]);m68k_write_memory_16(0xff13ae,f[106]);
        m68k_write_memory_16(0xff33e2,f[107]);collision_secondary=f[108];m68k_write_memory_16(0xff087a,f[109]);m68k_write_memory_16(0xff087c,f[110]);
        for(unsigned i=0;i<4;++i)m68k_write_memory_16(0xff0a9e + 2*i,0x1111*(i+1));
        m68k_write_memory_16(0xff0ab6,0x5a5a); // FCB32 selector mismatch: request only, no driver.
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth<f[111];++i)if(i!=s && i!=l1 && i!=l2 && i!=o)m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        for(unsigned w=0;w<f[112] && !hit_stop;++w) {
            if(f[113] && w==f[113]){m68k_write_memory_16(0xff06d4,(f[105]+0x4000)&65535);if(f[108])m68k_write_memory_16(0xff087c,(f[110]+0x4000)&65535);}
            m68k_set_reg(M68K_REG_A6,ps);call(0x69aa);++walks;
            if(!hit_stop && m68k_get_reg(NULL,M68K_REG_A6)!=ps)fail("pickup walk identity changed");
        }
        if(hit_stop){printf("0 %u\n",hit_stop==0xcaf0 ? 2 : 1);continue;}
        for(unsigned i=0;i<78;++i) {
            const unsigned a=(ps&65535)+i;
            const int allowed=i==0 || (i>=2 && i<0x14) || (i>=0x16 && i<0x1e) || (i>=0x42 && i<0x4a);
            if(!allowed && ram[a]!=before[a])fail("pickup hit changed an uncontracted pickup byte");
        }
        for(unsigned k=0;k<2;++k) {
            const unsigned a=pl[k]&65535,emitter=m68k_read_memory_32(pl[k]+0x16)==0x6d8c;
            if(!f[18+k] && !emitter){for(unsigned i=0;i<78;++i)if(ram[a+i]!=before[a+i])fail("dormant link changed");}
            else if(!f[18+k]) { // 6D22: the FB06 copy carries the pickup's residue and its callback (seeded, or 6CF4 once re-dressed).
                const unsigned callback=m68k_read_memory_32(pl[k]+0x1a);
                if(ram[a+1] || ram[a+0x14] || ram[a+0x15] || (callback!=0xcaf0 && callback!=0x6cf4) || m68k_read_memory_32(pl[k]+0x46)!=0x12646)fail("converted link residue differs");
                for(unsigned i=0x38;i<0x42;++i)if(ram[a+i])fail("converted link residue differs");
            } else {
                if(!emitter)fail("emitter link lost its handler");
                for(unsigned i=0;i<78;++i) {
                    const int allowed=(i>=6 && i<0x0c) || i==0x0d || i==0x10 || i==0x11 || (i>=0x42 && i<0x46);
                    if(!allowed && ram[a+i]!=before[a+i])fail("exchange changed an uncontracted link byte");
                }
            }
        }
        for(unsigned a=0;a<65536;++a) {
            const unsigned i=(a-0x1b50)/78;
            const int mine=a>=0x1b50 && a<0x3008 && (i==s || i==l1 || i==l2);
            const int record=a>=0x447a && a<0x453a && (a-0x447a)%12<4;
            const int moved=f[113] && f[113]<f[112] && ((a>=0x06d4 && a<0x06d6) || (f[108] && a>=0x087c && a<0x087e));
            const int allowed=mine || record || moved || (a>=0x311c && a<0x3120) || (a>=0x300c+4*depth && a<0x3010+4*depth) || (a>=0x0a9e && a<0x0aa6) || (a>=0xef00 && a<0xf004);
            if(!allowed && ram[a]!=before[a]){fprintf(stderr,"case %u address FF%04X\n",cases,a);fail("pickup hit changed an uncontracted byte");}
        }
        const unsigned after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4,released=after==depth+1;
        if(released ? m68k_read_memory_32(0xff300c+4*depth)!=ps : after!=depth)fail("pickup hit free stack differs");
        printf("1 %u",released);hit_fields(ps);
        printf(" %u %u %u %u",m68k_read_memory_32(ps+0x4a),m68k_read_memory_16(ps+0x1e),m68k_read_memory_16(ps+0x20),hit_record(ps));
        const unsigned service=m68k_read_memory_32(ps+0x46),callback=m68k_read_memory_32(ps+0x1a);
        const unsigned phase=service==0x6bd6 ? 0 : callback==0xfaa4 ? 1 : callback==0x6cda ? 2 : callback==0x6cf4 ? 3 : 9;
        if(m68k_read_memory_32(ps+0x16)!=0x12646 || phase==9 || (phase && service!=0x12646))fail("pickup phase selectors differ");
        printf(" %u",phase);
        for(unsigned k=0;k<2;++k) {
            const unsigned a=pl[k],emitter=m68k_read_memory_32(a+0x16)==0x6d8c;
            printf(" %u",emitter);hit_fields(a);
            if(emitter) {
                printf(" %u",m68k_read_memory_16(a+0x36));for(unsigned h=0;h<10;++h)printf(" %u",m68k_read_memory_16(a+0x22+2*h));
                printf(" %u %u %u %u",m68k_read_memory_32(a+0x4a),m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20),hit_record(a));
            } else printf(" %u",m68k_read_memory_32(a+0x4a));
        }
        const unsigned holders[4]={ps,pl[0],pl[1],0xffff1b50+78*o};
        for(unsigned r=0;r<16;++r) {
            const unsigned a=0xff447a+12*r,object=m68k_read_memory_32(a),entry=m68k_read_memory_32(a+4);
            unsigned code=0;for(unsigned k=0;k<4;++k)if(object==holders[k])code=k+1;
            if(object && !code)fail("pickup hit record object differs");
            if(entry && (entry<0xffff312c || entry>=0xffff314c || (entry&1)))fail("pickup hit record entry differs");
            printf(" %u %u",code,entry ? (entry-0xffff312c)/2 : 16);
        }
        printf(" %u",sound_count);for(unsigned n=0;n<sound_count;++n)for(unsigned i=0;i<4;++i)printf(" %u",sound_requests[n][i]);
        printf(" %u %u\n",after,released ? s : 99);
    }
    if(ferror(stdin))fail("pickup hit input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"queries\":%u,\"visited\":[",cases,walks,total_instructions,collision_queries);
}
static void probe_link(unsigned a, const unsigned *r, unsigned emitter) {
    // The --pickup-hit link seeding: a dormant return-only object or a carrying 6D8C emitter.
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    memset(ram+(a&65535),0,78);
    for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(a+offsets[i],r[i]);else m68k_write_memory_16(a+offsets[i],r[i]);}
    m68k_write_memory_32(a+0x4a,r[22]);m68k_write_memory_32(a+0x46,0x12646);
    if(emitter) {
        m68k_write_memory_32(a+0x16,0x6d8c);m68k_write_memory_16(a+0x36,r[11]);
        for(unsigned h=0;h<10;++h)m68k_write_memory_16(a+0x22+2*h,r[12+h]);
        m68k_write_memory_16(a+0x1e,r[23]);m68k_write_memory_16(a+0x20,r[24]);m68k_write_memory_32(a+0x42,0xffff447a+12*r[25]);
    } else m68k_write_memory_32(a+0x16,0x12646);
}
static void probe_print_link(unsigned a) {
    const unsigned emitter=m68k_read_memory_32(a+0x16)==0x6d8c;
    printf(" %u",emitter);hit_fields(a);
    if(emitter) {
        printf(" %u",m68k_read_memory_16(a+0x36));for(unsigned h=0;h<10;++h)printf(" %u",m68k_read_memory_16(a+0x22+2*h));
        printf(" %u %u %u %u",m68k_read_memory_32(a+0x4a),m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20),hit_record(a));
    } else printf(" %u",m68k_read_memory_32(a+0x4a));
}
static void probe_hit_cases(void) {
    // probe x y flags mode w06 w08 w0a c0c r0d target count, control, extents;
    // slots s l1 l2; link kinds; per link the 26 --pickup-hit fields; FF31B0
    // high and low words; 78EE inputs; free depth, the top free slot and the one
    // below it; walks; the walks after which P1 and P2 leave (Y + 4000, 0 = never).
    enum {fields=86,link=19,width=26};
    unsigned f[fields],cases=0,walks=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid probe hit case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete probe hit case");
        for(unsigned i=0;i<11;++i)if(f[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("probe field outside range");
        if(f[12]>65535 || f[13]>65535)fail("probe extents outside range");
        const unsigned s=f[14],l1=f[15],l2=f[16],top=f[81],below=f[82];
        if(s>=68 || l1>=68 || l2>=68 || s==l1 || s==l2 || l1==l2 || f[17]>1 || f[18]>1)fail("probe hit slots/link kinds invalid");
        if(top>=68 || below>=68 || top==below || top==s || top==l1 || top==l2 || below==s || below==l1 || below==l2)fail("probe hit free slots invalid");
        for(unsigned k=0;k<2;++k) {
            const unsigned *r=f+link+width*k;
            for(unsigned i=0;i<11;++i)if(r[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("probe hit link field outside range");
            for(unsigned i=11;i<22;++i)if(r[i]>65535)fail("probe hit link word outside range");
            if(r[23]>65535 || r[24]>65535 || r[25]>15)fail("probe hit link word outside range");
        }
        for(unsigned i=71;i<80;++i)if(f[i]>65535)fail("probe hit context word outside range");
        if(f[77]>1 || (!f[77] && (f[78] || f[79])) || f[80]>64 || !f[83] || f[83]>64 || f[84]>64 || f[85]>64)fail("probe hit context invalid");
        memset(ram,0xa5,sizeof ram);sound_count=0;hit_stop=hit_exhausted=delivery_count=0;
        const unsigned ps=0xffff1b50+78*s,pl[2]={0xffff1b50+78*l1,0xffff1b50+78*l2};
        memset(ram+(ps&65535),0,78);
        for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(ps+offsets[i],f[i]);else m68k_write_memory_16(ps+offsets[i],f[i]);}
        m68k_write_memory_32(ps+0x4a,f[11]);m68k_write_memory_16(ps+0x1e,f[12]);m68k_write_memory_16(ps+0x20,f[13]);
        m68k_write_memory_32(ps+0x16,0x12646);m68k_write_memory_32(ps+0x46,0x78ee);m68k_write_memory_32(ps+0x1a,0xcaf0); // A probe callback stops at CAF0.
        for(unsigned k=0;k<2;++k)probe_link(pl[k],f+link+width*k,f[17+k]);
        m68k_write_memory_32(0xff0832,pl[0]);m68k_write_memory_32(0xff09da,pl[1]);
        m68k_write_memory_16(0xff31b0,f[71]);m68k_write_memory_16(0xff31b2,f[72]);
        m68k_write_memory_16(0xff06d2,f[73]);m68k_write_memory_16(0xff06d4,f[74]);m68k_write_memory_16(0xff13ae,f[75]);
        m68k_write_memory_16(0xff33e2,f[76]);collision_secondary=f[77];m68k_write_memory_16(0xff087a,f[78]);m68k_write_memory_16(0xff087c,f[79]);
        for(unsigned i=0;i<4;++i)m68k_write_memory_16(0xff0a9e + 2*i,0x1111*(i+1));
        m68k_write_memory_16(0xff0ab6,0x5a5a); // FCB32 selector mismatch: request only, no driver.
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth+2<f[80];++i)if(i!=s && i!=l1 && i!=l2 && i!=top && i!=below)m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        if(f[80]>=2)m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*below);
        if(f[80]>=1)m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*top);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        for(unsigned w=0;w<f[83] && !hit_stop && !hit_exhausted;++w) {
            if(f[84] && w==f[84])m68k_write_memory_16(0xff06d4,(f[74]+0x4000)&65535);
            if(f[85] && w==f[85] && f[77])m68k_write_memory_16(0xff087c,(f[79]+0x4000)&65535);
            m68k_set_reg(M68K_REG_A6,ps);call(0x69aa);++walks;
            if(!hit_stop && !hit_exhausted && m68k_get_reg(NULL,M68K_REG_A6)!=ps)fail("probe walk identity changed");
        }
        if(hit_exhausted){printf("0 1\n");continue;}
        if(hit_stop){printf("0 3\n");continue;}
        for(unsigned i=0;i<78;++i) {
            const unsigned a=(ps&65535)+i;
            if(i!=0 && i!=6 && i!=7 && i!=0x0c && ram[a]!=before[a])fail("probe hit changed an uncontracted probe byte");
        }
        unsigned delivered[2]={0,0};
        for(unsigned n=0;n<delivery_count;++n)if(delivery_kinds[n]) {
            // FB06 copied the link just before CLR.B cleared its mode: the copy equals it elsewhere.
            const unsigned c=delivery_created[n]&65535;unsigned k=2;
            for(unsigned j=0;j<2;++j)if(!memcmp(ram+c+1,ram+(pl[j]&65535)+1,77) && f[17+j] && !ram[pl[j]&65535] && !delivered[j])k=j;
            if(k==2 || ram[c]!=0x87)fail("probe hit copy differs from its link");
            delivered[k]=1;
        }
        for(unsigned k=0;k<2;++k) {
            const unsigned a=pl[k]&65535;
            for(unsigned i=0;i<78;++i) {
                const int allowed=delivered[k] && (i==0 || (i>=2 && i<0x10) || i==0x12 || i==0x13 || (i>=0x16 && i<0x1e) || i==0x22 || i==0x23 || i==0x26 || i==0x27 || (i>=0x42 && i<0x4e));
                if(!allowed && ram[a+i]!=before[a+i])fail("probe hit changed an uncontracted link byte");
            }
        }
        for(unsigned n=0;n<delivery_count;++n)if(!delivery_kinds[n]) {
            const unsigned c=delivery_created[n];
            if(m68k_read_memory_16(c+0x14) || m68k_read_memory_32(c+0x16)!=0x12646 || m68k_read_memory_32(c+0x46)!=0x12646 || m68k_read_memory_32(c+0x1a)!=0xfaa4)fail("probe hit sparkle selectors differ");
        }
        for(unsigned a=0;a<65536;++a) {
            const unsigned i=(a-0x1b50)/78,o=(a-0x1b50)%78;int mine=a>=0x1b50 && a<0x3008 && (i==s || i==l1 || i==l2);
            for(unsigned n=0;n<delivery_count;++n)if(a>=0x1b50 && a<0x3008 && 0xff1b50+78*i==delivery_created[n])
                mine|=delivery_kinds[n] || o==0 || (o>=2 && o<0x10) || (o>=0x12 && o<0x1e) || (o>=0x46 && o<0x4a);
            const int moved=(f[84] && f[84]<f[83] && a>=0x06d4 && a<0x06d6) || (f[85] && f[85]<f[83] && f[77] && a>=0x087c && a<0x087e);
            const int allowed=mine || moved || (a>=0x311c && a<0x3120) || (a>=0x0a9e && a<0x0aa6) || (a>=0xef00 && a<0xf004);
            if(!allowed && ram[a]!=before[a]){fprintf(stderr,"case %u address FF%04X\n",cases,a);fail("probe hit changed an uncontracted byte");}
        }
        const unsigned after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4;
        if(after+delivery_count!=depth)fail("probe hit free stack differs");
        for(unsigned n=0;n<delivery_count;++n)if(m68k_read_memory_32(0xff300c+4*(depth-1-n))!=(delivery_created[n]|0xff000000u))fail("probe hit pop order differs");
        printf("1");hit_fields(ps);printf(" %u %u %u",m68k_read_memory_32(ps+0x4a),m68k_read_memory_16(ps+0x1e),m68k_read_memory_16(ps+0x20));
        for(unsigned k=0;k<2;++k)probe_print_link(pl[k]);
        printf(" %u",delivery_count);
        for(unsigned n=0;n<delivery_count;++n) {
            const unsigned c=delivery_created[n];printf(" %u %u",delivery_kinds[n],(c-0xff1b50)/78);
            if(!delivery_kinds[n]){const unsigned sparkle[]={2,4,18,0,6,8,10,12,13,14};for(unsigned i=0;i<10;++i)printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(c+sparkle[i]) : m68k_read_memory_16(c+sparkle[i]));continue;}
            hit_fields(c);printf(" %u %u %u %u %u %u",m68k_read_memory_32(c+0x4a),m68k_read_memory_16(c+0x22),m68k_read_memory_16(c+0x26),m68k_read_memory_16(c+0x1e),m68k_read_memory_16(c+0x20),hit_record(c));
        }
        printf(" %u",sound_count);for(unsigned n=0;n<sound_count;++n)for(unsigned i=0;i<4;++i)printf(" %u",sound_requests[n][i]);
        printf(" %u\n",after);
    }
    if(ferror(stdin))fail("probe hit input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"queries\":%u,\"visited\":[",cases,walks,total_instructions,collision_queries);
}
static void delivered_cases(void) {
    // kind (0 sparkle, 1 copy), x y flags mode w06 w08 w0a c0c r0d target count,
    // control, frames (+22/+26), extents, record (count..record zero for a
    // sparkle), slot, free depth, walks.
    enum {fields=21};
    unsigned f[fields],cases=0,walks=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid delivered case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete delivered case");
        for(unsigned i=0;i<11;++i)if(f[1+i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("delivered field outside range");
        if(f[0]>1 || f[13]>65535 || f[14]>65535 || f[15]>65535 || f[16]>65535 || f[17]>15 || f[18]>=68 || f[19]>64 || !f[20] || f[20]>64)fail("delivered context invalid");
        if(!f[0])for(unsigned i=11;i<18;++i)if(f[i])fail("sparkle residue must be zero");
        memset(ram,0xa5,sizeof ram);hit_stop=0;
        const unsigned a=0xffff1b50+78*f[18];memset(ram+(a&65535),0,78);
        for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(a+offsets[i],f[1+i]);else m68k_write_memory_16(a+offsets[i],f[1+i]);}
        m68k_write_memory_32(a+0x4a,f[12]);m68k_write_memory_16(a+0x22,f[13]);m68k_write_memory_16(a+0x26,f[14]);m68k_write_memory_16(a+0x1e,f[15]);m68k_write_memory_16(a+0x20,f[16]);
        if(f[0])m68k_write_memory_32(a+0x42,0xffff447a+12*f[17]);
        m68k_write_memory_32(a+0x16,0x12646);m68k_write_memory_32(a+0x46,0x12646);m68k_write_memory_32(a+0x1a,f[0] ? 0x79b6 : 0xfaa4);
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth<f[19];++i)if(i!=f[18])m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        for(unsigned w=0;w<f[20] && !hit_stop;++w) {
            m68k_set_reg(M68K_REG_A6,a);call(0x69aa);++walks;
            if(!hit_stop && m68k_get_reg(NULL,M68K_REG_A6)!=a)fail("delivered walk identity changed");
        }
        if(hit_stop){printf("0 2\n");continue;}
        const unsigned after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4,released=after==depth+1;
        if(released ? m68k_read_memory_32(0xff300c+4*depth)!=a : after!=depth)fail("delivered free stack differs");
        for(unsigned x=0;x<65536;++x) {
            const int mine=x>=(a&65535) && x<(a&65535)+78 && (x-(a&65535)==0 || x-(a&65535)==6 || x-(a&65535)==7 || x-(a&65535)==0x0c);
            const int allowed=mine || (x>=0x311c && x<0x3120) || (released && x>=0x300c+4*depth && x<0x3010+4*depth) || (x>=0xef00 && x<0xf004);
            if(!allowed && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("delivered walk changed an uncontracted byte");}
        }
        printf("1 %u",released);hit_fields(a);
        if(f[0])printf(" %u %u %u %u %u %u",m68k_read_memory_32(a+0x4a),m68k_read_memory_16(a+0x22),m68k_read_memory_16(a+0x26),m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20),hit_record(a));
        else printf(" 0 0 0 0 0 0");
        printf(" %u\n",after);
    }
    if(ferror(stdin))fail("delivered input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"visited\":[",cases,walks,total_instructions);
}
static void table_print(unsigned a) {
    // A 7A88 table object: the eleven fields, +4A, the +2E cursor (a word index into 7A58), +32 and +36.
    const unsigned cursor=m68k_read_memory_32(a+0x2e);
    if(cursor<0x7a58 || cursor>=0x7a88 || (cursor&1))fail("ingredient table cursor differs");
    hit_fields(a);printf(" %u %u %u %u",m68k_read_memory_32(a+0x4a),(cursor-0x7a58)/2,m68k_read_memory_16(a+0x32),m68k_read_memory_16(a+0x36));
}
static void ingredient_cases(void) {
    // copy x y flags mode w06 w08 w0a c0c r0d target count, control, frames,
    // extents, record; copy, FF31B4 and record-holder slots; record entry;
    // FF31AC set; the control's +46 code, +53, +56; FF0D60 as two words; FF31BC;
    // FF31BE; free depth; walks.
    enum {fields=31};
    unsigned f[fields],cases=0,walks=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16},messages[5]={0xffffffff,0xd28c,0xd2a2,0xd20e,0xd22f};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid ingredient case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete ingredient case");
        for(unsigned i=0;i<11;++i)if(f[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("ingredient field outside range");
        const unsigned s=f[17],t=f[18],h=f[19];
        if(f[12]>65535 || f[13]>65535 || f[14]>65535 || f[15]>65535 || f[16]>15 || s>=68 || t>=68 || h>=68 || s==t || s==h || t==h || f[20]>15 || f[21]>1 || f[22]>4
           || f[23]>255 || f[24]>65535 || f[25]>65535 || f[26]>65535 || f[27]>65535 || f[28]>65535 || f[29]>64 || !f[30] || f[30]>64
           || (f[11]!=0xffff0690u && f[11]!=0xffff0838u))fail("ingredient context invalid");
        memset(ram,0xa5,sizeof ram);hit_stop=delivery_count=0;
        const unsigned a=0xffff1b50+78*s,ta=0xffff1b50+78*t,ha=0xffff1b50+78*h,control=f[11],rec=0xff447a+12*f[16];
        memset(ram+(a&65535),0,78);
        for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(a+offsets[i],f[i]);else m68k_write_memory_16(a+offsets[i],f[i]);}
        m68k_write_memory_32(a+0x4a,control);m68k_write_memory_16(a+0x22,f[12]);m68k_write_memory_16(a+0x26,f[13]);m68k_write_memory_16(a+0x1e,f[14]);m68k_write_memory_16(a+0x20,f[15]);
        m68k_write_memory_32(a+0x42,0xffff0000u|rec);m68k_write_memory_32(a+0x16,0x12646);m68k_write_memory_32(a+0x46,0x12646);m68k_write_memory_32(a+0x1a,0x79b6);
        memset(ram+(ta&65535),0,78);m68k_write_memory_32(ta+0x16,0x12646);m68k_write_memory_32(ta+0x46,0x12646); // The dormant FF31B4 object.
        m68k_write_memory_32(rec,ha);m68k_write_memory_32(rec+4,0xffff312c+2*f[20]);m68k_write_memory_32(rec+8,0xffff314c+2*f[20]);
        m68k_write_memory_32(0xff31ac,f[21] ? ha : 0);m68k_write_memory_32(0xff31b4,ta);
        const unsigned m=control==0xffff0690u ? 0xff06d6 : 0xff087e; // +46; +53 and +56 follow.
        m68k_write_memory_32(m,messages[f[22]]);m68k_write_memory_8(m+0x0d,f[23]);m68k_write_memory_16(m+0x10,f[24]);
        m68k_write_memory_16(0xff0d60,f[25]);m68k_write_memory_16(0xff0d62,f[26]);m68k_write_memory_16(0xff31bc,f[27]);m68k_write_memory_16(0xff31be,f[28]);
        m68k_write_memory_16(0xff010c,0xa55a);
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth<f[29];++i)if(i!=s && i!=t && i!=h)m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);message_vdp_count=0;message_lock_ok=1;
        unsigned copied[78];int at_copy=0;
        for(unsigned w=0;w<f[30] && !hit_stop;++w) {
            m68k_set_reg(M68K_REG_A6,a);call(0x69aa);++walks;
            if(!hit_stop && m68k_get_reg(NULL,M68K_REG_A6)!=a)fail("ingredient walk identity changed");
            if(delivery_count && !at_copy){for(unsigned i=0;i<78;++i)copied[i]=ram[(ta&65535)+i];at_copy=1;}
        }
        if(hit_stop){printf("0 3\n");continue;}
        const unsigned called=delivery_count!=0,after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4,released=after==depth+1;
        if(delivery_count>1 || released!=called || (released && m68k_read_memory_32(0xff300c+4*depth)!=a) || (!released && after!=depth))fail("ingredient free stack differs");
        if(m68k_read_memory_16(0xff010c)!=0xa55a)fail("ingredient lock not restored");
        unsigned cleared=0,vram=0;
        if(message_vdp_count) {
            // CB9A: register 8004, a VRAM write command, 26 data words of 1, register 8014.
            if(message_vdp_count!=30 || !message_lock_ok || message_vdp[0][0]!=0xc00004 || message_vdp[0][1]!=0x8004 || message_vdp[1][0]!=0xc00004 || message_vdp[2][0]!=0xc00006
               || message_vdp[29][0]!=0xc00004 || message_vdp[29][1]!=0x8014)fail("ingredient VDP sequence differs");
            for(unsigned i=3;i<29;++i)if(message_vdp[i][0]!=0xc00000 || message_vdp[i][1]!=1)fail("ingredient VDP data differs");
            const unsigned command=message_vdp[1][1]<<16 | message_vdp[2][1];
            if((command&0xc000fffc)!=0x40000000)fail("ingredient VDP command differs");
            cleared=1;vram=(command>>16&0x3fff)|(command&3)<<14;
        }
        if(called) {
            // FB06 copied the called-back copy; FAA4 then cleared its mode and 7A88 moved it.
            for(unsigned i=1;i<78;++i) {
                const int moved=(i>=2 && i<6) || i==0x10 || i==0x11 || (i>=0x2e && i<0x34) || i==0x36 || i==0x37;
                if(!moved && copied[i]!=ram[(a&65535)+i])fail("ingredient copy differs from the released copy");
            }
            if(copied[0]!=0x81 || ram[a&65535])fail("ingredient copy modes differ");
            for(unsigned i=0;i<78;++i)if(copied[i]!=ram[(ta&65535)+i])fail("ingredient target changed after the copy");
        }
        for(unsigned x=0;x<65536;++x) {
            const unsigned o=(x-(a&65535));
            const int mine=x>=(a&65535) && x<(a&65535)+78 && (o==0 || (o>=2 && o<0x0e) || o==0x10 || o==0x11 || (o>=0x16 && o<0x1a) || (o>=0x2e && o<0x34) || o==0x36 || o==0x37);
            const int target=called && x>=(ta&65535) && x<(ta&65535)+78;
            const int globals=called && ((x>=0x31ac && x<0x31b0) || (x>=0x31bc && x<0x31c0) || (x>=(rec&65535) && x<(rec&65535)+4) || (x>=(m&65535) && x<(m&65535)+4) || x==(m&65535)+0x0d);
            const int allowed=mine || target || globals || (x>=0x311c && x<0x3120) || (released && x>=0x300c+4*depth && x<0x3010+4*depth) || (x>=0xef00 && x<0xf004);
            if(!allowed && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("ingredient walk changed an uncontracted byte");}
        }
        printf("1 %u %u",called,released);
        if(!called) {
            hit_fields(a);printf(" %u %u %u %u %u %u",m68k_read_memory_32(a+0x4a),m68k_read_memory_16(a+0x22),m68k_read_memory_16(a+0x26),m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20),hit_record(a));
        } else {
            table_print(a);table_print(ta);
            const unsigned activation=m68k_read_memory_32(0xff31ac),holder=m68k_read_memory_32(rec),message=m68k_read_memory_32(m);
            unsigned code=99;for(unsigned k=0;k<5;++k)if(message==messages[k])code=k;
            if(activation!=ta || holder!=ta || code==99)fail("ingredient identities differ");
            printf(" %u %u %u %u %u %u %u",t,t,(m68k_read_memory_32(rec+4)-0xffff312c)/2,code,m68k_read_memory_8(m+0x0d),m68k_read_memory_16(m+0x10),cleared);
            if(cleared)printf(" %u",vram);
            printf(" %u %u",m68k_read_memory_16(0xff31bc),m68k_read_memory_16(0xff31be));
        }
        printf(" %u\n",after);
    }
    if(ferror(stdin))fail("ingredient input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"visited\":[",cases,walks,total_instructions);
}
static void second_ingredient_cases(void) {
    // copy x y flags mode w06 w08 w0a c0c r0d target count, control, frames,
    // extents, record; copy, FF31AC, FF31B8, anchor and record-holder slots;
    // record entry; the FF31AC object's +32; anchor x y flags mode w06 w08 w0a
    // c0c r0d target countdown, control; the control's +46 code, +53, +56;
    // FF0D60 as two words; FF31BC; FF31BE; free depth; walks.
    enum {fields=45};
    unsigned f[fields],cases=0,walks=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16},messages[5]={0xffffffff,0xd28c,0xd2a2,0xd20e,0xd22f};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid second ingredient case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete second ingredient case");
        for(unsigned i=0;i<11;++i)if(f[i]>((i==3 || i==7 || i==8) ? 255u : 65535u) || f[24+i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("second ingredient field outside range");
        const unsigned s=f[17],ao=f[18],t=f[19],c=f[20],h=f[21];
        const unsigned slots[5]={s,ao,t,c,h};
        for(unsigned i=0;i<5;++i){if(slots[i]>=68)fail("second ingredient slot outside pool");for(unsigned j=0;j<i;++j)if(slots[i]==slots[j])fail("second ingredient slots repeat");}
        if(f[12]>65535 || f[13]>65535 || f[14]>65535 || f[15]>65535 || f[16]>15 || f[22]>15 || f[23]>65535 || f[36]>4 || f[37]>255 || f[38]>65535 || f[39]>65535 || f[40]>65535
           || f[41]>65535 || f[42]>65535 || f[43]>64 || !f[44] || f[44]>64 || (f[11]!=0xffff0690u && f[11]!=0xffff0838u))fail("second ingredient context invalid");
        memset(ram,0xa5,sizeof ram);hit_stop=delivery_count=0;
        const unsigned a=0xffff1b50+78*s,aa=0xffff1b50+78*ao,ta=0xffff1b50+78*t,ca=0xffff1b50+78*c,ha=0xffff1b50+78*h,control=f[11],rec=0xff447a+12*f[16];
        memset(ram+(a&65535),0,78);
        for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(a+offsets[i],f[i]);else m68k_write_memory_16(a+offsets[i],f[i]);}
        m68k_write_memory_32(a+0x4a,control);m68k_write_memory_16(a+0x22,f[12]);m68k_write_memory_16(a+0x26,f[13]);m68k_write_memory_16(a+0x1e,f[14]);m68k_write_memory_16(a+0x20,f[15]);
        m68k_write_memory_32(a+0x42,0xffff0000u|rec);m68k_write_memory_32(a+0x16,0x12646);m68k_write_memory_32(a+0x46,0x12646);m68k_write_memory_32(a+0x1a,0x79b6);
        memset(ram+(aa&65535),0,78);m68k_write_memory_16(aa+0x32,f[23]); // The FF31AC object: only +32 is read.
        memset(ram+(ta&65535),0,78);m68k_write_memory_32(ta+0x16,0x12646);m68k_write_memory_32(ta+0x46,0x12646); // The dormant FF31B8 object.
        memset(ram+(ca&65535),0,78); // The FF31C0 anchor: a return-only object.
        for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(ca+offsets[i],f[24+i]);else m68k_write_memory_16(ca+offsets[i],f[24+i]);}
        m68k_write_memory_32(ca+0x4a,f[35]);m68k_write_memory_32(ca+0x16,0x12646);m68k_write_memory_32(ca+0x46,0x12646);
        m68k_write_memory_32(rec,ha);m68k_write_memory_32(rec+4,0xffff312c+2*f[22]);m68k_write_memory_32(rec+8,0xffff314c+2*f[22]);
        m68k_write_memory_32(0xff31ac,aa);m68k_write_memory_32(0xff31b0,0);m68k_write_memory_32(0xff31b4,aa);m68k_write_memory_32(0xff31b8,ta);m68k_write_memory_32(0xff31c0,ca);
        const unsigned m=control==0xffff0690u ? 0xff06d6 : 0xff087e; // +46; +53 and +56 follow.
        m68k_write_memory_32(m,messages[f[36]]);m68k_write_memory_8(m+0x0d,f[37]);m68k_write_memory_16(m+0x10,f[38]);
        m68k_write_memory_16(0xff0d60,f[39]);m68k_write_memory_16(0xff0d62,f[40]);m68k_write_memory_16(0xff31bc,f[41]);m68k_write_memory_16(0xff31be,f[42]);
        m68k_write_memory_16(0xff010c,0xa55a);
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth<f[43];++i)if(i!=s && i!=ao && i!=t && i!=c && i!=h)m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);message_vdp_count=0;message_lock_ok=1;
        unsigned copied[78];int at_copy=0;
        for(unsigned w=0;w<f[44] && !delivery_count;++w) {
            m68k_set_reg(M68K_REG_A6,a);call(0x69aa);++walks;
            if(m68k_get_reg(NULL,M68K_REG_A6)!=a)fail("second ingredient walk identity changed");
            if(delivery_count && !at_copy){for(unsigned i=0;i<78;++i)copied[i]=ram[(ta&65535)+i];at_copy=1;}
        }
        const unsigned called=delivery_count!=0,after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4,released=after==depth+1;
        if(delivery_count>1 || released!=called || (released && m68k_read_memory_32(0xff300c+4*depth)!=a) || (!released && after!=depth))fail("second ingredient free stack differs");
        if(m68k_read_memory_16(0xff010c)!=0xa55a)fail("second ingredient lock not restored");
        unsigned cleared=0,vram=0;
        if(message_vdp_count) {
            if(message_vdp_count!=30 || !message_lock_ok || message_vdp[0][0]!=0xc00004 || message_vdp[0][1]!=0x8004 || message_vdp[1][0]!=0xc00004 || message_vdp[2][0]!=0xc00006
               || message_vdp[29][0]!=0xc00004 || message_vdp[29][1]!=0x8014)fail("second ingredient VDP sequence differs");
            for(unsigned i=3;i<29;++i)if(message_vdp[i][0]!=0xc00000 || message_vdp[i][1]!=1)fail("second ingredient VDP data differs");
            const unsigned command=message_vdp[1][1]<<16 | message_vdp[2][1];
            if((command&0xc000fffc)!=0x40000000)fail("second ingredient VDP command differs");
            cleared=1;vram=(command>>16&0x3fff)|(command&3)<<14;
        }
        if(called) {
            // FB06 copied the called-back copy; FAA4 then cleared its mode and 7A88 moved it.
            for(unsigned i=1;i<78;++i) {
                const int moved=(i>=2 && i<6) || i==0x10 || i==0x11 || (i>=0x2e && i<0x34) || i==0x36 || i==0x37;
                if(!moved && copied[i]!=ram[(a&65535)+i])fail("second ingredient copy differs from the released copy");
            }
            if(copied[0]!=0x81 || ram[a&65535])fail("second ingredient copy modes differ");
            for(unsigned i=0;i<78;++i)if(copied[i]!=ram[(ta&65535)+i])fail("second ingredient target changed after the copy");
            if(m68k_read_memory_32(ca+0x16)!=0x7b42 || m68k_read_memory_32(ca+0x4a)!=control || m68k_read_memory_16(ca+0x10)!=0x012c)fail("second ingredient anchor differs");
            if(m68k_read_memory_32(0xff31b0)!=ta || m68k_read_memory_32(0xff31ac)!=aa || m68k_read_memory_32(rec)!=ta)fail("second ingredient identities differ");
        }
        for(unsigned x=0;x<65536;++x) {
            const unsigned o=(x-(a&65535)),q=(x-(ca&65535));
            const int mine=x>=(a&65535) && x<(a&65535)+78 && (o==0 || (o>=2 && o<0x0e) || o==0x10 || o==0x11 || (o>=0x16 && o<0x1a) || (o>=0x2e && o<0x34) || o==0x36 || o==0x37);
            const int target=called && x>=(ta&65535) && x<(ta&65535)+78;
            const int anchor=called && x>=(ca&65535) && x<(ca&65535)+78 && (q==0x10 || q==0x11 || (q>=0x16 && q<0x1a) || (q>=0x4a && q<0x4e));
            const int globals=called && ((x>=0x31b0 && x<0x31b4) || (x>=(rec&65535) && x<(rec&65535)+4) || (x>=(m&65535) && x<(m&65535)+4) || x==(m&65535)+0x0d);
            const int allowed=mine || target || anchor || globals || (x>=0x311c && x<0x3120) || (released && x>=0x300c+4*depth && x<0x3010+4*depth) || (x>=0xef00 && x<0xf004);
            if(!allowed && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("second ingredient walk changed an uncontracted byte");}
        }
        printf("1 %u %u",called,released);
        if(!called) {
            hit_fields(a);printf(" %u %u %u %u %u %u",m68k_read_memory_32(a+0x4a),m68k_read_memory_16(a+0x22),m68k_read_memory_16(a+0x26),m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20),hit_record(a));
        } else {
            table_print(a);table_print(ta);hit_fields(ca);printf(" %u",m68k_read_memory_32(ca+0x4a));
            const unsigned message=m68k_read_memory_32(m);unsigned code=99;for(unsigned k=0;k<5;++k)if(message==messages[k])code=k;
            if(code==99)fail("second ingredient message differs");
            printf(" %u %u %u %u %u %u %u %u",ao,t,t,(m68k_read_memory_32(rec+4)-0xffff312c)/2,code,m68k_read_memory_8(m+0x0d),m68k_read_memory_16(m+0x10),cleared);
            if(cleared)printf(" %u",vram);
            printf(" %u %u",m68k_read_memory_16(0xff31bc),m68k_read_memory_16(0xff31be));
        }
        printf(" %u\n",after);
    }
    if(ferror(stdin))fail("second ingredient input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"visited\":[",cases,walks,total_instructions);
}
static unsigned ram16(unsigned a) { return (unsigned)ram[a&65535]<<8 | ram[(a+1)&65535]; }
static unsigned ram32(unsigned a) { return ram16(a)<<16 | ram16(a+2); }
// FF0B90..FF0B97, FF0EDE, then curve pointers zero (no producer ran yet).
static void transition_seed(const unsigned *t) {
    for(unsigned i=0;i<4;++i)m68k_write_memory_16(0xff0b90+2*i,t[i]);
    for(unsigned i=0;i<3;++i)m68k_write_memory_32(0xff0b98+4*i,0);
    m68k_write_memory_16(0xff0ede,t[4]);
}
static void transition_print(void) {
    printf(" %u %u %u %u %u %u %u %u",ram16(0xff0b90),ram16(0xff0b92),ram16(0xff0b94),ram16(0xff0b96),ram32(0xff0b98),ram32(0xff0b9c),ram32(0xff0ba0),ram16(0xff0ede));
}
static int transition_byte(unsigned x) { return (x>=0x0b90 && x<0x0ba4) || x==0x0ede || x==0x0edf; }
static void anchor_cases(void) {
    // anchor x y flags mode w06 w08 w0a c0c r0d target countdown, control, slot,
    // walks, phase (0 7B42, 1 7B58, 2 7B8A), FF0B90 FF0B92 FF0B94 FF0B96, FF0EDE.
    enum {fields=20};
    unsigned f[fields],cases=0,walks=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16},handlers[3]={0x7b42,0x7b58,0x7b8a};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid anchor case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete anchor case");
        for(unsigned i=0;i<11;++i)if(f[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("anchor field outside range");
        if(f[12]>=68 || !f[13] || f[13]>512 || f[14]>2)fail("anchor context invalid");
        for(unsigned i=15;i<20;++i)if(f[i]>65535)fail("anchor timer outside range");
        memset(ram,0xa5,sizeof ram);hit_stop=0;
        const unsigned a=0xffff1b50+78*f[12];memset(ram+(a&65535),0,78);
        for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(a+offsets[i],f[i]);else m68k_write_memory_16(a+offsets[i],f[i]);}
        m68k_write_memory_32(a+0x4a,f[11]);m68k_write_memory_32(a+0x16,handlers[f[14]]);m68k_write_memory_32(a+0x46,0x12646);
        transition_seed(f+15);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        for(unsigned w=0;w<f[13] && !hit_stop;++w) {
            m68k_set_reg(M68K_REG_A6,a);call(0x69aa);++walks;
            if(!hit_stop && m68k_get_reg(NULL,M68K_REG_A6)!=a)fail("anchor walk identity changed");
        }
        for(unsigned x=0;x<65536;++x) {
            const unsigned o=x-(a&65535);
            const int mine=x>=(a&65535) && x<(a&65535)+78 && (o==0 || o==6 || o==7 || o==0x0c || o==0x10 || o==0x11 || (o>=0x16 && o<0x1a));
            if(!mine && !transition_byte(x) && !(x>=0xef00 && x<0xf004) && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("anchor walk changed an uncontracted byte");}
        }
        const unsigned h=m68k_read_memory_32(a+0x16);
        const unsigned phase=hit_stop ? 4 : h==0x7b42 ? 0 : h==0x7b58 ? 1 : h==0x7b8a ? 2 : h==0x12646 ? 3 : 99;
        if(phase==99 || (hit_stop && h!=0x7b58))fail("anchor handler differs");
        printf("%u",phase);hit_fields(a);printf(" %u",m68k_read_memory_32(a+0x4a));transition_print();printf("\n");
    }
    if(ferror(stdin))fail("anchor input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"visited\":[",cases,walks,total_instructions);
}
static unsigned char recipe_effects[0x10000];
static int recipe_stop(unsigned pc) { return pc<0x10000 && recipe_effects[pc]; }
static void table_seed(unsigned b, const unsigned *g, unsigned rec) {
    // x y w06 w08 w0a c0c r0d +10 +36 +32 cursor-index mode flags target control.
    const unsigned offsets[]={2,4,6,8,10,12,13,0x10,0x36,0x32,0x2e,0,0x12,0x0e,0x4a};
    memset(ram+(b&65535),0,78);
    for(unsigned i=0;i<15;++i) {
        const int byte=i==5 || i==6 || i==11,wide=i==14;
        if((byte && g[i]>255) || (!byte && !wide && g[i]>65535) || (i==10 && g[i]>=24))fail("completion table field outside range");
        if(i==10)m68k_write_memory_32(b+offsets[i],0x7a58+2*g[i]);else if(byte)m68k_write_memory_8(b+offsets[i],g[i]);else if(wide)m68k_write_memory_32(b+offsets[i],g[i]);else m68k_write_memory_16(b+offsets[i],g[i]);
    }
    m68k_write_memory_32(b+0x16,0x7a88);m68k_write_memory_32(b+0x46,0x12646);m68k_write_memory_32(b+0x1a,0x79b6);m68k_write_memory_32(b+0x42,0xffff0000u|rec);
}
static void completion_cases(void) {
    // anchor x y flags mode w06 w08 w0a c0c r0d target countdown, control; the
    // anchor, FF31AC and FF31B0 slots; both table objects (fifteen fields each);
    // their records and entries; FF31A8, FF316C, FF33E2, FF31A6, FF31A4; FF0690
    // +3C/+3E; the control's +46 code, +53, +56; FF0D60 as two words; free depth;
    // FF0B90 FF0B92 FF0B94 FF0B96, FF0EDE.
    enum {fields=67};
    unsigned f[fields],cases=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16},messages[6]={0xffffffff,0xd28c,0xd2a2,0xd20e,0xd22f,0xd269};
    for(unsigned a=0x83da;rom[a]!=0xff;a+=6){const unsigned e=rom[a+2]<<24|rom[a+3]<<16|rom[a+4]<<8|rom[a+5];if(e!=0x8652)recipe_effects[e]=1;}
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid completion case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete completion case");
        for(unsigned i=0;i<11;++i)if(f[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("completion anchor field outside range");
        const unsigned s=f[12],sa=f[13],sb=f[14];
        if(s>=68 || sa>=68 || sb>=68 || s==sa || s==sb || sa==sb || (f[11]!=0xffff0690u && f[11]!=0xffff0838u))fail("completion context invalid");
        if(f[45]>15 || f[46]>15 || f[47]>15 || f[48]>15 || f[45]==f[47] || f[56]>4 || f[57]>255 || f[61]>65)fail("completion context invalid");
        for(unsigned i=49;i<67;++i)if(i!=56 && i!=57 && i!=61 && f[i]>65535)fail("completion word outside range");
        memset(ram,0xa5,sizeof ram);hit_stop=completion_pops=completion_effect=0;sound_count=0;
        const unsigned a=0xffff1b50+78*s,aa=0xffff1b50+78*sa,ab=0xffff1b50+78*sb,control=f[11];
        const unsigned ra=0xff447a+12*f[45],rb=0xff447a+12*f[47];
        memset(ram+(a&65535),0,78);
        for(unsigned i=0;i<11;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(a+offsets[i],f[i]);else m68k_write_memory_16(a+offsets[i],f[i]);}
        m68k_write_memory_32(a+0x4a,control);m68k_write_memory_32(a+0x16,0x7b58);m68k_write_memory_32(a+0x46,0x12646);m68k_write_memory_32(a+0x1a,0xcaf0);
        table_seed(aa,f+15,ra);table_seed(ab,f+30,rb);
        for(unsigned r=0;r<16;++r)for(unsigned i=0;i<12;i+=4)m68k_write_memory_32(0xff447a+12*r+i,0);
        m68k_write_memory_32(ra,aa);m68k_write_memory_32(ra+4,0xffff312c+2*f[46]);m68k_write_memory_32(ra+8,0xffff314c+2*f[46]);
        m68k_write_memory_32(rb,ab);m68k_write_memory_32(rb+4,0xffff312c+2*f[48]);m68k_write_memory_32(rb+8,0xffff314c+2*f[48]);
        for(unsigned k=0;k<16;++k)m68k_write_memory_16(0xff312c+2*k,0x100+k);
        m68k_write_memory_16(0xff31a8,f[49]);m68k_write_memory_32(0xff31ac,aa);m68k_write_memory_32(0xff31b0,ab);
        m68k_write_memory_16(0xff316c,f[50]);m68k_write_memory_16(0xff33e2,f[51]);m68k_write_memory_16(0xff31a6,f[52]);m68k_write_memory_16(0xff31a4,f[53]);
        m68k_write_memory_16(0xff06cc,f[54]);m68k_write_memory_16(0xff06ce,f[55]);
        const unsigned m=control==0xffff0690u ? 0xff06d6 : 0xff087e; // +46; +53 and +56 follow.
        m68k_write_memory_32(m,messages[f[56]]);m68k_write_memory_8(m+0x0d,f[57]);m68k_write_memory_16(m+0x10,f[58]);
        m68k_write_memory_16(0xff0d60,f[59]);m68k_write_memory_16(0xff0d62,f[60]);m68k_write_memory_16(0xff010c,0xa55a);
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth<f[61];++i)if(i!=s && i!=sa && i!=sb)m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        transition_seed(f+62);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);message_vdp_count=0;message_lock_ok=1;
        m68k_set_reg(M68K_REG_A6,a);call(0x69aa);
        if(hit_stop){printf("2 %u\n",hit_stop);continue;}
        if(m68k_get_reg(NULL,M68K_REG_A6)!=a)fail("completion walk identity changed");
        if(m68k_read_memory_16(0xff010c)!=0xa55a)fail("completion lock not restored");
        const int completed=m68k_read_memory_32(a+0x16)==0x7b8a,after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4;
        if(completed!=(f[62]==0) || (!completed && m68k_read_memory_32(a+0x16)!=0x7b58))fail("completion handler differs");
        unsigned sparkle=0,sign=0,door=0,cleared=0,vram=0;
        if(completed) {
            if(after!=depth-3)fail("completion free stack differs");
            const unsigned p0=m68k_read_memory_32(0xff300c+4*(depth-1)),p1=m68k_read_memory_32(0xff300c+4*(depth-2)),p2=m68k_read_memory_32(0xff300c+4*(depth-3));
            sparkle=p0;sign=p1<p2 ? p1 : p2;door=p1<p2 ? p2 : p1;
            if(ram32(0xff316e)!=door || m68k_read_memory_32(door+0x36)!=sign || m68k_read_memory_32(door+0x4a)!=0xffff0690u || m68k_read_memory_32(door+0x16)!=0x6fb6
               || m68k_read_memory_32(sign+0x16)!=0x12646 || m68k_read_memory_32(sparkle+0x16)!=0x7f6a)fail("completion allocations differ");
            if(ram[aa&65535] || ram[ab&65535] || m68k_read_memory_32(ra) || m68k_read_memory_32(rb) || m68k_read_memory_32(0xff31ac) || m68k_read_memory_32(0xff31b0) || m68k_read_memory_16(0xff31a8))fail("completion ingredients not cleared");
            if(message_vdp_count) {
                if(message_vdp_count!=30 || !message_lock_ok || message_vdp[0][0]!=0xc00004 || message_vdp[0][1]!=0x8004 || message_vdp[1][0]!=0xc00004 || message_vdp[2][0]!=0xc00006
                   || message_vdp[29][0]!=0xc00004 || message_vdp[29][1]!=0x8014)fail("completion VDP sequence differs");
                for(unsigned i=3;i<29;++i)if(message_vdp[i][0]!=0xc00000 || message_vdp[i][1]!=1)fail("completion VDP data differs");
                const unsigned command=message_vdp[1][1]<<16 | message_vdp[2][1];
                if((command&0xc000fffc)!=0x40000000)fail("completion VDP command differs");
                cleared=1;vram=(command>>16&0x3fff)|(command&3)<<14;
            }
        } else if(after!=depth || sound_count || message_vdp_count)fail("waiting completion changed state");
        for(unsigned x=0;x<65536;++x) {
            const unsigned o=x-(a&65535);
            const int anchor=x>=(a&65535) && x<(a&65535)+78 && (o==0 || o==6 || o==7 || o==0x0c || (o>=0x16 && o<0x1a));
            const int made=completed && ((x>=(sparkle&65535) && x<(sparkle&65535)+78) || (x>=(sign&65535) && x<(sign&65535)+78) || (x>=(door&65535) && x<(door&65535)+78));
            const int state=completed && (x==(aa&65535) || x==(ab&65535) || (x>=(ra&65535) && x<(ra&65535)+4) || (x>=(rb&65535) && x<(rb&65535)+4)
                || (x>=0x312c+2*f[46] && x<0x312e + 2*f[46]) || (x>=0x312c+2*f[48] && x<0x312e + 2*f[48]) || (x>=0x31a8 && x<0x31b4) || (x>=0x31c4 && x<0x31c8)
                || (x>=0x316c && x<0x3172) || (x>=(m&65535) && x<(m&65535)+4) || x==(m&65535)+0x0d || (x>=0x0a9e && x<0x0aa6) || transition_byte(x) || (x>=0x311c && x<0x3120));
            if(!anchor && !made && !state && !(x>=0xef00 && x<0xf004) && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("completion walk changed an uncontracted byte");}
        }
        printf("%u",completed);hit_fields(a);printf(" %u",m68k_read_memory_32(a+0x4a));
        if(completed) {
            table_print(aa);table_print(ab);
            const unsigned message=m68k_read_memory_32(m);unsigned code=99;for(unsigned k=0;k<6;++k)if(message==messages[k])code=k;
            if(code==99)fail("completion message differs");
            printf(" %u %u %u %u %u %u %u %u",ram16(0xff312c+2*f[46]),ram16(0xff312c+2*f[48]),ram16(0xff31c4),ram16(0xff31c6),
                   code,m68k_read_memory_8(m+0x0d),m68k_read_memory_16(m+0x10),cleared);
            if(cleared)printf(" %u",vram);
            printf(" %u",sound_count);for(unsigned k=0;k<sound_count;++k)printf(" %u %u %u %u",sound_requests[k][0],sound_requests[k][1],sound_requests[k][2],sound_requests[k][3]);
            printf(" %u %u %u %u %u %u %u %u %u",(sparkle-0xffff1b50)/78,m68k_read_memory_16(sparkle+2),m68k_read_memory_16(sparkle+4),m68k_read_memory_16(sparkle+0x12),m68k_read_memory_8(sparkle),
                   m68k_read_memory_16(sparkle+6),m68k_read_memory_16(sparkle+0x10),m68k_read_memory_16(sparkle+0x1e),m68k_read_memory_16(sparkle+0x20));
            printf(" %u %u %u %u %u %u",(sign-0xffff1b50)/78,m68k_read_memory_16(sign+2),m68k_read_memory_16(sign+4),m68k_read_memory_16(sign+0x12),m68k_read_memory_8(sign),m68k_read_memory_16(sign+6));
            printf(" %u %u %u %u %u %u %u %u",(door-0xffff1b50)/78,m68k_read_memory_16(door+2),m68k_read_memory_16(door+4),m68k_read_memory_16(door+0x12),m68k_read_memory_8(door),
                   m68k_read_memory_16(door+6),m68k_read_memory_16(door+0x10),m68k_read_memory_32(door+0x4a));
            printf(" %u",m68k_read_memory_16(0xff316c));transition_print();
        }
        printf(" %u\n",after);
    }
    if(ferror(stdin))fail("completion input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void sparkle_cases(void) {
    // sparkle x y flags mode w06 +10 extents, E918 state (FF0BAC, FF0BAE), slot,
    // free depth, walks.
    enum {fields=13};
    unsigned f[fields],cases=0,walks=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid sparkle case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete sparkle case");
        for(unsigned i=0;i<10;++i)if(f[i]>(i==3 ? 255u : 65535u))fail("sparkle field outside range");
        if(f[10]>=68 || f[11]>67 || !f[12] || f[12]>96)fail("sparkle context invalid");
        memset(ram,0xa5,sizeof ram);hit_stop=0;spawn_count=0;
        const unsigned a=0xffff1b50+78*f[10];memset(ram+(a&65535),0,78);
        m68k_write_memory_16(a+2,f[0]);m68k_write_memory_16(a+4,f[1]);m68k_write_memory_16(a+0x12,f[2]);m68k_write_memory_8(a,f[3]);m68k_write_memory_16(a+6,f[4]);
        m68k_write_memory_16(a+0x10,f[5]);m68k_write_memory_16(a+0x1e,f[6]);m68k_write_memory_16(a+0x20,f[7]);
        m68k_write_memory_32(a+0x16,0x7f6a);m68k_write_memory_32(a+0x46,0x12646);m68k_write_memory_32(a+0x1a,0xcaf0);
        m68k_write_memory_16(0xff0bac,f[8]);m68k_write_memory_16(0xff0bae,f[9]);
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth<f[11];++i)if(i!=f[10])m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        unsigned w=0;
        for(;w<f[12] && !hit_stop;++w) {
            m68k_set_reg(M68K_REG_A6,a);call(0x69aa);++walks;
            if(!hit_stop && m68k_get_reg(NULL,M68K_REG_A6)!=a)fail("sparkle walk identity changed");
        }
        if(hit_stop){printf("1 %u\n",w);continue;}
        const unsigned after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4,released=!ram[a&65535];
        if(after!=depth-spawn_count+released)fail("sparkle free stack differs");
        for(unsigned k=0;k<spawn_count;++k){const unsigned q=spawned[k];if(m68k_read_memory_32(q+0x16)!=0x5ae2 || m68k_read_memory_32(q+0x1a)!=0xfaa4 || m68k_read_memory_32(q+0x46)!=0x12646 || m68k_read_memory_16(q+0x14))fail("sparkle particle differs");}
        for(unsigned x=0;x<65536;++x) {
            const unsigned o=x-(a&65535);int made=0;
            for(unsigned k=0;k<spawn_count;++k)if(x>=(spawned[k]&65535) && x<(spawned[k]&65535)+78)made=1;
            const int mine=x>=(a&65535) && x<(a&65535)+78 && (o==0 || o==6 || o==7 || o==0x0c || o==0x10 || o==0x11);
            if(!mine && !made && !(x>=0x0bac && x<0x0bb4) && !(x>=0x3008 && x<0x3120) && !(x>=0xef00 && x<0xf004) && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("sparkle walk changed an uncontracted byte");}
        }
        printf("0 %u %u %u %u %u %u %u %u",m68k_read_memory_16(a+2),m68k_read_memory_16(a+4),m68k_read_memory_16(a+0x12),m68k_read_memory_8(a),m68k_read_memory_16(a+6),
               m68k_read_memory_16(a+0x10),m68k_read_memory_16(a+0x1e),m68k_read_memory_16(a+0x20));
        printf(" %u %u %u",ram32(0xff0bac),ram32(0xff0bb0),spawn_count);
        for(unsigned k=0;k<spawn_count;++k){printf(" %u",((spawned[k]&65535)-0x1b50)/78);trail_particle_print(spawned[k]);}
        printf(" %u\n",after);
    }
    if(ferror(stdin))fail("sparkle input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"visited\":[",cases,walks,total_instructions);
}
static void door_cases(void) {
    // door x y flags mode w06 w08 w0a c0c r0d target +10 extents, phase (0 6FB6,
    // 1 appearing, 2 705C); sign x y flags mode w06 cursor, bobbing; door and
    // sign slots; FF0690 +42/+44; FF13AE; FF33E2; FF0690 +3A; walks; the +1A2
    // link's slot and mode; the FF31C0 anchor's slot (an inactive return-only
    // object); FF0836; FF444A/FF444C; FF0F00; P1's actor mode and +6; free depth.
    enum {fields=39};
    unsigned f[fields],cases=0,walks=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16,0x1e,0x20};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid door case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete door case");
        for(unsigned i=0;i<13;++i)if(f[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("door field outside range");
        for(unsigned i=14;i<20;++i)if(f[i]>(i==17 ? 255u : i==19 ? 13u : 65535u))fail("door sign field outside range");
        const unsigned slots[4]={f[21],f[22],f[29],f[31]};
        for(unsigned i=0;i<4;++i){if(slots[i]>=68)fail("door slot outside pool");for(unsigned j=0;j<i;++j)if(slots[i]==slots[j])fail("door slots repeat");}
        if(f[13]>2 || f[20]>1 || !f[28] || f[28]>96 || f[30]>255 || f[36]>255 || f[37]>65535 || f[38]>64)fail("door context invalid");
        for(unsigned i=23;i<28;++i)if(f[i]>65535)fail("door input outside range");
        if(f[32]>65535 || f[33]>65535 || f[34]>65535)fail("door word outside range");
        memset(ram,0xa5,sizeof ram);hit_stop=0;sound_count=0;
        const unsigned d=0xffff1b50+78*f[21],g=0xffff1b50+78*f[22],l=0xffff1b50+78*f[29],an=0xffff1b50+78*f[31],actor=0xffff1ab4;
        memset(ram+(d&65535),0,78);memset(ram+(g&65535),0,78);memset(ram+(l&65535),0,78);memset(ram+(an&65535),0,78);memset(ram+(actor&65535),0,78);
        for(unsigned i=0;i<13;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(d+offsets[i],f[i]);else m68k_write_memory_16(d+offsets[i],f[i]);}
        m68k_write_memory_32(d+0x16,f[13]==0 ? 0x6fb6 : 0x12646);m68k_write_memory_32(d+0x46,f[13]==2 ? 0x705c : 0x12646);
        m68k_write_memory_32(d+0x1a,f[13]==1 ? 0x6fca : 0xcaf0);m68k_write_memory_32(d+0x4a,0xffff0690);m68k_write_memory_32(d+0x36,g);if(f[13]==2)m68k_write_memory_32(d+0x3a,g);
        m68k_write_memory_16(g+2,f[14]);m68k_write_memory_16(g+4,f[15]);m68k_write_memory_16(g+0x12,f[16]);m68k_write_memory_8(g,f[17]);m68k_write_memory_16(g+6,f[18]);
        m68k_write_memory_32(g+0x16,f[20] ? 0x4c34 : 0x12646);m68k_write_memory_32(g+0x46,0x12646);m68k_write_memory_32(g+0x1a,0xcaf0);m68k_write_memory_32(g+0x22,0x4c52+2*f[19]);
        // The link: a return-only object whose presentation never steps (counter 0).
        m68k_write_memory_8(l,f[30]);m68k_write_memory_32(l+0x16,0x12646);m68k_write_memory_32(l+0x46,0x12646);
        m68k_write_memory_32(an+0x16,0x12646);m68k_write_memory_32(an+0x46,0x12646);
        m68k_write_memory_8(actor,f[36]);m68k_write_memory_16(actor+6,f[37]);m68k_write_memory_32(actor+0x16,0xa1be);m68k_write_memory_32(actor+0x4a,0xffff0690);
        m68k_write_memory_32(0xff0690,actor);m68k_write_memory_32(0xff0832,l);m68k_write_memory_16(0xff0836,f[32]);m68k_write_memory_32(0xff31c0,an);
        m68k_write_memory_16(0xff444a,f[33]);m68k_write_memory_16(0xff444c,f[34]);m68k_write_memory_32(0xff0f00,f[35]);
        m68k_write_memory_16(0xff06d2,f[23]);m68k_write_memory_16(0xff06d4,f[24]);m68k_write_memory_16(0xff13ae,f[25]);m68k_write_memory_16(0xff33e2,f[26]);m68k_write_memory_16(0xff06ca,f[27]);
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth<f[38];++i)if(i!=f[21] && i!=f[22] && i!=f[29] && i!=f[31])m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        const unsigned order[2]={d<g ? d : g,d<g ? g : d};int entered=0;
        for(unsigned w=0;w<f[28] && !hit_stop && !entered;++w)for(unsigned k=0;k<2 && !hit_stop;++k) {
            m68k_set_reg(M68K_REG_A6,order[k]);call(0x69aa);++walks;
            if(!hit_stop && m68k_get_reg(NULL,M68K_REG_A6)!=order[k])fail("door walk identity changed");
            if(!hit_stop && m68k_read_memory_32(d+0x46)==0x12646 && ram[d&65535]==0x85 && m68k_read_memory_32(d+0x1a)==0xfaa4)entered=1; // 7082 ran.
        }
        if(hit_stop){printf("1 %u\n",hit_stop);continue;}
        const unsigned after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4;
        if(after!=depth+entered || (entered && m68k_read_memory_32(0xff300c+4*depth)!=g))fail("door free stack differs");
        for(unsigned x=0;x<65536;++x) {
            const unsigned o=x-(d&65535),q=x-(g&65535),r=x-(an&65535);
            const int door=x>=(d&65535) && x<(d&65535)+78 && (o<0x22 || (o>=0x3a && o<0x3e) || (o>=0x46 && o<0x4a));
            const int sign=x>=(g&65535) && x<(g&65535)+78 && (q<8 || q==0x0c || (q>=0x16 && q<0x1a) || (q>=0x22 && q<0x26));
            const int exits=entered && ((x>=0x0f00 && x<0x0f04) || (x>=0x444a && x<0x444e) || x==0x0836 || x==0x0837 || x==0x1ab4 || x==0x1aba || x==0x1abb
                || (x>=0x1aca && x<0x1ace) || (x>=0x1afe && x<0x1b02) || (x>=(an&65535) && r>=0x16 && r<0x1a) || (x>=0x3008 && x<0x3120));
            if(!door && !sign && !exits && !(x>=0x0a9e && x<0x0aa6) && !(x>=0xef00 && x<0xf004) && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("door walk changed an uncontracted byte");}
        }
        const unsigned h=m68k_read_memory_32(d+0x16),v=m68k_read_memory_32(d+0x46),sh=m68k_read_memory_32(g+0x16);
        const unsigned phase=entered ? 3 : h==0x6fb6 ? 0 : h==0x12646 && v==0x12646 ? 1 : h==0x12646 && v==0x705c ? 2 : 99;
        if(phase==99 || (phase==2 && m68k_read_memory_32(d+0x3a)!=g) || (sh!=0x12646 && sh!=0x4c34))fail("door handlers differ");
        const unsigned cursor=m68k_read_memory_32(g+0x22);
        if(sh==0x4c34 && (cursor<0x4c52 || cursor>=0x4c6e || (cursor&1)))fail("door sign cursor differs");
        printf("0 %u",phase);
        if(entered)trail_particle_print(d);else{hit_fields(d);printf(" %u %u",m68k_read_memory_16(d+0x1e),m68k_read_memory_16(d+0x20));}
        printf(" %u %u %u %u %u %u %u",sh==0x4c34,m68k_read_memory_16(g+2),m68k_read_memory_16(g+4),m68k_read_memory_16(g+0x12),m68k_read_memory_8(g),m68k_read_memory_16(g+6),sh==0x4c34 ? (cursor-0x4c52)/2 : f[19]);
        printf(" %u",sound_count);for(unsigned k=0;k<sound_count;++k)printf(" %u %u %u %u",sound_requests[k][0],sound_requests[k][1],sound_requests[k][2],sound_requests[k][3]);
        if(entered)printf(" %u %u %u %u %u %u %u %u %u",ram32(0xff0f00),ram16(0xff444a),ram16(0xff444c),ram[0x1ab4],ram16(0xff1aba),ram32(0xff1aca),ram32(0xff1afe),ram16(0xff0836),m68k_read_memory_32(an+0x16));
        printf(" %u\n",after);
    }
    if(ferror(stdin))fail("door input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"visited\":[",cases,walks,total_instructions);
}
static void spell_mix_cases(void) {
    // FF31B0 present, FF31AC present, FF31BE, FF31BC, the FF31AC and FF31B0
    // objects' slots, then per object x y w06 w08 w0a c0c r0d +10 +36 +32
    // cursor-index mode flags target control.
    enum {fields=36,width=15};
    unsigned f[fields],cases=0;int first;
    const unsigned offsets[]={2,4,6,8,10,12,13,0x10,0x36,0x32,0x2e,0,0x12,0x0e,0x4a};
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid spell mix case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete spell mix case");
        if(f[0]>1 || f[1]>1 || f[2]>65535 || f[3]>65535 || f[4]>=68 || f[5]>=68 || f[4]==f[5])fail("spell mix context invalid");
        memset(ram,0xa5,sizeof ram);
        unsigned addr[2];
        for(unsigned k=0;k<2;++k) {
            const unsigned b=0xffff1b50+78*f[4+k],*g=f+6+width*k;addr[k]=b;memset(ram+(b&65535),0,78);
            for(unsigned i=0;i<width;++i) {
                const int byte=i==5 || i==6 || i==11,wide=i==14;
                if((byte && g[i]>255) || (!byte && !wide && g[i]>65535) || (i==10 && g[i]>=24))fail("spell mix field outside range");
                if(i==10)m68k_write_memory_32(b+offsets[i],0x7a58+2*g[i]);else if(byte)m68k_write_memory_8(b+offsets[i],g[i]);else if(wide)m68k_write_memory_32(b+offsets[i],g[i]);else m68k_write_memory_16(b+offsets[i],g[i]);
            }
            m68k_write_memory_32(b+0x16,0x7a88);m68k_write_memory_32(b+0x46,0x12646);m68k_write_memory_32(b+0x1a,0x79b6);
        }
        m68k_write_memory_32(0xff31ac,f[1] ? addr[0] : 0);m68k_write_memory_32(0xff31b0,f[0] ? addr[1] : 0);
        m68k_write_memory_16(0xff31be,f[2]);m68k_write_memory_16(0xff31bc,f[3]);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);call(0x7cc8);
        for(unsigned x=0;x<65536;++x) {
            int allowed=(x>=0x31bc && x<0x31c0) || (x>=0xef00 && x<0xf004);
            for(unsigned k=0;k<2;++k) {
                const unsigned o=x-(addr[k]&65535);
                if(x>=(addr[k]&65535) && x<(addr[k]&65535)+78 && ((o>=2 && o<0x0e) || o==0x10 || o==0x11 || (o>=0x2e && o<0x34) || o==0x36 || o==0x37))allowed=1;
            }
            if(!allowed && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("spell mix changed an uncontracted byte");}
        }
        printf("%u %u",m68k_read_memory_16(0xff31be),m68k_read_memory_16(0xff31bc));
        for(unsigned k=0;k<2;++k) for(unsigned i=0;i<width;++i) {
            const unsigned b=addr[k];
            if(i==10){const unsigned cursor=m68k_read_memory_32(b+0x2e);if(cursor<0x7a58 || cursor>=0x7a88 || (cursor&1))fail("spell mix cursor differs");printf(" %u",(cursor-0x7a58)/2);}
            else printf(" %u",(i==5 || i==6 || i==11) ? m68k_read_memory_8(b+offsets[i]) : i==14 ? m68k_read_memory_32(b+offsets[i]) : m68k_read_memory_16(b+offsets[i]));
        }
        printf("\n");
    }
    if(ferror(stdin))fail("spell mix input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static unsigned pool_slot(unsigned a) {
    a&=0xffffff;
    if(a<0xff1b50 || a>=0xff3008 || (a-0xff1b50)%78)fail("hub object pointer outside pool");
    return (a-0xff1b50)/78;
}
static void hub_doors_cases(void) {
    // FF33E2, FF33C4, FF33DE's seed byte; nine FF330C records of x y number
    // +6 state marker +C; the free depth and 68 slots bottom first.
    enum {fields=2+1+9*7+1+68};
    unsigned f[fields],cases=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid hub doors case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete hub doors case");
        if(f[0]>65535 || f[1]>65535 || f[2]>255 || f[66]>68)fail("hub doors context invalid");
        for(unsigned i=3;i<66;++i)if(f[i]>65535)fail("hub door record word outside range");
        unsigned used[68]={0};
        for(unsigned i=0;i<68;++i){if(f[67+i]>=68 || used[f[67+i]]++)fail("hub doors slot order is not a permutation");}
        memset(ram,0xa5,sizeof ram);hit_stop=0;
        for(unsigned r=0;r<9;++r)for(unsigned k=0;k<7;++k)m68k_write_memory_16(0xff330c+14*r+2*k,f[3+7*r+k]);
        m68k_write_memory_16(0xff33e2,f[0]);m68k_write_memory_16(0xff33c4,f[1]);m68k_write_memory_8(0xff33de,f[2]);
        const unsigned depth=f[66];m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<depth;++i)m68k_write_memory_32(0xff300c+4*i,0xffff1b50+78*f[67+i]);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);call(0x5e86);
        if(hit_stop){printf("1 %u\n",hit_stop);continue;}
        const unsigned head=m68k_read_memory_32(0xff311c);
        if(head<0xffff300c || head>0xffff300c+4*depth || (head-0xffff300c)%4)fail("hub doors free head differs");
        const unsigned pops=depth-(head-0xffff300c)/4;
        static unsigned char allowed[65536];memset(allowed,0,sizeof allowed);
        for(unsigned x=0xef00;x<0xf004;++x)allowed[x]=1;
        for(unsigned x=0x311c;x<0x3120;++x)allowed[x]=1;
        allowed[0x33de]=1;for(unsigned r=0;r<8;++r)allowed[(0x330c+14*r+8)&65535]=allowed[(0x330c+14*r+9)&65535]=1;
        printf("0 %u %u",ram[0x33de],pops);
        for(unsigned k=0;k<pops;++k) {
            const unsigned slot=f[67+depth-1-k],a=0xffff1b50+78*slot,o=a&65535;
            const unsigned h=m68k_read_memory_32(a+0x16),v=m68k_read_memory_32(a+0x46),w06=m68k_read_memory_16(a+6);
            if(v!=0x12646)fail("hub object service differs");
            const unsigned kind=h==0x61f6 ? 1 : h==0x12646 && w06==0xb0 ? 0 : h==0x12646 ? 2 : 99;
            if(kind==99)fail("hub object handler differs");
            const unsigned common[]={0,2,3,4,5,6,7,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x46,0x47,0x48,0x49};
            for(unsigned i=0;i<sizeof common/sizeof common[0];++i)allowed[o+common[i]]=1;
            printf(" %u %u %u %u %u %u %u %u",slot,kind,ram[o],m68k_read_memory_16(a+2),m68k_read_memory_16(a+4),w06,m68k_read_memory_16(a+0x12),m68k_read_memory_16(a+0x14));
            if(kind<2) {
                for(unsigned i=0x22;i<0x2e;++i)if(i<0x24 || i>=0x26)allowed[o+i]=1;
                printf(" %u %u %u",m68k_read_memory_16(a+0x22),pool_slot(m68k_read_memory_32(a+0x26)),pool_slot(m68k_read_memory_32(a+0x2a)));
            }
            if(kind==1) {
                for(unsigned i=8;i<0x0e;++i)allowed[o+i]=1;
                allowed[o+0x10]=allowed[o+0x11]=1;
                printf(" %u %u %u %u %u",m68k_read_memory_16(a+8),m68k_read_memory_16(a+10),ram[o+12],ram[o+13],m68k_read_memory_16(a+0x10));
            }
        }
        for(unsigned r=0;r<9;++r)printf(" %u",m68k_read_memory_16(0xff330c+14*r+8));
        printf("\n");
        for(unsigned x=0;x<65536;++x)if(!allowed[x] && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("hub setup changed an uncontracted byte");}
    }
    if(ferror(stdin))fail("hub doors input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void hub_door_cases(void) {
    // door x y flags mode w06 w08 w0a c0c r0d target +10 extents number, phase
    // (0 closed, 1 61F6, 2 621A, 3 FAC4, 4 FAE2); the left/right number slots and
    // modes; the door slot; FF0690/FF0838 +42/+44; FF13AE; FF33E2; walks; free
    // depth; both +1A6; FF4446/FF4448; FF3398; FF0B90..FF0B96, the three curve
    // longs and FF0EDE; both actors' mode and +6; both message blocks (+46 +4E
    // +52 +53 +54 +56 +58).
    enum {fields=59};
    unsigned f[fields],cases=0,walks=0;int first;
    const unsigned offsets[]={2,4,18,0,6,8,10,12,13,14,16,0x1e,0x20,0x22};
    const unsigned handlers[5][3]={{0x12646,0x12646,0xcaf0},{0x61f6,0x12646,0xcaf0},{0x6218,0x621a,0xcaf0},{0xfac4,0x6218,0xfaa4},{0xfae2,0x6218,0xfaa4}};
    const unsigned controls[2]={0xff0690,0xff0838},actors[2]={0xff1ab4,0xff1b02},selectors[2]={0xff0836,0xff09de};
    collision_secondary=1; // FF0838's +42/+44 are always supplied.
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid hub door case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete hub door case");
        for(unsigned i=0;i<14;++i)if(f[i]>((i==3 || i==7 || i==8) ? 255u : 65535u))fail("hub door field outside range");
        const unsigned slots[3]={f[19],f[15],f[16]};
        for(unsigned i=0;i<3;++i){if(slots[i]>=68)fail("hub door slot outside pool");for(unsigned j=0;j<i;++j)if(slots[i]==slots[j])fail("hub door slots repeat");}
        if(f[14]>4 || f[17]>255 || f[18]>255 || !f[26] || f[26]>96 || f[27]>64)fail("hub door context invalid");
        for(unsigned i=20;i<32;++i)if(i!=26 && i!=27 && f[i]>65535)fail("hub door word outside range");
        for(unsigned i=33;i<37;++i)if(f[i]>65535)fail("hub door timer word outside range");
        if(f[40]>65535 || f[41]>255 || f[42]>65535 || f[43]>255 || f[44]>65535)fail("hub door context word outside range");
        for(unsigned k=0;k<2;++k)if(f[47+7*k]>255 || f[48+7*k]>255 || f[49+7*k]>65535 || f[50+7*k]>65535 || f[51+7*k]>65535)fail("hub door message field outside range");
        memset(ram,0xa5,sizeof ram);hit_stop=0;hub_entries=0;hub_touched=0;
        const unsigned d=0xffff1b50+78*f[19],nl=0xffff1b50+78*f[15],nr=0xffff1b50+78*f[16];
        memset(ram+(d&65535),0,78);memset(ram+(nl&65535),0,78);memset(ram+(nr&65535),0,78);
        for(unsigned i=0;i<14;++i){if(i==3 || i==7 || i==8)m68k_write_memory_8(d+offsets[i],f[i]);else m68k_write_memory_16(d+offsets[i],f[i]);}
        m68k_write_memory_32(d+0x16,handlers[f[14]][0]);m68k_write_memory_32(d+0x46,handlers[f[14]][1]);m68k_write_memory_32(d+0x1a,handlers[f[14]][2]);
        m68k_write_memory_32(d+0x26,nl);m68k_write_memory_32(d+0x2a,nr);
        for(unsigned k=0;k<2;++k) {
            const unsigned n=k ? nr : nl;
            m68k_write_memory_8(n,f[17+k]);m68k_write_memory_32(n+0x16,0x12646);m68k_write_memory_32(n+0x46,0x12646);m68k_write_memory_32(n+0x1a,0xcaf0);
            const unsigned c=controls[k],a=actors[k],*m=f+45+7*k;
            m68k_write_memory_32(c,a);m68k_write_memory_16(c+0x42,f[20+2*k]);m68k_write_memory_16(c+0x44,f[21+2*k]);m68k_write_memory_16(selectors[k],f[28+k]);
            m68k_write_memory_32(c+0x46,m[0]);m68k_write_memory_32(c+0x4e,m[1]);m68k_write_memory_8(c+0x52,m[2]);m68k_write_memory_8(c+0x53,m[3]);
            m68k_write_memory_16(c+0x54,m[4]);m68k_write_memory_16(c+0x56,m[5]);m68k_write_memory_16(c+0x58,m[6]);
            memset(ram+(a&65535),0,78);m68k_write_memory_8(a,f[41+2*k]);m68k_write_memory_16(a+6,f[42+2*k]);m68k_write_memory_32(a+0x16,0xa1be);m68k_write_memory_32(a+0x4a,c);
        }
        m68k_write_memory_16(0xff13ae,f[24]);m68k_write_memory_16(0xff33e2,f[25]);
        m68k_write_memory_16(0xff4446,f[30]);m68k_write_memory_16(0xff4448,f[31]);m68k_write_memory_32(0xff3398,f[32]);
        for(unsigned i=0;i<4;++i)m68k_write_memory_16(0xff0b90+2*i,f[33+i]);
        for(unsigned i=0;i<3;++i)m68k_write_memory_32(0xff0b98+4*i,f[37+i]);
        m68k_write_memory_16(0xff0ede,f[40]);
        unsigned depth=0;m68k_write_memory_32(0xff3008,0);
        for(unsigned i=0;i<68 && depth<f[27];++i)if(i!=f[19] && i!=f[15] && i!=f[16])m68k_write_memory_32(0xff300c+4*depth++,0xffff1b50+78*i);
        m68k_write_memory_32(0xff311c,0xffff300c+4*depth);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        int revived=0;
        for(unsigned w=0;w<f[26] && !hit_stop && !hub_entries && !revived;++w) {
            m68k_set_reg(M68K_REG_A6,d);call(0x5f5e);++walks;
            if(!hit_stop && m68k_get_reg(NULL,M68K_REG_A6)!=d)fail("hub door walk identity changed");
            // FAC4 after the presentation's FAA4: an active object on the free stack.
            const unsigned top=(m68k_read_memory_32(0xff311c)-0xffff300c)/4;
            for(unsigned i=depth;i<top;++i)if(m68k_read_memory_32(0xff300c+4*i)==d && (ram[d&65535]&0x80))revived=1;
        }
        if(hub_entries>1)fail("hub door entered twice");
        if(hit_stop){printf("1 %u\n",hit_stop);continue;}
        if(revived){printf("1 %u\n",0xfac4u);continue;}
        const int entered=hub_entries!=0;
        const unsigned after=(m68k_read_memory_32(0xff311c)-0xffff300c)/4;
        const int released=!(ram[d&65535]&0x80) && after>depth && m68k_read_memory_32(0xff300c+4*depth)==d;
        if(after!=depth+2*entered+released)fail("hub door free stack differs");
        if(entered && (m68k_read_memory_32(0xff300c+4*depth)!=nl || m68k_read_memory_32(0xff300c+4*depth+4)!=nr))fail("hub door number pushes differ");
        static unsigned char allowed[65536];memset(allowed,0,sizeof allowed);
        for(unsigned x=0xef00;x<0xf004;++x)allowed[x]=1;
        for(unsigned x=0x3008;x<0x3120;++x)allowed[x]=1;
        const unsigned o=d&65535;
        for(unsigned i=0;i<0x12;++i)if(i!=1)allowed[o+i]=1;
        for(unsigned i=0x16;i<0x22;++i)allowed[o+i]=1;
        for(unsigned i=0x46;i<0x4a;++i)allowed[o+i]=1;
        if(entered) {
            allowed[nl&65535]=allowed[nr&65535]=1;
            for(unsigned k=0;k<2;++k){
                const unsigned c=controls[k]&65535,a=actors[k]&65535;
                for(unsigned i=0x46;i<0x5a;++i)allowed[c+i]=1;
                allowed[selectors[k]&65535]=allowed[(selectors[k]&65535)+1]=1;
                allowed[a]=allowed[a+6]=allowed[a+7]=1;for(unsigned i=0x16;i<0x1a;++i)allowed[a+i]=1;
            }
            for(unsigned x=0x4446;x<0x444a;++x)allowed[x]=1;
            for(unsigned x=0x3398;x<0x339c;++x)allowed[x]=1;
            for(unsigned x=0x0b90;x<0x0ba4;++x)allowed[x]=1;
            allowed[0x0ede]=allowed[0x0edf]=1;
        }
        for(unsigned x=0;x<65536;++x)if(!allowed[x] && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("hub door walk changed an uncontracted byte");}
        const unsigned h=m68k_read_memory_32(d+0x16),v=m68k_read_memory_32(d+0x46),cb=m68k_read_memory_32(d+0x1a);
        unsigned phase=99;
        for(unsigned k=0;k<5;++k)if(h==handlers[k][0] && v==handlers[k][1] && cb==handlers[k][2])phase=k;
        if(phase==99)fail("hub door handlers differ");
        printf("0 %u",phase);
        for(unsigned i=0;i<14;++i)printf(" %u",(i==3 || i==7 || i==8) ? m68k_read_memory_8(d+offsets[i]) : m68k_read_memory_16(d+offsets[i]));
        printf(" %u %u %u %u",ram[nl&65535],ram[nr&65535],after,entered);
        if(entered) {
            if(hub_touched!=0xffff0690 && hub_touched!=0xffff0838)fail("hub door touching control differs");
            printf(" %u %u %u %u",hub_touched==0xffff0838,ram16(0xff4446),ram16(0xff4448),ram32(0xff3398));
            // Direct RAM reads: the harness's own observation, outside the fixture's read scope.
            for(unsigned i=0;i<4;++i)printf(" %u",ram16(0xff0b90+2*i));
            for(unsigned i=0;i<3;++i)printf(" %u",ram32(0xff0b98+4*i));
            printf(" %u",ram16(0xff0ede));
            for(unsigned k=0;k<2;++k){
                const unsigned c=controls[k],a=actors[k];
                printf(" %u %u %u %u",ram16(selectors[k]),ram[a&65535],ram16(a+6),ram32(a+0x16));
                printf(" %u %u %u %u %u %u %u",ram32(c+0x46),ram32(c+0x4e),ram[(c+0x52)&65535],ram[(c+0x53)&65535],ram16(c+0x54),ram16(c+0x56),ram16(c+0x58));
            }
        }
        printf("\n");
    }
    if(ferror(stdin))fail("hub door input failure");
    fprintf(stderr,"{\"cases\":%u,\"walks\":%u,\"instructions\":%u,\"visited\":[",cases,walks,total_instructions);
}
static void hub_exit_cases(void) {
    // FF0690's +1A6 (FF0836) and FF0B90.
    unsigned f[2],cases=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000 || scanf("%u",&f[1])!=1 || f[0]>65535 || f[1]>65535)fail("invalid hub exit case");
        memset(ram,0xa5,sizeof ram);hit_stop=0;
        m68k_write_memory_16(0xff0836,f[0]);m68k_write_memory_16(0xff0b90,f[1]);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);call(0x6024);
        printf("%u\n",hit_stop ? 0u : 1u); // 603E's RTS ends the scene; 603A's BRA continues the loop.
    }
    if(ferror(stdin))fail("hub exit input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void scene_change_cases(void) {
    // FF4446/FF4448, FF0838's +A2/+A4, each control's +30, FF33E2, FF13E0, a fill seed.
    enum {fields=9};
    // Control words written here that are not native (camera, HUD, messages, render).
    static const unsigned research[]={8,9,10,11,12,13,14,15,0x18,0x19,0x3a,0x3b,0x68,0x69,0xf2,0xf3,0x108,0x109,0x10a,0x10b,0x11a,0x11b,0x144,0x145,0x16e,0x16f};
    const unsigned controls[2]={0xff0690,0xff0838},actors[2]={0xff1ab4,0xff1b02};
    const unsigned params[9]={0x5a,0x5c,0x5e,0x60,0x62,0x64,0x66,0x6a,0x6c};
    unsigned f[fields],cases=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid scene change case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete scene change case");
        for(unsigned i=0;i<fields;++i)if(f[i]>65535)fail("scene change field outside range");
        unsigned seed=f[8]*2654435761u+1;
        for(unsigned x=0;x<65536;++x){seed=seed*1103515245u+12345u;ram[x]=(unsigned char)(seed>>16);}
        m68k_write_memory_16(0xff4446,f[0]);m68k_write_memory_16(0xff4448,f[1]);m68k_write_memory_16(0xff0838+0xa2,f[2]);m68k_write_memory_16(0xff0838+0xa4,f[3]);
        m68k_write_memory_16(0xff0690+0x30,f[4]);m68k_write_memory_16(0xff0838+0x30,f[5]);m68k_write_memory_16(0xff33e2,f[6]);m68k_write_memory_16(0xff13e0,f[7]);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        const unsigned order[]={0x488,0x17024,0xf850,0x16fb4,0x16ff8,0x9880,0x17284,0x5d6a,0x5ed4};
        for(unsigned k=0;k<sizeof order/sizeof order[0];++k)call(order[k]);
        static unsigned char allowed[65536];memset(allowed,0,sizeof allowed);
        for(unsigned x=0xef00;x<0xf004;++x)allowed[x]=1;
        for(unsigned x=0x1ab4;x<0x3120;++x)allowed[x]=1; // Actors, pool, free stack: compared below.
        for(unsigned x=0x0b90;x<0x0ba4;++x)allowed[x]=1;
        allowed[0x0ede]=allowed[0x0edf]=allowed[0x0f16]=allowed[0x0f17]=1;
        for(unsigned x=0x148c;x<0x1494;++x)allowed[x]=1;
        for(unsigned x=0x17ac;x<0x17b4;++x)allowed[x]=1;
        for(unsigned x=0x1aa8;x<0x1ab2;++x)allowed[x]=1;
        for(unsigned k=0;k<2;++k) {
            const unsigned c=controls[k]&65535;
            for(unsigned i=0;i<sizeof research/sizeof research[0];++i)allowed[c+research[i]]=1;
            for(unsigned i=0x46;i<0x5a;++i)allowed[c+i]=1;   // 17298's message fields.
            for(unsigned i=0x96;i<0xaa;++i)allowed[c+i]=1;   // 1737E/991E's camera words and 0x488's +A2/+A4.
            for(unsigned i=0xb2;i<0xba;++i)allowed[c+i]=1;   // 1737E's +B2/+B4, 9952's +B6, +B8.
            for(unsigned i=0;i<9;++i)allowed[c+params[i]]=allowed[c+params[i]+1]=1;
            allowed[c+0x1a6]=allowed[c+0x1a7]=1;
            for(unsigned i=0;i<4;++i)allowed[c+i]=1; // F940's actor pointer, compared below.
        }
        for(unsigned x=0;x<65536;++x)if(!allowed[x] && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("scene change changed an uncontracted byte");}
        for(unsigned k=0;k<2;++k) {
            const unsigned a=actors[k],c=controls[k];
            const unsigned offsets[]={2,4,6,8,10,14,16,18,0x22,0x26,0x2a};
            printf(k ? " %u" : "%u",ram[a&65535]);
            for(unsigned i=0;i<11;++i)printf(" %u",ram16(a+offsets[i]));
            printf(" %u %u %u %u %u %u",ram[(a+12)&65535],ram[(a+13)&65535],ram32(a+0x16),ram32(a+0x1a),ram32(a+0x46),ram32(a+0x4a));
            for(unsigned i=0;i<78;++i)if(!(i==0 || (i>=2 && i<0x14) || (i>=0x16 && i<0x1e) || (i>=0x22 && i<0x2c) || (i>=0x46 && i<0x4e)) && ram[(a+i)&65535])fail("scene change left actor residue");
            printf(" %u %u",ram32(c),ram16(c+0x1a6));
            for(unsigned i=0;i<9;++i)printf(" %u",ram16(c+params[i]));
        }
        for(unsigned i=0;i<4;++i)printf(" %u",ram16(0xff0b90+2*i));
        for(unsigned i=0;i<3;++i)printf(" %u",ram32(0xff0b98+4*i));
        printf(" %u %u",ram16(0xff0ede),ram16(0xff0f16));
        unsigned reset=0;
        for(unsigned i=0;i<68;++i){
            const unsigned b=(0x1b50+78*i)&65535;int ok=ram32(0xff0000|(b+0x16))==0x12646 && ram32(0xff0000|(b+0x46))==0x12646;
            for(unsigned j=0;j<78;++j)if(!((j>=0x16 && j<0x1a) || (j>=0x46 && j<0x4a)) && ram[b+j])ok=0;
            reset+=ok;
        }
        const unsigned head=ram32(0xff311c),depth=(head-0xffff300c)/4;int ascending=ram32(0xff3008)==0 && head>=0xffff300c && (head-0xffff300c)%4==0 && depth<=68;
        for(unsigned i=0;ascending && i<depth;++i)if(ram32(0xff300c+4*i)!=0xffff1b50+78*i)ascending=0;
        printf(" %u %u %u\n",reset,depth,ascending);
    }
    if(ferror(stdin))fail("scene change input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void second_level_cases(void) {
    // FF0838's +A2/+A4, each control's +30, FF33E2, FF13E0, FF3402, E918's state and mirror, a fill seed.
    enum {fields=12};
    static const unsigned research[]={8,9,10,11,12,13,14,15,0x18,0x19,0x3a,0x3b,0x68,0x69,0xf2,0xf3,0x108,0x109,0x10a,0x10b};
    const unsigned controls[2]={0xff0690,0xff0838},actors[2]={0xff1ab4,0xff1b02};
    const unsigned params[9]={0x5a,0x5c,0x5e,0x60,0x62,0x64,0x66,0x6a,0x6c};
    unsigned f[fields],cases=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid second level case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete second level case");
        for(unsigned i=0;i<fields;++i)if(f[i]>65535)fail("second level field outside range");
        unsigned seed=f[11]*2654435761u+1;
        for(unsigned x=0;x<65536;++x){seed=seed*1103515245u+12345u;ram[x]=(unsigned char)(seed>>16);}
        m68k_write_memory_16(0xff0838+0xa2,f[0]);m68k_write_memory_16(0xff0838+0xa4,f[1]);m68k_write_memory_16(0xff0690+0x30,f[2]);m68k_write_memory_16(0xff0838+0x30,f[3]);
        m68k_write_memory_16(0xff33e2,f[4]);m68k_write_memory_16(0xff13e0,f[5]);m68k_write_memory_16(0xff3402,f[6]);
        m68k_write_memory_16(0xff0bac,f[7]);m68k_write_memory_16(0xff0bae,f[8]);m68k_write_memory_16(0xff0bb0,f[9]);m68k_write_memory_16(0xff0bb2,f[10]);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);
        const unsigned order[]={0x17024,0xf850,0x16fb4,0x16ff8,0xe44,0x9880,0x11a6,0x1356,0x774};
        for(unsigned k=0;k<sizeof order/sizeof order[0];++k) {
            if(order[k]==0x11a6 || order[k]==0x1356)m68k_set_reg(M68K_REG_A5,0xffff0690); // 118C's A5 (0x76A).
            call(order[k]);
        }
        static unsigned char allowed[65536];memset(allowed,0,sizeof allowed);
        for(unsigned x=0xef00;x<0xf004;++x)allowed[x]=1;
        for(unsigned x=0x1ab4;x<0x3120;++x)allowed[x]=1; // Actors, pool, free stack: compared below.
        for(unsigned x=0x0b90;x<0x0ba4;++x)allowed[x]=1;
        for(unsigned x=0x0bac;x<0x0bb4;++x)allowed[x]=1;
        allowed[0x0ede]=allowed[0x0edf]=allowed[0x0f16]=allowed[0x0f17]=1;
        allowed[0x33d8]=allowed[0x33d9]=allowed[0x33e0]=allowed[0x33e1]=1;
        allowed[0x33ce]=allowed[0x33cf]=allowed[0x33e4]=allowed[0x33e5]=1; // Research-only: FF33CE cleared, FF33E4 = 1.
        for(unsigned x=0x148c;x<0x1494;++x)allowed[x]=1;
        for(unsigned x=0x17ac;x<0x17b4;++x)allowed[x]=1;
        for(unsigned x=0x1aa8;x<0x1ab2;++x)allowed[x]=1;
        for(unsigned k=0;k<2;++k) {
            const unsigned c=controls[k]&65535;
            for(unsigned i=0;i<sizeof research/sizeof research[0];++i)allowed[c+research[i]]=1;
            for(unsigned i=0x96;i<0xaa;++i)allowed[c+i]=1;   // 1737E/991E's camera words and E2A's +A2/+A4.
            for(unsigned i=0xb2;i<0xba;++i)allowed[c+i]=1;   // 1737E's +B2/+B4, 9952's +B6, +B8.
            for(unsigned i=0;i<9;++i)allowed[c+params[i]]=allowed[c+params[i]+1]=1;
            allowed[c+0x1a6]=allowed[c+0x1a7]=1;
            for(unsigned i=0;i<4;++i)allowed[c+i]=1; // F940's actor pointer, compared below.
        }
        for(unsigned x=0;x<65536;++x)if(!allowed[x] && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("second level entry changed an uncontracted byte");}
        for(unsigned k=0;k<2;++k) {
            const unsigned a=actors[k],c=controls[k];
            const unsigned offsets[]={2,4,6,8,10,14,16,18,0x22,0x26,0x2a};
            printf(k ? " %u" : "%u",ram[a&65535]);
            for(unsigned i=0;i<11;++i)printf(" %u",ram16(a+offsets[i]));
            printf(" %u %u %u %u %u %u",ram[(a+12)&65535],ram[(a+13)&65535],ram32(a+0x16),ram32(a+0x1a),ram32(a+0x46),ram32(a+0x4a));
            for(unsigned i=0;i<78;++i)if(!(i==0 || (i>=2 && i<0x14) || (i>=0x16 && i<0x1e) || (i>=0x22 && i<0x2c) || (i>=0x46 && i<0x4e)) && ram[(a+i)&65535])fail("second level entry left actor residue");
            printf(" %u %u",ram32(c),ram16(c+0x1a6));
            for(unsigned i=0;i<9;++i)printf(" %u",ram16(c+params[i]));
        }
        for(unsigned i=0;i<4;++i)printf(" %u",ram16(0xff0b90+2*i));
        for(unsigned i=0;i<3;++i)printf(" %u",ram32(0xff0b98+4*i));
        printf(" %u %u",ram16(0xff0ede),ram16(0xff0f16));
        unsigned reset=0;
        for(unsigned i=0;i<68;++i){
            const unsigned b=(0x1b50+78*i)&65535;int ok=ram32(0xff0000|(b+0x16))==0x12646 && ram32(0xff0000|(b+0x46))==0x12646;
            for(unsigned j=0;j<78;++j)if(!((j>=0x16 && j<0x1a) || (j>=0x46 && j<0x4a)) && ram[b+j])ok=0;
            reset+=ok;
        }
        const unsigned head=ram32(0xff311c),depth=(head-0xffff300c)/4;int ascending=ram32(0xff3008)==0 && head>=0xffff300c && (head-0xffff300c)%4==0 && depth<=68;
        for(unsigned i=0;ascending && i<depth;++i)if(ram32(0xff300c+4*i)!=0xffff1b50+78*i)ascending=0;
        printf(" %u %u %u %u %u %u %u\n",reset,depth,ascending,ram16(0xff33d8),ram16(0xff33e0),ram32(0xff0bac),ram32(0xff0bb0));
    }
    if(ferror(stdin))fail("second level input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
static void hint_screen_cases(void) {
    // FF0B90..FF0B97, FF0EDE, FF0F10, FF0F0E, FF0690's +14, +1E, +1F, +20, a fill seed.
    enum {fields=12};
    unsigned f[fields],cases=0;int first;
    while((first=scanf("%u",&f[0]))!=EOF) {
        if(first!=1 || ++cases>1000000)fail("invalid hint screen case");
        for(unsigned i=1;i<fields;++i)if(scanf("%u",&f[i])!=1)fail("incomplete hint screen case");
        for(unsigned i=0;i<fields;++i)if(f[i]>65535 || (i>=7 && i<11 && f[i]>255))fail("hint screen field outside range");
        unsigned seed=f[11]*2654435761u+1;
        for(unsigned x=0;x<65536;++x){seed=seed*1103515245u+12345u;ram[x]=(unsigned char)(seed>>16);}
        for(unsigned i=0;i<4;++i)m68k_write_memory_16(0xff0b90+2*i,f[i]);
        for(unsigned i=0;i<3;++i)m68k_write_memory_32(0xff0b98+4*i,0x135ea); // Distinct from 13208's curves.
        m68k_write_memory_16(0xff0ede,f[4]);m68k_write_memory_16(0xff0f10,f[5]);m68k_write_memory_16(0xff0f0e,f[6]);
        m68k_write_memory_8(0xff06a4,f[7]);m68k_write_memory_8(0xff06ae,f[8]);m68k_write_memory_8(0xff06af,f[9]);m68k_write_memory_8(0xff06b0,f[10]);
        static unsigned char before[65536];memcpy(before,ram,sizeof ram);
        for(unsigned reg=M68K_REG_D0;reg<=M68K_REG_A6;++reg)m68k_set_reg(reg,0x5a5a0000u+reg);
        m68k_set_reg(M68K_REG_SR,0x2700);m68k_set_reg(M68K_REG_A5,0xffff0690); // 19720's A5.
        if(!f[6])call(0x14e3c);
        call(f[6] ? 0x1975a : 0x1972e);
        static unsigned char allowed[65536];memset(allowed,0,sizeof allowed);
        for(unsigned x=0xef00;x<0xf004;++x)allowed[x]=1;
        for(unsigned x=0x0b90;x<0x0ba4;++x)allowed[x]=1;
        allowed[0x0ede]=allowed[0x0edf]=allowed[0x0f0e]=allowed[0x0f0f]=allowed[0x0f10]=allowed[0x0f11]=allowed[0x06a6]=1;
        for(unsigned x=0;x<65536;++x)if(!allowed[x] && ram[x]!=before[x]){fprintf(stderr,"case %u address FF%04X\n",cases,x);fail("hint screen changed an uncontracted byte");}
        printf("%u",!boundary_stop_seen);
        for(unsigned i=0;i<4;++i)printf(" %u",ram16(0xff0b90+2*i));
        for(unsigned i=0;i<3;++i)printf(" %u",ram32(0xff0b98+4*i));
        printf(" %u %u %u %u\n",ram16(0xff0ede),ram16(0xff0f0e),ram16(0xff0f10),f[6] ? 0u : (unsigned)ram[0x06a6]);
    }
    if(ferror(stdin))fail("hint screen input failure");
    fprintf(stderr,"{\"cases\":%u,\"instructions\":%u,\"visited\":[",cases,total_instructions);
}
int main(int argc, char **argv) {
    if(argc==3 && (!strcmp(argv[2],"--probe-hit") || !strcmp(argv[2],"--delivered") || !strcmp(argv[2],"--ingredient") || !strcmp(argv[2],"--second-ingredient") || !strcmp(argv[2],"--anchor")
                   || !strcmp(argv[2],"--completion") || !strcmp(argv[2],"--sparkle") || !strcmp(argv[2],"--door"))) {
        hit_mode=!strcmp(argv[2],"--probe-hit") ? 2 : !strcmp(argv[2],"--delivered") ? 3 : !strcmp(argv[2],"--ingredient") ? 4 : !strcmp(argv[2],"--second-ingredient") ? 5
            : !strcmp(argv[2],"--completion") ? 7 : !strcmp(argv[2],"--sparkle") ? 8 : !strcmp(argv[2],"--door") ? 9 : 6;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);
        if(hit_mode==2)probe_hit_cases();else if(hit_mode==3)delivered_cases();else if(hit_mode==4)ingredient_cases();else if(hit_mode==5)second_ingredient_cases();else if(hit_mode==7)completion_cases();else if(hit_mode==8)sparkle_cases();else if(hit_mode==9)door_cases();else anchor_cases();
        goto finish;
    }
    if(argc==3 && (!strcmp(argv[2],"--second-level") || !strcmp(argv[2],"--hint-screen"))) {
        hit_mode=!strcmp(argv[2],"--second-level") ? 14 : 15;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);
        if(hit_mode==14)second_level_cases();else hint_screen_cases();
        goto finish;
    }
    if(argc==3 && (!strcmp(argv[2],"--hub-doors") || !strcmp(argv[2],"--hub-door") || !strcmp(argv[2],"--hub-exit") || !strcmp(argv[2],"--scene-change"))) {
        hit_mode=!strcmp(argv[2],"--hub-doors") ? 10 : !strcmp(argv[2],"--hub-door") ? 11 : !strcmp(argv[2],"--hub-exit") ? 12 : 13;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);
        if(hit_mode==10)hub_doors_cases();else if(hit_mode==11)hub_door_cases();else if(hit_mode==12)hub_exit_cases();else scene_change_cases();
        goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--spell-mix")) {
        table_mode=4;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);spell_mix_cases();goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--pickup-hit")) {
        hit_mode=1;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);pickup_hit_cases();goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--setup-pairs")) {
        pair_mode=8;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);pairs_cases();goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--setup-message")) {
        pair_mode=7;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);message_cases();goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--setup-tail")) {
        pair_mode=6;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);tail_cases();goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--setup-prefix")) {
        pair_mode=5;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);prefix_cases();goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--collision-quad")) {
        pair_mode=4;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);quad_cases();goto finish;
    }
    if(argc==3 && (!strcmp(argv[2],"--pair-initializer") || !strcmp(argv[2],"--visibility-pair") || !strcmp(argv[2],"--rising-pair"))) {
        pair_mode=!strcmp(argv[2],"--pair-initializer") ? 1 : !strcmp(argv[2],"--visibility-pair") ? 2 : 3;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);pair_cases();goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--return-only")) {
        return_only_mode=1;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);return_only_cases();goto finish;
    }
    if(argc==3 && (!strcmp(argv[2],"--overlap") || !strcmp(argv[2],"--collision-service") || !strcmp(argv[2],"--collision-scheduled") || !strcmp(argv[2],"--pickup-service") || !strcmp(argv[2],"--pickup-scheduled"))) {
        collision_mode=!strcmp(argv[2],"--overlap") ? 1 : !strcmp(argv[2],"--collision-service") ? 2 : !strcmp(argv[2],"--collision-scheduled") ? 3 : !strcmp(argv[2],"--pickup-service") ? 4 : 5;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);collision_cases();goto finish;
    }
    if(argc==3 && !strcmp(argv[2],"--table-writers")) {
        table_mode=3;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);table_writer_cases();goto finish;
    }
    if(argc==3 && (!strcmp(argv[2],"--table-motion") || !strcmp(argv[2],"--table-motion-scheduled"))) {
        table_mode=!strcmp(argv[2],"--table-motion") ? 1 : 2;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);table_cases();goto finish;
    }
    if(argc==3 && (!strcmp(argv[2],"--private") || !strcmp(argv[2],"--private-scheduled"))) {
        private_mode=!strcmp(argv[2],"--private") ? 1 : 2;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);private_cases();goto finish;
    }
    if(argc==3 && (!strcmp(argv[2],"--trail") || !strcmp(argv[2],"--trail-scheduled") || !strcmp(argv[2],"--trail-particle") || !strcmp(argv[2],"--trail-rng") || !strcmp(argv[2],"--trail-spawn"))) {
        trail_mode=!strcmp(argv[2],"--trail") ? 1 : !strcmp(argv[2],"--trail-scheduled") ? 2 : !strcmp(argv[2],"--trail-particle") ? 3 : !strcmp(argv[2],"--trail-rng") ? 4 : 5;
        if(load(argv[1],rom,sizeof rom)!=sizeof rom)fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();m68k_set_instr_hook_callback(hook);trail_cases();goto finish;
    }
    if (argc==3 && (!strcmp(argv[2],"--pad") || !strcmp(argv[2],"--banner"))) {
        pad_conversion=!strcmp(argv[2],"--pad");level_banner=!strcmp(argv[2],"--banner");
        if (load(argv[1],rom,sizeof rom)!=sizeof rom) fail("ROM extent mismatch");
        m68k_init();m68k_set_cpu_type(M68K_CPU_TYPE_68000);m68k_pulse_reset();
        if (m68k_get_reg(NULL,M68K_REG_CPU_TYPE)!=M68K_CPU_TYPE_68000) fail("wrong CPU");
        m68k_set_instr_hook_callback(hook);if (level_banner) banner_cases();else pad_cases();goto finish;
    }

    if (argc != 5 && !(argc == 6 && (!strcmp(argv[5],"--score") || !strcmp(argv[5],"--exit-tally") || !strcmp(argv[5],"--bonus") || !strcmp(argv[5],"--palette") || !strcmp(argv[5],"--tally") || !strcmp(argv[5],"--coast-entry") || !strcmp(argv[5],"--transition") || !strcmp(argv[5],"--transition-timer") || !strcmp(argv[5],"--dispatch") || !strcmp(argv[5],"--actions") || !strcmp(argv[5],"--actions-scheduled") || !strcmp(argv[5],"--actions-presentation") || !strcmp(argv[5],"--movement") || !strcmp(argv[5],"--airborne") || !strcmp(argv[5],"--actor") || !strcmp(argv[5],"--presentation") || !strcmp(argv[5],"--scheduled") || !strcmp(argv[5],"--reversal") || !strcmp(argv[5],"--reversal-scheduled") || !strcmp(argv[5],"--effect") || !strcmp(argv[5],"--reversal-empty")))) fail("usage: terrain-reference ROM MAP RECORDS BASE [--movement|--airborne|--actor|--presentation|--scheduled|--reversal|--reversal-scheduled|--reversal-empty|--effect]");
    movement = argc == 6;
    score = movement && !strcmp(argv[5],"--score");
    exit_tally = score || movement && !strcmp(argv[5],"--exit-tally");
    bonus = movement && !strcmp(argv[5],"--bonus");
    palette = movement && !strcmp(argv[5],"--palette");
    tally = exit_tally || bonus || palette || movement && !strcmp(argv[5],"--tally");
    coast_entry = movement && !strcmp(argv[5],"--coast-entry");
    transition_timer = movement && !strcmp(argv[5],"--transition-timer");
    transition = tally || coast_entry || transition_timer || (movement && !strcmp(argv[5],"--transition"));
    dispatch = transition || (movement && !strcmp(argv[5],"--dispatch"));
    actions = transition || (movement && (!strcmp(argv[5],"--dispatch") || !strcmp(argv[5],"--actions") || !strcmp(argv[5],"--actions-scheduled") || !strcmp(argv[5],"--actions-presentation")));
    empty_pool = movement && !strcmp(argv[5],"--reversal-empty");
    reversal = movement && (empty_pool || !strcmp(argv[5],"--reversal") || !strcmp(argv[5],"--reversal-scheduled") || !strcmp(argv[5],"--effect"));
    effect_mode = movement && !strcmp(argv[5],"--effect");
    scheduling = dispatch ? 3 : !movement ? 0 : (!strcmp(argv[5],"--presentation") || !strcmp(argv[5],"--actions-presentation") || effect_mode) ? 1 : (!strcmp(argv[5],"--scheduled") || !strcmp(argv[5],"--actions-scheduled") || !strcmp(argv[5],"--reversal-scheduled")) ? 2 : 0;
    controller = movement && (scheduling || reversal || actions || !strcmp(argv[5],"--actor"));
    airborne = controller || (movement && !strcmp(argv[5],"--airborne"));
    char *end; unsigned long value = strtoul(argv[4], &end, 10);
    if (*end || value > 2047) fail("invalid base"); base = (unsigned)value;
    if (load(argv[1], rom, sizeof rom) != sizeof rom) fail("ROM extent mismatch");
    if (load(argv[2], ram + 0x4d02, 8192) != 8192) fail("map extent mismatch");
    record_size = load(argv[3], ram + 0x8000, 16384);
    if (!record_size || record_size % 8 || record_size / 8 + base > 2048) fail("record extent/base mismatch");
    m68k_write_memory_32(0xff4452, 0xffff4d02);
    m68k_write_memory_32(0xff444e, 0xffff8000 - base * 8);
    m68k_write_memory_16(0xff13a4, 256);
    m68k_write_memory_16(0xff13ae, 1023);
    m68k_write_memory_16(0xff140e, base);
    m68k_init(); m68k_set_cpu_type(M68K_CPU_TYPE_68000); m68k_pulse_reset();
    if (m68k_get_reg(NULL, M68K_REG_CPU_TYPE) != M68K_CPU_TYPE_68000) fail("wrong CPU");
    m68k_set_instr_hook_callback(hook);
    if (effect_mode) { effect_cases(); goto finish; }
    if (controller) { actor_cases(); goto finish; }
    if (airborne) { airborne_cases(); goto finish; }
    if (movement) { movement_cases(); goto finish; }
    unsigned mode, x, y, sx, sy, cases = 0;
    int fields;
    while ((fields = scanf("%u %u %u %u %u", &mode, &x, &y, &sx, &sy)) == 5) {
        if (++cases > 1000000 || mode > 4 || x > 65535 || y > 65535 || sx > 65535 || sy > 65535)
            fail("invalid reference case");
        for (int reg = M68K_REG_D0; reg <= M68K_REG_A6; ++reg) m68k_set_reg(reg, 0x5a5a0000u + (unsigned)reg);
        m68k_set_reg(M68K_REG_SR, 0x2710);
        m68k_set_reg(M68K_REG_D0, x); m68k_set_reg(M68K_REG_D1, y);
        m68k_set_reg(M68K_REG_A6, 0xffff0690);
        m68k_write_memory_16(0xff0692, x); m68k_write_memory_16(0xff0694, y);
        m68k_write_memory_16(0xff4442, sx); m68k_write_memory_16(0xff4444, sy);
        if (!mode) { call(0x99d4); call(0x9a18); }
        else { const unsigned entries[] = {0,0x9b34,0x9b5c,0x9b84,0x9a80}; call(entries[mode]); }
        if (m68k_get_reg(NULL, M68K_REG_D2) != 0x5a5a0002) fail("D2 preservation failed");
        unsigned relative = (tile & 2047) - base;
        if (relative >= record_size / 8) fail("reference tile cannot normalize");
        printf("%u %u %u %u %u %u %u %u\n", m68k_read_memory_16(0xff0692),
            m68k_read_memory_16(0xff0694), m68k_read_memory_16(0xff4442), m68k_read_memory_16(0xff4444),
            m68k_get_reg(NULL, M68K_REG_D0) & 255, mode ? m68k_get_reg(NULL, M68K_REG_D1) & 65535 : 0,
            m68k_get_reg(NULL, M68K_REG_SR) & 15, (tile & 0xf800) | relative);
    }
    if (fields != EOF || ferror(stdin) || fflush(stdout) || ferror(stdout)) fail("reference transport failure");
    fprintf(stderr, "{\"cases\":%u,\"instructions\":%u,\"visited\":[", cases, total_instructions);
finish:
    if (fflush(stdout) || ferror(stdout)) fail("reference output failure");
    int first = 1;
    for (unsigned pc = 0; pc < 1048576; ++pc) if (visits[pc]) { fprintf(stderr, "%s%u", first ? "" : ",", pc); first = 0; }
    fprintf(stderr, "]}\n");
    return 0;
}
