#pragma once
#include "sim/actor.hpp"
#include "sim/collision_probe.hpp"
#include "sim/input.hpp"
#include "sim/return_only.hpp"
#include <array>
#include <optional>

namespace wiz::sim {
// The scene between levels (5D30): its doors. FF330C holds nine 14-byte door
// records (6040 seeds them from 6090). 60E6 reads +0 X, +2 Y, +4 the door's
// number, +8 its state (negative: closed) and +A the two-player marker; 63A4
// rewrites +8. +6 and +C are never read here.
struct HubDoorRecord {
    Position position;
    std::uint16_t number{}, word6{}, state{}, marker{}, word12{};
};
using HubDoorTable = std::array<HubDoorRecord,9>;
// 63A4: with FF33E2 clear and FF33C4's low three bits clear, the first eight
// records' +8 become FF33C4 >> 3 (FF33DE, a byte, is cleared; not modeled).
// Returns whether it rewrote them.
bool update_hub_door_states(HubDoorTable& table, std::uint16_t stage, bool two_player) noexcept;
// 6334's number frames: 00B8 plus the 639A byte at the number's low byte
// (EXT.W, so 0..9); the left object gets it, the right one it plus one. Other
// numbers read outside the table and reject.
std::array<std::uint16_t,2> hub_door_number_frames(std::uint16_t number);

// A door object. 611E: F9E2 defaults, +22 = the number, (x, y), mode 80, frame
// 00B0, handler 12646, +26/+2A = 6334's two number objects; an open record
// (+8 non-negative) then gets mode 81, frames 00A8/00B7, cadence 3/3, +10 =
// 003C and handler 61F6 (`waiting`); a closed one keeps the RTS (`closed`).
// 61F6 counts +10 down; a negative result sets extents 0010/0018, service
// 621A and handler 6218 (`open`). 621A tests AC5E against FF0690, then FF0838
// with FF33E2 set; a contact runs 623C (MixedPool::enter_hub_door), which
// leaves the door `vanishing`: (x - 4, y + 8), mode 85, frames 021E/021E/0227,
// target 0227, cadence 3/3, callback FAA4, +10 = 0, handler FAC4, service
// 6218. FAC4 counts +10 down; negative: X - 4, mode 85, frame back to +08 and
// handler FAE2 (`puffing`, an RTS) until the presentation's FAA4 releases it.
// F9E2 leaves +0E, +1A and the extents as the previous occupant left them;
// they are read only after being written here and are held as zero.
enum class HubDoorPhase : std::uint8_t { closed, waiting, open, vanishing, puffing };
struct HubDoor {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{}, x_extent{}, y_extent{};
    std::uint16_t number{};
    std::array<EffectId,2> numbers{}; // +26 (left), +2A (right).
    HubDoorPhase phase = HubDoorPhase::closed;
};
// 611E for one record, given its two 6334 number objects.
HubDoor make_hub_door(const HubDoorRecord& record, std::array<EffectId,2> numbers) noexcept;
// 6334's number objects (F994 defaults, mode 80): left at (x - 10, y - 0A),
// right at (x + 8, y - 0A), frames from hub_door_number_frames.
std::array<ReturnOnlyObject,2> make_hub_door_numbers(const HubDoorRecord& record);
// A closed record's third object (F9E2, mode 80): (x - 8, y), frame 00CD.
ReturnOnlyObject make_hub_door_lock(const HubDoorRecord& record) noexcept;
// With FF33E2 set and +A non-negative, a closed record's fourth object
// (F9E2, mode 80): (x - 1, y + 7), frame 0217; +A nonzero moves it to x + 1,
// frame 0218 and flips +12 bit 0800.
ReturnOnlyObject make_hub_door_partner(const HubDoorRecord& record) noexcept;
// One walk: active gate, presentation (FAA4 releases a vanishing or puffing
// door; any other callback rejects), the phase's handler, then its service
// (621A when open, chosen after the handler). `touched` names the control
// (0 FF0690, 1 FF0838) whose contact the caller's 623C must run; a contact
// leaves the door as walked. FF0838 needs the secondary tracker.
struct HubDoorStep { bool released{}; std::optional<std::size_t> touched; };
HubDoorStep step_hub_door(HubDoor& door, const CollisionInputs* inputs, bool two_player);
// 623C's change to the touched door itself (see HubDoor).
void vanish_hub_door(HubDoor& door) noexcept;
// 623C's FF4446/FF4448 from the touched door: (x - 0114, y - 0098), each AND FFF8.
Position hub_requested_position(const HubDoor& door) noexcept;
// 9880 on one control, after 17024 zeroed its actor and F872 gave it the
// 12646 selectors: 98DE clears the control's +1A6 (the caller's tracking
// selector); 9952 sets +4A, clears +12 and +22 and runs 5964 (mode 87, frames
// 0227/021E/0227, target 021E, cadence 3/3, flags & 9FFF) before callback AA50;
// then +0C = 19, flags | 0800 and the position (0114, 00B0) + the control's
// +A2/+A4 (`anchor`, which 0x488 copied from FF4446/FF4448). 1737E's camera
// words and 9952's other control words are not native.
ActorState make_hub_actor(Position anchor) noexcept;
// 9952's change to an actor (from 98DE, or again from 118C): +12 and +22
// cleared, then 5964 (mode 87, frames 0227/021E/0227, target 021E, cadence
// 3/3, handler and service 12646, flags & 9FFF) and callback AA50. The
// position, vertical motion, airborne delay and +10 are kept; +4A (the owning
// control) is not native.
void reset_actor_appearance(ActorState& actor) noexcept;
// The hint screen (1959E) between the hub and the second level. Its head
// (16EA4's fade-in with FF0B92 = 001E, then FF0F10 = 00F0) leaves `countdown`
// at 00F0. Each loop follows the frame's 1345A: once `ending` (FF0F0E) the
// screen returns (19764) when the timer is idle; otherwise 14DA2 converts the
// pad and 14E3C sets its +16 to A|B|C; while the timer runs the loop waits;
// then Start (the raw byte's bit 7 clear) or FF0F10 decremented below zero sets
// FF0F0E and starts 13208's fade. Its text and sprite objects are not native.
struct HintScreen {
    std::uint16_t countdown = 0xf0;
    bool ending{};
};
// 14E3C: +16 = +1E | +1F | +20 (A|B|C).
void merge_action_buttons(PadControl& control) noexcept;
// [1975A,19764) when ending, else [1972E,19764): the loop's test after the
// pad. Returns whether the screen returns.
bool continue_hint_screen(HintScreen& hint, TransitionState& timer, bool start) noexcept;
// One loop: the frame's 1345A, the pad (unless ending), then the test.
bool step_hint_screen(HintScreen& hint, TransitionState& timer, PadControl& control, ThreeButtonPad held) noexcept;
// 9952's movement parameters (+5A..+6C; +68 = 2 is not a native parameter):
// limits 00C0/FF40, or 0060/FFA0 when the control's +30 is nonzero.
ActorParameters hub_actor_parameters(bool slow) noexcept;
// 6024: the loop returns (603E) when FF0690's +1A6 is FFFF and FF0B90 is zero.
bool hub_loop_ends(std::uint16_t selector, const TransitionState& timer) noexcept;
} // namespace wiz::sim
