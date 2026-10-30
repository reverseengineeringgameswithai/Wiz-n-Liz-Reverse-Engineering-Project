#pragma once
#include "sim/session.hpp"
#include "sim/trail.hpp"
#include "sim/private_object.hpp"
#include "sim/table_motion.hpp"
#include "sim/collision_probe.hpp"
#include "sim/return_only.hpp"
#include "sim/gated_pair.hpp"
#include "sim/spell.hpp"
#include "sim/hub.hpp"
#include <variant>

namespace wiz::sim {
// Explicit occupancy projection: the caller has established that this object's
// omitted private work cannot change this pool, RNG, owner or session inputs.
// This is not an unknown handler treated as a successful native invocation.
struct ExternalReservation {};
using PoolObject = std::variant<std::monostate,ExternalReservation,ReversalEffect,TrailParticle,TrailEmitter,PrivateObject,TableMotion,CollisionProbe,ReturnOnlyObject,Pickup,GatedLead,DeliveredPickup,SpellCountdown,
    SpellSparkle,ExitDoor,DoorSign,HubDoor>;
// Only a free slot may carry inherited fields, and only from verified seed
// evidence. Any allocation clears them; a released slot's residue is unknown.
struct PoolSlot { PoolObject object; std::uint64_t generation{}; std::optional<InheritedObjectFields> inherited{}; };
enum class PoolEventKind { spawn, update, release, inactive };
struct PoolEvent { PoolEventKind kind; EffectId id; PoolObject object; };
// Messages posted through CB72, all ROM strings: 7DB8's D28C ("MIX THOSE
// FRUIT!") and D2A2 ("FRUIT RETURNED!"), priority byte 0x64, and callback79B6's
// D20E ("FIRST INGREDIENT COLLECTED!") and D22F ("SECOND INGREDIENT
// COLLECTED!"), priority byte 0x01.
enum class SetupMessage : std::uint8_t { mix_those_fruit, fruit_returned, first_ingredient, second_ingredient, spell_completed };
// A control record's +46 (message, or FFFFFFFF when absent), +53 (signed
// priority byte) and +56 (message row word).
struct ControlMessage {
    std::optional<SetupMessage> message{};
    std::uint8_t priority{};
    std::uint16_t row{};
    bool operator==(const ControlMessage&) const = default;
};
// CB9A as a logical render request: 26 tiles of value 1 written from VRAM word
// address `vram` (tilemap base + 14 + row << 7, low 16 bits). No VDP is native.
struct MessageRowClear {
    std::uint16_t vram{};
    bool operator==(const MessageRowClear&) const = default;
};
// CB72 with +46 already set to `text`: a priority below the stored +53 (signed
// bytes) leaves +46 = FFFFFFFF; otherwise +53 takes it and CB9A clears the
// message row of the FF0D60 tilemap.
std::optional<MessageRowClear> post_message(ControlMessage& message, SetupMessage text, std::uint32_t tilemap) noexcept;
// What a 6C00 or 7910 hit, the 6CF4 re-dress and a delivered copy's 79B6
// callback read and write besides the pool; none is produced natively here.
// The logical FF0690/FF0838 controls a contact selects, their +1A2 links, the
// FF447A records, the FF312C kinds (read through a record) and the FCB32
// requests made, in order. 7910 reads only the controls and links and makes
// requests. 79B6 and 7AD6 use FF31AC (`activation`), the FF31B4/FF31B8 dormant
// objects, the controls' message fields, the FF0D60 tilemap, the records and
// FF31BE (`ingredient_timer`), and request CB9A row clears; 7AD6's second path
// also names FF31B0 (`spell`) and gives the FF31C0 anchor (`anchor`) 7B42. The
// spell's completion (7B58's 7E18 and recipe 8652) reads FF31A8 (`spell_flags`),
// FF316C (`pair_request`), FF33E2 (`two_player`) and FF0690's +3C/+3E
// (`control_origin`), and writes FF31C4/FF31C6 (`recipe`), FF316C and FF316E
// (`door`). Entering the door (7082) writes FF0F00 (`exit_control`) and
// FF444A/FF444C (`exit_camera`) and leaves `door_entered` for the session, which
// hands P1 to its 710E exit handler after the loop.
struct PickupWorld {
    std::array<ActorId,2> controls{};
    std::array<std::optional<EffectId>,2> links{};
    std::array<std::optional<PickupRecord>,16> records{};
    std::array<std::uint16_t,16> kinds{};
    std::vector<SoundRequest> sounds{};
    std::optional<EffectId> activation{};
    std::array<std::optional<EffectId>,2> dormant{};
    std::array<std::optional<ControlMessage>,2> messages{};
    std::uint32_t message_tilemap{};
    std::uint16_t ingredient_timer{};
    std::vector<MessageRowClear> clears{};
    std::optional<EffectId> anchor{}, spell{};
    std::uint16_t spell_flags{}, pair_request{};
    bool two_player{};
    Position control_origin{};
    std::optional<std::array<std::uint16_t,2>> recipe{};
    std::optional<EffectId> door{};
    std::optional<ActorId> exit_control{};
    std::optional<Position> exit_camera{};
    bool door_entered{};
};
// The scene between levels after its setup: the FF330C door records, FF33E2
// (`two_player`) and FF3398 (`selected`: FF330C + 0E * number, as the number
// 623C stored). FF4446/FF4448 are the session timer's requested position.
// `entry` is 623C's work outside the pool, left for the session after the
// loop: 17298 on the touching control's message fields (not carried here),
// and 630A on both controls (the session applies P1's).
struct HubEntry { std::size_t control{}; std::uint16_t number{}; };
struct HubWorld {
    HubDoorTable table{};
    bool two_player{};
    std::optional<std::uint16_t> selected{};
    std::optional<HubEntry> entry{};
};
// The two 7910 allocations: the 59AE sparkle (F9E2) and the copy (F994).
struct DeliveryIds { EffectId sparkle, copy; };
class MixedPool {
public:
    // Ascending slot order and bottom-to-top free stack are caller-owned logical
    // identities. Bounds are host safety limits, not a fixed original RAM pool.
    MixedPool(std::vector<PoolObject> objects, std::vector<std::size_t> free_stack,
        std::vector<std::optional<InheritedObjectFields>> inherited = {});
    EffectId spawn(ReversalEffect effect);
    EffectId spawn(TrailParticle particle);
    // 7B9C / 7C26: two ordered F9E2 pops from this shared LIFO stack, each typed
    // over that slot's verified inherited fields. 7B9C's second member is the
    // FF31C0 identity; 7C26 stores no identity. Exhaustion or unknown
    // inheritance rejects with no allocation; the original instead loops
    // forever at FA1E, so no failure value is invented.
    ObjectPair initialize_return_only_pair();
    ObjectPair initialize_visibility_pair();
    // 7772: the caller's control identity is stored in both rising members.
    ObjectPair initialize_rising_pair(ActorId control);
    // 783A: four ordered pops. The first is a 78EE collision probe storing the
    // caller's control; the others are return-only objects placed from it.
    // Every member keeps +08..+0D, target and countdown, so each popped slot
    // must carry verified inherited presentation as well as the other fields.
    ObjectQuad initialize_collision_quad(ActorId control);
    // 6EC8 / 6EDC: one pop left dormant (mode 0) over a slot whose inherited
    // position and presentation are verified. The stored identity is the
    // caller's concern (see the session API below).
    EffectId initialize_dormant();
    // 6AF0 for one table entry: one pop typed as a pickup over a slot whose
    // inherited target is verified.
    EffectId initialize_pickup(ActorId control, Position at, std::uint16_t kind, std::uint16_t count, std::size_t record);
    // 7FBE / 7154 / 735E / 7568 open: two ordered pops, then CMPA.L/BLT/EXG
    // orders them by address (ascending slot order here). The lower becomes a
    // return-only partner, the higher a lead naming it. Both keep +08..+0D, so
    // each popped slot must carry verified inherited presentation.
    GatedPairIds initialize_gated_pair(GatedPair pair, ActorId control, Position p2_origin);
    // One scheduled pickup walk (walk_pickup) with its 6C00 hit. A contact
    // requests sound 0089/0006/00C0/0001; frame +08 of 20D/205/1FD rejects
    // (6E32/6E8A/6E5E are not native). The touching control's link decides: a
    // dormant return-only link becomes the carrying emitter (6D22) and the
    // pickup vanishes to release; an active carrying emitter exchanges with the
    // pickup (6C50), which vanishes and returns. The records follow both.
    // Everything, including `world`, commits together; returns the release.
    bool walk_pickup(EffectId id, const CollisionInputs& inputs, PickupWorld& world);
    // One scheduled walk of a 78EE probe with its 7910 hit. A contact returns at
    // once while the FF31B0 rise gate (a long) is nonzero, and with the touching
    // control's link dormant (mode byte zero). An active carrying emitter link
    // requests 008C/0006/00C0/0001, then pops the 59AE sparkle and the F994 copy
    // from the shared stack in that order, and the link is left dormant (see
    // deliver_carried). Exhaustion (the original's endless FA1E or F9D0 loop),
    // any other link and an emitter without carried bytes reject. 7910 writes no
    // FF447A record: its +42 store writes back the value just copied. Everything,
    // including `world`, commits together.
    std::optional<DeliveryIds> walk_probe(EffectId id, const CollisionInputs& inputs, std::uint32_t rise_gate, PickupWorld& world);
    // One scheduled walk of a delivered copy with its 79B6 callback: X + 8,
    // Y + 4, frames back from +22/+26, mode 81 with 6BB2's cadence, the 7A88
    // table handler at cursor 0 with +36 = 0 and +10 = 000E. With FF31AC absent
    // (the first ingredient) +32 = FFFF, D20E is posted to the copy's control
    // through CB72, 7AD6 makes the dormant FF31B4 object that table object
    // (FB06), names it in FF31AC and the copy's record, releases the copy (FAA4)
    // and FF31BE = 0050, FF31BC = 0. With FF31AC present (the second) +32 is
    // the negated +32 of the FF31AC table object, D22F is posted, 7AD6 copies
    // into the dormant FF31B8 object, names it in FF31B0 (the rise gate becomes
    // nonzero) and the record, releases the copy and turns the FF31C0 anchor
    // into a SpellCountdown (+4A the copy's control, +10 = 012C); FF31BE/FF31BC
    // are untouched. The walk then runs 7A88 on the released copy with FF31BC.
    // A missing or non-dormant target, a missing anchor, record, control
    // message or globals reject. Everything, including `globals` and `world`,
    // commits together; returns the release.
    bool walk_delivered(EffectId id, PrivateGlobals& globals, PickupWorld& world);
    // 7CC8, called once per frame before P1's last input conversion. With FF31B0
    // absent nothing changes. Otherwise FF31BE decrements as a word; a negative
    // result increments FF31BC (word wrap) and reloads FF31BE = 0028. Then, with
    // FF31AC present too, the two table objects exchange frames, counter/reload,
    // +10, +36, +32, the cursor and position when the FF31AC object's +32 is
    // non-negative and the FF31B0 object lies at a lower address, or its +32 is
    // negative and the FF31B0 object lies higher. A missing FF31BC or a
    // non-table object rejects. Everything commits together.
    void mix_spell(PickupWorld& world, PrivateGlobals* globals);
    // One walk of the FF31C0 anchor as MixedPool::step makes it (7B42, 13294,
    // 7B58 with the completion, 7B8A); returns the walk's spawns. Everything,
    // including `world`, `globals` and `timer`, commits together.
    std::vector<PoolEvent> walk_anchor(EffectId id, PickupWorld& world, PrivateGlobals& globals, TransitionState& timer);
    // One walk of 7F08's sparkle (7F6A) with the shared RNG; returns its spawn
    // and release events. Everything commits together.
    std::vector<PoolEvent> walk_sparkle(EffectId id, TrailRandom& random);
    // 60E6: eight records (nine with `two_player`) in order, each through 611E:
    // the door (F9E2), 6334's left and right number objects (F994, F994), then
    // for a closed record the lock (F9E2) and, with two players and +A
    // non-negative, the partner (F9E2). Returns every identity in pop order.
    // All pops commit together; exhaustion (the original's endless FA1E or
    // F9D0 loop) or a number outside the 639A table rejects with no change.
    std::vector<EffectId> initialize_hub_doors(const HubDoorTable& table, bool two_player);
    const PoolSlot& at(EffectId id) const;
    const std::vector<PoolSlot>& slots() const noexcept { return slots_; }
    const std::vector<std::size_t>& free_stack() const noexcept { return free_; }
    std::size_t available() const noexcept { return free_.size(); }
    // One forward walk: later-slot births participate; earlier-slot births wait.
    // Release preserves final state and pushes the slot before later allocation.
    // The entire phase and RNG roll back on any failure.
    // Dormant return-only objects emit an inactive observation, consume no
    // update budget, and remain occupied with the same generation.
    // Pickups and 78EE probes use `pickups` for their hits and re-dress (probes
    // also need `globals` for FF31B0), delivered copies for their 79B6
    // callback; without it a contact or that callback rejects as before.
    // `globals` is shared state: 79B6's FF31BC store reaches later objects of
    // the phase, and it commits with the phase.
    // `transition` is the session's 1345A timer, which the FF31C0 anchor's 13294
    // and 1324E start; it commits with the phase.
    // Hub doors need `hub` and `collision`; their 623C also needs `transition`.
    std::vector<PoolEvent> step(ActorId owner, Position position, TrailRandom& random, std::size_t budget, PrivateGlobals* globals = nullptr,
        const CollisionInputs* collision = nullptr, PickupWorld* pickups = nullptr, TransitionState* transition = nullptr, HubWorld* hub = nullptr);
private:
    EffectId allocate(PoolObject object);
    PoolSlot& slot_at(EffectId id);
    bool walk_pickup_slot(std::size_t i, const CollisionInputs& inputs, PickupWorld* world);
    std::optional<DeliveryIds> walk_probe_slot(std::size_t i, const CollisionInputs& inputs, const std::uint32_t* rise_gate, PickupWorld* world);
    bool walk_delivered_slot(std::size_t i, PrivateGlobals* globals, PickupWorld* world);
    // 7B58 once FF0B90 is zero: D269 through CB72, 7E18 (both ingredients
    // deactivated by 7ED6, their records cleared and FF312C entries FFFF,
    // FF31A8/FF31B0/FF31AC cleared, the 83DA lookup, sound 9C, the effect and
    // 95EE), 1324E and +16 = 7B8A. Only recipe 8652 is native: 7F08's sparkle
    // (sound 90), FF316C = FFFF and 6F02's sign and door.
    void complete_spell(std::size_t i, PickupWorld& world, PrivateGlobals& globals, TransitionState& timer, std::vector<PoolEvent>& events);
    void walk_anchor_slot(std::size_t i, PickupWorld* world, PrivateGlobals* globals, TransitionState* timer, std::vector<PoolEvent>& events);
    // 705C's contact (7082): FF0F00, the FF31C0 anchor's 12646, 4CA2 (FAA4 on the
    // door's +3A sign, then the door's vanish and move), the single-player
    // camera words and `door_entered`; an active +1A2 link (70FE) rejects.
    void enter_exit_door(std::size_t i, PickupWorld& world, std::vector<PoolEvent>& events);
    bool walk_sparkle_slot(std::size_t i, TrailRandom& random, std::vector<PoolEvent>& events);
    // 623C for the control `touched` (0 FF0690, 1 FF0838): `entry` (17298 and
    // 630A for the session), FF4446/FF4448 into the timer's requested position,
    // FF3398, the door's vanish, FA8C on its +26 then +2A number objects (each
    // pushed; a number object no longer live rejects) and 13208 on the timer.
    void enter_hub_door(std::size_t i, std::size_t touched, HubWorld& hub, TransitionState* timer, std::vector<PoolEvent>& events);
    // Shared F9E2 template: N ordered pops, all-or-nothing. `needs` names the
    // inherited parts beyond target/countdown/link each slot must verify.
    template<std::size_t N, class Make> std::array<EffectId,N> initialize_group(Make make, const char* exhausted, const char* unknown, InheritanceNeeds needs);
    template<class Make> ObjectPair initialize_pair(Make make, const char* exhausted, const char* unknown);
    std::vector<PoolSlot> slots_;
    std::vector<std::size_t> free_;
};
// FF33E2 (two players), FF31AA (fruit returned), FF316C (6EF0 pair request) and
// the FF0D60 message tilemap base.
struct SetupGates {
    std::uint16_t two_player{}, fruit_returned{}, pair_request{};
    std::uint32_t message_tilemap{};
};
// What 7DB8 selected, and CB72's render request when the priority accepted it.
struct SetupMessageResult {
    std::optional<SetupMessage> selected{};
    std::optional<MessageRowClear> clear{};
};
// [68C4,68D4) explicit inputs, none produced natively: the FF3172 / FF3174 /
// FF3176 / FF3178 gate words (7FBE, 7154, 735E, 7568), the FF0838 control's
// +3C/+3E words (read only behind the first gate), the caller's A5 (stored by
// 7FBE) and the logical FF0690 control (stored by the other three).
struct GatedPairInputs {
    std::array<std::uint16_t,4> gates{};
    std::optional<Position> p2_origin{};
    ActorId caller, p1_control;
};
// Every identity [68C4,68D4) produces, by gate; closed gates create nothing.
struct LevelSetupPairs { std::array<std::optional<GatedPairIds>,4> pairs{}; };
struct MixedSessionState {
    P1SessionState p1;
    MixedPool pool;
    TrailRandom random;
    std::optional<PrivateGlobals> private_globals{};
    std::optional<CollisionConfig> collision{};
    // Logical FF31C0: the latest 7B9C second member. Retained, not consumed;
    // its readers (7AD6 activation, overlap-hit handler resets) are not native.
    std::optional<EffectId> return_only_anchor{};
    // Logical FF31B4 / FF31B8: the 6EC8 / 6EDC dormant objects. Moved into
    // `world` by establish_world.
    std::array<std::optional<EffectId>,2> dormant_anchors{};
    // Logical +1A2 of the FF0690 / FF0838 control records: the 6EB6 dormant
    // objects. Moved into `world` by establish_world.
    std::array<std::optional<EffectId>,2> control_links{};
    // Logical FF447A records (object, then FF312C/FF314C entry index), written
    // by 6AF0 in creation order after 6A94 clears all sixteen. Moved into
    // `world` by establish_world.
    std::array<std::optional<PickupRecord>,16> pickup_records{};
    // Logical FF31AC: 7AD6's branch identity. 6A94 clears it. Moved into `world`
    // by establish_world.
    std::optional<EffectId> activation_target{};
    // Logical message fields of the FF0690 control record (+46, +53, +56) and the
    // setup gates; both are explicit inputs whose producers are not native. The
    // message fields move into `world` by establish_world.
    std::optional<ControlMessage> p1_message{};
    std::optional<SetupGates> setup_gates{};
    // The level world after the setup: the identities above, carried by every
    // object loop through MixedPool::step and committed with it. Absent, a
    // contact or 79B6 callback rejects as before.
    std::optional<PickupWorld> world{};
    // The scene between levels instead (never both): its loop (5EEA) has no
    // 7CC8 and no 179F8, so P1's Up/Down reach only its actor, and it ends
    // after the loop that leaves FF0690's +1A6 = FFFF with FF0B90 clear.
    std::optional<HubWorld> hub{};
};
// Changes between object loops by producers that are not native, applied before
// a loop: E918 calls by code outside the pool (a count: the carried state
// advances through E918 itself, never by replacement) and the message
// producer's updates of each control's +46/+53/+56 (absent keeps the carried
// fields). Neither the banner nor P1 reads them.
struct WorldUpdates {
    unsigned random_calls{};
    std::array<std::optional<ControlMessage>,2> messages{};
};
// One object loop's events and the world's FCB32 requests and CB9A row clears.
struct WorldPhaseResult {
    std::vector<PoolEvent> events;
    std::vector<SoundRequest> sounds;
    std::vector<MessageRowClear> clears;
    std::optional<HubEntry> hub_entry;
};
enum class DormantAnchor { first, second }; // FF31B4 (6EC8), FF31B8 (6EDC)
// 6A94's explicit inputs: FF312C kinds and FF314C counts by entry, and the
// FF4C80 positions, which are consumed densely (one per created pickup).
// Their producers are not native.
struct PickupTables {
    std::array<std::uint16_t,16> kinds{}, counts{};
    std::array<Position,16> positions{};
};
// Every identity the verified [68A4,68BC) setup tail produces.
struct LevelSetupTail {
    std::vector<EffectId> pickups;
    std::array<EffectId,2> control_links;
};
// Every identity the verified [6886,68A4) level-setup prefix produces.
struct LevelSetupPrefix {
    std::array<EffectId,2> dormant;
    ObjectPair rising;
    ObjectQuad quad;
    ObjectPair return_only, visibility;
};
struct MixedSessionResult {
    P1SessionResult p1;
    std::vector<PoolEvent> events;
    std::vector<SoundRequest> world_sounds;
    std::vector<MessageRowClear> clears;
    // The hub: this loop's 623C work outside the pool, and whether 6024's test
    // ends the scene (the loop returns at 603E).
    std::optional<HubEntry> hub_entry{};
    bool scene_ended{};
};
// Banner/input/P1 precede the ordered object loop. Only physical inputs and
// explicit WorldUpdates follow the initial seed. P1 reversal allocation and
// emitter allocation share a stack. Dedicated P1 effects must be absent.
// Externally reserved private state, timer, rendering/audio and other
// controller contexts are excluded; collision hits need a carried world.
// Collision probes consume P1 tracking after its wrapper and a retained config.
// 7B9C within the retained world: pair allocation plus the anchor identity,
// committed together.
ObjectPair initialize_return_only_pair(MixedSessionState& state);
// 6EC8 / 6EDC within the retained world: dormant allocation plus its identity.
EffectId initialize_dormant(MixedSessionState& state, DormantAnchor anchor);
// [6886,68A4): LEA FF0690,A5, then 6EC8, 6EDC, 7772, 783A, 7B9C and 7C26 in
// order. `control` is the logical identity of FF0690. All twelve pops and the
// FF31B4/FF31B8/FF31C0 identities commit together or not at all.
LevelSetupPrefix initialize_level_setup_prefix(MixedSessionState& state, ActorId control);
// 6A94: clear all sixteen pickup records, FF31AC and the FF31B0 rise gate (when
// private globals are present), then one 6AF0 pickup per entry whose kind is not
// FFFF, storing `control` and recording it. All or nothing.
std::vector<EffectId> initialize_pickups(MixedSessionState& state, const PickupTables& tables, ActorId control);
// 6EB6 with A5 = FF0690 (player 0) or FF0838 (player 1): a dormant pop whose
// identity is stored in that control's +1A2 link.
EffectId initialize_control_link(MixedSessionState& state, std::size_t player);
// [68A4,68BC): 6A94 (with A5 still FF0690 from the prefix), then 6EB6 for P1
// and P2. All pops, records, links and clears commit together.
LevelSetupTail initialize_level_setup_tail(MixedSessionState& state, const PickupTables& tables, ActorId control);
// [68BC,68C4): 7DB8 then 6EF0. 7DB8 does nothing for two players; otherwise it
// selects FRUIT RETURNED (clearing FF31AA) when FF31AA is set, else MIX THOSE
// FRUIT when at least two FF312C kinds are not FFFF, and passes it through CB72:
// a priority below the stored +53 (signed bytes) leaves +46 = FFFFFFFF; else +53
// takes it and CB9A clears the message row. 6EF0 returns at once unless FF33E2
// or FF316C is set; its allocating path is not native and rejects.
SetupMessageResult continue_level_setup(MixedSessionState& state, const PickupTables& tables);
// [68C4,68D4): 7FBE, 7154, 735E and 7568 in order, each returning at once while
// its gate is zero. A5 at 68C4 is FF0690 when 7DB8 stored a message and the
// tail's FF0838 otherwise. Every pop commits together or not at all; the leads'
// handlers are not native.
LevelSetupPairs initialize_gated_pairs(MixedSessionState& state, const GatedPairInputs& inputs);
// After [6886,68D4): the setup's +1A2 links, records, FF31AC, FF31B4/FF31B8,
// FF31C0, P1 message fields, tilemap, FF316C and FF33E2 become one carried
// PickupWorld (FF31A8 and FF0690's +3C/+3E are the caller's) with what the
// setup does not produce: the FF312C kinds, the logical FF0690/FF0838 controls,
// P2's message fields and FF31BE. The moved session fields are cleared so one
// copy stays authoritative. Every world identity must stay live.
void establish_world(MixedSessionState& state, const PickupTables& tables, std::array<ActorId,2> controls,
    ControlMessage p2, std::uint16_t ingredient_timer);
// 17024 then F850 (F872, F940): 68 free slots, zero but their 12646 selectors,
// with the free stack bottom-first in address order (slot 0 at FF300C). The
// slot count is the original pool's.
MixedPool reset_object_pool();
// The scene change from the level's end into the scene between levels, as it
// changes the carried session: 0x488 (FF4446/FF4448, the timer's requested
// position, into FF0690's +A2/+A4), 16EA4 (17024 and F850: `reset_object_pool`;
// FF0F16, the acceleration gate, cleared; 131C2 and FF0B92 = 001E), 9880 on
// FF0690 (`make_hub_actor`, tracking selector 0; P2's actor is not native),
// 5D58 (FF33E0 = 7), then 63A4/60E6
// (`initialize_hub` over the records), 63E2's banner (single player, row 000D:
// the scratch Y) and 5ED4 (FF0B92 = 000A). The level's world and every identity
// it named are dropped. Returns 9952's parameters and the cleared gate for the
// session's configuration, the doors and the banner request. Everything
// commits together.
struct HubSceneInputs {
    HubDoorTable table{};
    bool two_player{}, slow{};
    std::uint16_t stage{};
    LevelBannerConfig banner{};
};
struct HubSceneEntry {
    ActorParameters parameters;
    std::uint16_t acceleration_gate{};
    std::vector<EffectId> doors;
    std::optional<LevelBannerRequest> banner;
};
HubSceneEntry enter_hub_scene(MixedSessionState& state, const HubSceneInputs& inputs);
// After the hub's loop returns, 0x4A4's 10D8/10F8 (not native) and, unless
// FF13E2 is 3 or FF33F4's +0E is FFFFFFFF, the hint screen (1959E). Its head as
// it changes the session: 16EA4 (`reset_object_pool`; both actors zeroed, P1's
// keeping only its 12646 selectors; FF0F16, the acceleration gate, cleared;
// 131C2 and FF0B92 = 001E), then FF0F10 = 00F0. The hub world is dropped. P1
// is not stepped again until `enter_second_level` rebuilds it; the screen's
// loops are `step_hint_screen` on the carried timer and P1's control.
HintScreen enter_hint_screen(MixedSessionState& state);
// E2A and 754's head (118C, 0x774) as they change the session, single player:
// 16EA4 again, FF0690's +A2/+A4 (the timer's saved position) cleared and 9880
// (`make_hub_actor` at that zero anchor; tracking selector 0); then 118C: 54BA's
// E918 draws (`random_before`:
// a retry per draw whose map column fails its test; not native), +1A6
// cleared, FF33D8 (FFFF when FF3402 is above 000A as a signed word, 0 when it
// is 0, else E918's low word modulo FF3402 plus 2), the remaining E918 draws
// (`random_after`: 2512's objects and 1386; not native), 9952 again
// (`reset_actor_appearance`); then FF33E0 = 0013. The level's world (2512's
// objects, the HUD, messages, the camera words) is not native: the pool stays
// as 16EA4 left it. Returns 9952's parameters and the cleared gate. Two players
// reject; everything commits together.
struct SecondLevelInputs {
    bool two_player{}, slow{};
    std::uint16_t cooldown_range{}; // FF3402
    unsigned random_before{}, random_after{};
};
struct SecondLevelEntry {
    ActorParameters parameters;
    std::uint16_t acceleration_gate{};
};
SecondLevelEntry enter_second_level(MixedSessionState& state, const SecondLevelInputs& inputs);
// [11B0,11EE): FF33D8 from FF3402, drawing E918 only for 1..000A or a negative word.
std::uint16_t choose_action_cooldown(std::uint16_t range, TrailRandom& random) noexcept;
// [5E86,5E8E) of the scene between levels: 63A4 on `stage` (FF33C4), then
// 60E6 over the carried hub world's records. Everything commits together.
std::vector<EffectId> initialize_hub(MixedSessionState& state, std::uint16_t stage);
// One object loop of the session's pool: `updates`, the frame's 7CC8 call
// (mix_spell) when a level world is carried, then MixedPool::step with
// the private globals, `collision` and the carried world when established. The
// owner and position feed reversal effects and 6D8C emitters. A hub world's
// 623C leaves its entry in `hub_entry` and P1 coasting (630A). All of it
// commits together; the loop's world requests move into the result.
WorldPhaseResult step_world_phase(MixedSessionState& state, ActorId owner, Position position,
    const CollisionInputs* collision, std::size_t budget, const WorldUpdates& updates = {});
// The transition timer (when the session carries one), banner, input and P1,
// then step_world_phase with P1's tracking (AC5E's
// control coordinates) and actor position, so a carried world's hits, emitter
// owner and collisions come from native P1.
MixedSessionResult step_mixed_session(const assets::SceneResource& scene, const assets::PatternBank& bank,
    MixedSessionState& state, const P1SessionConfig& config, ThreeButtonPad held, const WorldUpdates& updates = {});
} // namespace wiz::sim
