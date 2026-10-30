#include "sim/hub.hpp"
#include "sim/presentation.hpp"

namespace wiz::sim {
namespace {
// 639A: the number objects' frame offsets.
constexpr std::array<std::uint8_t,10> number_offsets{0x02,0x04,0x06,0x08,0x0a,0x0c,0x0e,0x10,0x12,0x00};
std::uint16_t word(unsigned value) noexcept { return static_cast<std::uint16_t>(value); }
}
bool update_hub_door_states(HubDoorTable& table, std::uint16_t stage, bool two_player) noexcept {
    if (two_player || (stage & 7U)) return false;
    for (std::size_t i=0;i<8;++i) table[i].state=word(stage >> 3U);
    return true;
}
std::array<std::uint16_t,2> hub_door_number_frames(std::uint16_t number) {
    // EXT.W D2, then ADD.B 0E(PC,D2.W): only the low byte indexes.
    const auto index=static_cast<std::int8_t>(number & 0xffU);
    if (index<0 || index>=static_cast<std::int8_t>(number_offsets.size())) throw assets::BankError("hub door number outside the 639A table");
    // ADD.B: the byte wraps inside 00B8's low byte.
    const auto low=static_cast<std::uint8_t>(0xb8U + number_offsets[static_cast<std::size_t>(index)]);
    return {low,word(low + 1U)};
}
HubDoor make_hub_door(const HubDoorRecord& record, std::array<EffectId,2> numbers) noexcept {
    HubDoor door;door.position=record.position;door.number=record.number;door.numbers=numbers;
    door.presentation.mode=0x80;door.presentation.words[0]=0xb0;
    if (!(record.state & 0x8000U)) {
        door.presentation={0x81,{0xb0,0xa8,0xb7},3,3};door.countdown=0x3c;door.phase=HubDoorPhase::waiting;
    }
    return door;
}
std::array<ReturnOnlyObject,2> make_hub_door_numbers(const HubDoorRecord& record) {
    const auto frames=hub_door_number_frames(record.number);
    std::array<ReturnOnlyObject,2> out{};
    out[0].position={word(record.position.x-0x10U),word(record.position.y-0x0aU)};
    out[1].position={word(record.position.x+8U),word(record.position.y-0x0aU)};
    for (std::size_t i=0;i<2;++i) { out[i].presentation.mode=0x80;out[i].presentation.words[0]=frames[i]; }
    return out;
}
ReturnOnlyObject make_hub_door_lock(const HubDoorRecord& record) noexcept {
    ReturnOnlyObject lock;lock.position={word(record.position.x-8U),record.position.y};
    lock.presentation.mode=0x80;lock.presentation.words[0]=0xcd;return lock;
}
ReturnOnlyObject make_hub_door_partner(const HubDoorRecord& record) noexcept {
    ReturnOnlyObject partner;partner.position={word(record.position.x-1U),word(record.position.y+7U)};
    partner.presentation.mode=0x80;partner.presentation.words[0]=0x217;
    if (record.marker) { partner.position.x=word(partner.position.x+2U);partner.presentation.words[0]=0x218;partner.flags^=0x0800U; }
    return partner;
}
HubDoorStep step_hub_door(HubDoor& door, const CollisionInputs* inputs, bool two_player) {
    if (!(door.presentation.mode & 0x80U)) return {};
    auto next=door;HubDoorStep step;
    if (advance_presentation(next.presentation,next.target)) {
        if (next.phase!=HubDoorPhase::vanishing && next.phase!=HubDoorPhase::puffing) throw assets::BankError("unsupported hub door callback");
        next.presentation.mode=0;step.released=true; // FAA4
    }
    if (next.phase==HubDoorPhase::waiting) {
        next.countdown=word(next.countdown-1U);
        if (next.countdown & 0x8000U) { next.x_extent=0x10;next.y_extent=0x18;next.phase=HubDoorPhase::open; }
    } else if (next.phase==HubDoorPhase::vanishing) {
        next.countdown=word(next.countdown-1U);
        if (next.countdown & 0x8000U) {
            next.position.x=word(next.position.x-4U);next.presentation.mode=0x85;
            next.presentation.words[0]=next.presentation.words[1];next.phase=HubDoorPhase::puffing;
        }
    }
    // FAC4 after FAA4 in the same walk would revive a slot already on the free stack.
    if (step.released && next.presentation.mode) throw assets::BankError("unsupported hub door revival after release");
    if (next.phase==HubDoorPhase::open) {
        if (!inputs) throw assets::BankError("hub door collision inputs unavailable");
        const Position extents{next.x_extent,next.y_extent};
        if (overlaps_control(next.position,extents,inputs->primary,inputs->config.x_mask)) step.touched=0;
        else if (two_player) {
            if (!inputs->config.secondary) throw assets::BankError("hub door secondary tracker unavailable");
            if (overlaps_control(next.position,extents,*inputs->config.secondary,inputs->config.x_mask)) step.touched=1;
        }
    }
    door=next;return step;
}
void vanish_hub_door(HubDoor& door) noexcept {
    door.position={word(door.position.x-4U),word(door.position.y+8U)};
    door.presentation={0x85,{0x21e,0x21e,0x227},3,3};door.target=0x227;door.countdown=0;door.phase=HubDoorPhase::vanishing;
}
Position hub_requested_position(const HubDoor& door) noexcept {
    return {word((door.position.x-0x114U) & 0xfff8U),word((door.position.y-0x98U) & 0xfff8U)};
}
ActorState make_hub_actor(Position anchor) noexcept {
    ActorState a;reset_actor_appearance(a);auto& m=a.motion;
    m.presentation.counter=0x19;m.flags|=0x0800;m.position={word(anchor.x+0x114U),word(anchor.y+0xb0U)};
    return a;
}
void reset_actor_appearance(ActorState& actor) noexcept {
    auto& m=actor.motion;
    m.flags=0;m.horizontal_speed=0;
    m.presentation={0x87,{0x227,0x21e,0x227},3,3};actor.presentation_target=0x21e;
    m.update=MotionUpdate::return_only;actor.service=ActorService::return_only;actor.callback=PresentationCallback::enter_airborne;
}
void merge_action_buttons(PadControl& control) noexcept {
    control.jump=static_cast<std::uint8_t>(control.a | control.b | control.c);
}
bool continue_hint_screen(HintScreen& hint, TransitionState& timer, bool start) noexcept {
    if (timer.direction) return false;
    if (hint.ending) return true;
    if (!start) {
        hint.countdown=word(hint.countdown-1U);
        if (!(hint.countdown & 0x8000U)) return false;
    }
    hint.ending=true;start_transition(timer);
    return false;
}
bool step_hint_screen(HintScreen& hint, TransitionState& timer, PadControl& control, ThreeButtonPad held) noexcept {
    step_transition_timer(timer);
    if (!hint.ending) {
        control=produce_pad_control(held);merge_action_buttons(control);
    }
    return continue_hint_screen(hint,timer,!(control.raw & 0x80U));
}
ActorParameters hub_actor_parameters(bool slow) noexcept {
    ActorParameters p;
    p.airborne.motion={static_cast<std::uint16_t>(slow ? 0x60 : 0xc0),static_cast<std::uint16_t>(slow ? 0xffa0 : 0xff40),3};
    p.airborne.acceleration=0x0c;p.airborne.contact_damping_count_minus_one=0x0b;p.airborne.gravity=4;
    p.ground_acceleration=8;p.jump_impulse=0x1c;p.jump_delay=0x0a;
    return p;
}
bool hub_loop_ends(std::uint16_t selector, const TransitionState& timer) noexcept {
    return selector==0xffff && !timer.direction;
}
} // namespace wiz::sim
