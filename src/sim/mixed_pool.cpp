#include "sim/mixed_pool.hpp"
#include <algorithm>
#include <limits>
#include <type_traits>

namespace wiz::sim {
namespace {
bool active(const PoolObject& object) {
    return std::visit([](const auto& o) {
        using T=std::decay_t<decltype(o)>;
        if constexpr (std::is_same_v<T,std::monostate> || std::is_same_v<T,ExternalReservation>) return false;
        else return bool(o.presentation.mode & 0x80U);
    },object);
}
}
MixedPool::MixedPool(std::vector<PoolObject> objects,std::vector<std::size_t> free_stack,
        std::vector<std::optional<InheritedObjectFields>> inherited) {
    if (objects.size()>4096) throw assets::BankError("mixed pool slot budget exceeded");
    if (!inherited.empty() && inherited.size()!=objects.size()) throw assets::BankError("mixed pool inherited extent differs");
    inherited.resize(objects.size());
    std::vector<bool> free(objects.size());
    for (auto i:free_stack) {
        if (i>=objects.size() || free[i] || !std::holds_alternative<std::monostate>(objects[i]))
            throw assets::BankError("invalid mixed pool free stack");
        free[i]=true;
    }
    slots_.reserve(objects.size());
    for (std::size_t i=0;i<objects.size();++i) {
        if (std::holds_alternative<std::monostate>(objects[i])!=free[i])
            throw assets::BankError("mixed pool occupancy mismatch");
        if (!free[i] && !std::holds_alternative<ExternalReservation>(objects[i]) && !std::holds_alternative<ReturnOnlyObject>(objects[i]) && !active(objects[i]))
            throw assets::BankError("inactive managed seed must be free or reserved");
        if (inherited[i] && !free[i]) throw assets::BankError("occupied slot cannot carry inherited fields");
        slots_.push_back({std::move(objects[i]),free[i] ? 0U : 1U,inherited[i]});
    }
    free_=std::move(free_stack);
}
EffectId MixedPool::allocate(PoolObject object) {
    if (free_.empty()) throw assets::BankError("mixed pool allocation exhausted");
    const auto i=free_.back();auto& slot=slots_[i];
    if (slot.generation==std::numeric_limits<std::uint64_t>::max())
        throw assets::BankError("mixed pool identity exhausted");
    slot.object=std::move(object);slot.inherited.reset();++slot.generation;free_.pop_back();return {i,slot.generation};
}
template<std::size_t N,class Make> std::array<EffectId,N> MixedPool::initialize_group(Make make,const char* exhausted,const char* unknown,InheritanceNeeds needs) {
    auto next=*this;std::array<EffectId,N> ids{};
    for (std::size_t m=0;m<N;++m) {
        if (next.free_.empty()) throw assets::BankError(exhausted);
        const auto inherited=next.slots_[next.free_.back()].inherited;
        if (!inherited || (needs.presentation && !inherited->presentation) || (needs.position && !inherited->position))
            throw assets::BankError(unknown);
        ids[m]=next.allocate(make(m,*inherited));
    }
    *this=std::move(next);return ids;
}
template<class Make> ObjectPair MixedPool::initialize_pair(Make make,const char* exhausted,const char* unknown) {
    const auto ids=initialize_group<2>([&](std::size_t m,const InheritedObjectFields& inherited) {
        return make(m ? PairMember::second : PairMember::first,inherited);
    },exhausted,unknown,{});
    return {ids[0],ids[1]};
}
ObjectPair MixedPool::initialize_return_only_pair() {
    return initialize_pair(make_return_only_pair_member,"return-only pair allocation exhausted","return-only pair inherits unknown slot state");
}
ObjectPair MixedPool::initialize_rising_pair(ActorId control) {
    // The second member derives its position from the first member just built.
    Position first{};
    return initialize_pair([&](PairMember m,const InheritedObjectFields& inherited) {
        auto object=make_rising_pair_member(m,inherited,control,first);
        if (m==PairMember::first) first=object.position;
        return object;
    },"rising pair allocation exhausted","rising pair inherits unknown slot state");
}
ObjectQuad MixedPool::initialize_collision_quad(ActorId control) {
    // Members 1..3 copy the probe's position through A4 before adding 32.
    Position probe{};
    return {initialize_group<4>([&](std::size_t m,const InheritedObjectFields& inherited) -> PoolObject {
        if (!m) { auto object=make_quad_probe(inherited,control);probe=object.position;return object; }
        return make_quad_return_only(static_cast<QuadMember>(m),inherited,probe);
    },"collision quad allocation exhausted","collision quad inherits unknown slot state",{true,false})};
}
EffectId MixedPool::initialize_pickup(ActorId control, Position at, std::uint16_t kind, std::uint16_t count, std::size_t record) {
    return initialize_group<1>([&](std::size_t,const InheritedObjectFields& inherited) -> PoolObject {
        return make_pickup(inherited,control,at,kind,count,record);
    },"pickup allocation exhausted","pickup inherits unknown slot state",{})[0];
}
GatedPairIds MixedPool::initialize_gated_pair(GatedPair pair, ActorId control, Position p2_origin) {
    // The pops are LIFO from a known stack, so the address order is known before
    // either is made; with fewer than two entries the group rejects anyway.
    const auto n=free_.size();
    const bool first_lower=n<2 || free_[n-1]<free_[n-2];
    const auto ids=initialize_group<2>([&](std::size_t m,const InheritedObjectFields& inherited) -> PoolObject {
        if ((m==0)==first_lower) return make_gated_partner(pair,inherited);
        return make_gated_lead(pair,inherited,control,p2_origin);
    },"gated pair allocation exhausted","gated pair inherits unknown slot state",{true,false});
    const GatedPairIds out{ids[first_lower ? 0 : 1],ids[first_lower ? 1 : 0]};
    std::get<GatedLead>(slots_[out.lead.slot].object).partner=out.partner;
    return out;
}
EffectId MixedPool::initialize_dormant() {
    return initialize_group<1>([](std::size_t,const InheritedObjectFields& inherited) -> PoolObject { return make_dormant(inherited); },
        "dormant allocation exhausted","dormant object inherits unknown slot state",{true,true})[0];
}
ObjectPair MixedPool::initialize_visibility_pair() {
    return initialize_pair(make_visibility_pair_member,"visibility pair allocation exhausted","visibility pair inherits unknown slot state");
}
std::vector<EffectId> MixedPool::initialize_hub_doors(const HubDoorTable& table, bool two_player) {
    auto next=*this;std::vector<EffectId> ids;
    // F9E2 (door, lock, partner) and F994 (6334's numbers) loop forever when empty.
    auto pop=[&](PoolObject object,bool number=false) {
        if (next.free_.empty()) throw assets::BankError(number ? "hub door number allocation exhausted" : "hub door allocation exhausted");
        ids.push_back(next.allocate(std::move(object)));return ids.back();
    };
    // 60E6: D7 = 7, or 8 with FF33E2 set; DBRA.
    for (std::size_t r=0;r<(two_player ? 9U : 8U);++r) {
        const auto& record=table[r];
        // 611E's F9E2 pops the door first; 6334 then pops A4 (left) and A5 (right).
        const auto door=pop(ReturnOnlyObject{});
        const auto numbers=make_hub_door_numbers(record);
        const auto left=pop(numbers[0],true);const auto right=pop(numbers[1],true);
        next.slots_[door.slot].object=make_hub_door(record,{left,right});
        if (!(record.state & 0x8000U)) continue;
        pop(make_hub_door_lock(record));
        if (two_player && !(record.marker & 0x8000U)) pop(make_hub_door_partner(record));
    }
    *this=std::move(next);return ids;
}
EffectId MixedPool::spawn(ReversalEffect effect) {
    if (!effect.owner.value || (effect.side!=ReversalSide::from_right && effect.side!=ReversalSide::from_left) || !(effect.presentation.mode&128U))
        throw assets::BankError("invalid mixed reversal spawn");
    return allocate(effect);
}
EffectId MixedPool::spawn(TrailParticle particle) {
    if (!(particle.presentation.mode&128U)) throw assets::BankError("inactive mixed trail spawn");
    return allocate(particle);
}
const PoolSlot& MixedPool::at(EffectId id) const {
    if (id.slot>=slots_.size() || !id.generation || slots_[id.slot].generation!=id.generation)
        throw assets::BankError("stale mixed pool identity");
    return slots_[id.slot];
}
PoolSlot& MixedPool::slot_at(EffectId id) { at(id);return slots_[id.slot]; }
bool MixedPool::walk_pickup_slot(std::size_t i, const CollisionInputs& inputs, PickupWorld* world) {
    auto& pickup=std::get<Pickup>(slots_[i].object);
    std::optional<std::uint16_t> kind;
    if (world && pickup.phase==PickupPhase::swapped_in && pickup.record<world->records.size() && world->records[pickup.record])
        kind=world->kinds.at(world->records[pickup.record]->entry);
    const auto walk=sim::walk_pickup(pickup,inputs,kind);
    if (walk.contact==PickupContact::none) return walk.released;
    const bool secondary=walk.contact==PickupContact::secondary;
    if (!world) throw assets::BankError(secondary ? "unsupported pickup-hit 6C00 (secondary)" : "unsupported pickup-hit 6C00 (primary)");
    world->sounds.push_back({0x89,6,0xc0,1});
    const auto frame=pickup.presentation.words[1];
    if (frame==0x20d || frame==0x205 || frame==0x1fd) throw assets::BankError("unsupported pickup-hit 6C00 family");
    const auto player=secondary ? 1U : 0U;
    const auto link=world->links[player];
    if (!link) throw assets::BankError("pickup control link unavailable");
    auto& held=slot_at(*link).object;
    auto record=[&](std::size_t r) -> PickupRecord& {
        if (r>=world->records.size() || !world->records[r]) throw assets::BankError("pickup record unavailable");
        return *world->records[r];
    };
    // TST.B of the link's mode byte selects 6D22 (zero) or the exchange.
    if (const auto* dormant=std::get_if<ReturnOnlyObject>(&held); dormant && !dormant->presentation.mode) {
        // FB06 copies the pickup before its X - 8; the record then names the link.
        auto& r=record(pickup.record);
        held=carry_pickup(pickup,world->controls[player]);
        r.object=*link;
        begin_pickup_vanish(pickup,PickupPhase::vanishing);
        return false;
    }
    auto* emitter=std::get_if<TrailEmitter>(&held);
    if (!emitter || !emitter->presentation.mode) throw assets::BankError("unsupported pickup-hit 6C00 link state");
    exchange_carried(pickup,*emitter);
    // Each record names its new holder; the pickup's write is the later one.
    record(emitter->carried->record).object=*link;
    record(pickup.record).object=EffectId{i,slots_[i].generation};
    begin_pickup_vanish(pickup,PickupPhase::swapped_out);
    return false;
}
std::optional<DeliveryIds> MixedPool::walk_probe_slot(std::size_t i, const CollisionInputs& inputs, const std::uint32_t* rise_gate, PickupWorld* world) {
    const auto contact=walk_collision_probe(std::get<CollisionProbe>(slots_[i].object),inputs);
    if (contact==PickupContact::none) return {};
    const bool secondary=contact==PickupContact::secondary;
    if (!world) throw assets::BankError(secondary ? "unsupported collision-hit7910 (secondary)" : "unsupported collision-hit7910 (primary)");
    if (!rise_gate) throw assets::BankError("collision-hit7910 rise gate unavailable");
    if (*rise_gate) return {}; // CMPI.L #0,FF31B0 then BNE 79B4.
    const auto player=secondary ? 1U : 0U;
    const auto link=world->links[player];
    if (!link) throw assets::BankError("probe control link unavailable");
    auto& held=slot_at(*link).object;
    // TST.B of the link's mode byte: zero returns at 7A56.
    if (const auto* dormant=std::get_if<ReturnOnlyObject>(&held); dormant && !dormant->presentation.mode) return {};
    const auto* emitter=std::get_if<TrailEmitter>(&held);
    if (!emitter) throw assets::BankError("unsupported collision-hit7910 link state");
    if (!emitter->presentation.mode) return {};
    world->sounds.push_back({0x8c,6,0xc0,1});
    const auto delivery=deliver_carried(*emitter,world->controls[player]);
    // 59AE's F9E2 pops first, then F994; either on an empty stack never returns.
    if (free_.size()<2) throw assets::BankError("delivery allocation exhausted");
    const DeliveryIds ids{allocate(delivery.sparkle),allocate(delivery.copy)};
    held=delivery.link;
    return ids;
}
std::optional<DeliveryIds> MixedPool::walk_probe(EffectId id, const CollisionInputs& inputs, std::uint32_t rise_gate, PickupWorld& world) {
    if (!std::holds_alternative<CollisionProbe>(at(id).object)) throw assets::BankError("pool object is not a collision probe");
    auto next=*this;auto w=world;
    const auto ids=next.walk_probe_slot(id.slot,inputs,&rise_gate,&w);
    *this=std::move(next);world=std::move(w);return ids;
}
bool MixedPool::walk_pickup(EffectId id, const CollisionInputs& inputs, PickupWorld& world) {
    if (!std::holds_alternative<Pickup>(at(id).object)) throw assets::BankError("pool object is not a pickup");
    auto next=*this;auto w=world;
    const bool released=next.walk_pickup_slot(id.slot,inputs,&w);
    if (released) next.free_.push_back(id.slot);
    *this=std::move(next);world=std::move(w);return released;
}
bool MixedPool::walk_delivered_slot(std::size_t i, PrivateGlobals* globals, PickupWorld* world) {
    auto& copy=std::get<DeliveredPickup>(slots_[i].object);
    if (!(copy.presentation.mode & 0x80U)) return false;
    auto next=copy;
    if (!advance_presentation(next.presentation,next.target)) { copy=next;return false; }
    if (!world) throw assets::BankError("unsupported delivered pickup callback 79B6");
    if (!globals) throw assets::BankError("private globals unavailable");
    // 79B6: frames back from +22/+26 and 6BB2's cadence from +10 (still the
    // carried count), then the 7A88 handler; +32 and +10 follow CB72.
    const std::uint8_t cadence=next.carried.count==2 ? 1 : 5;
    TableMotion table{{static_cast<std::uint16_t>(next.position.x+8U),static_cast<std::uint16_t>(next.position.y+4U)},next.flags,
        {0x81,{next.frames[0],next.frames[0],next.frames[1]},cadence,cadence},next.target,0x0e,next.control,0,0xffff,0};
    // 79F2: a nonzero FF31AC selects D22F and 7AD6's FF31B8 path; 7A0E then
    // negates the FF31AC object's +32 (A0 survives CB72).
    const bool second=bool(world->activation);
    if (second) {
        const auto* first=std::get_if<TableMotion>(&slot_at(*world->activation).object);
        if (!first) throw assets::BankError("79B6 FF31AC object is not a table object");
        table.delta_x=static_cast<std::uint16_t>(0U-first->delta_x);
    }
    const auto k=std::find(world->controls.begin(),world->controls.end(),next.control)-world->controls.begin();
    if (k==2 || !world->messages[static_cast<std::size_t>(k)]) throw assets::BankError("delivered control message unavailable");
    if (const auto clear=post_message(*world->messages[static_cast<std::size_t>(k)],second ? SetupMessage::second_ingredient : SetupMessage::first_ingredient,world->message_tilemap))
        world->clears.push_back(*clear);
    // 7B22 (first): FF31AC = the FF31B4 object. 7AE6 (second): FF31B0 = the
    // FF31B8 object. Either way FB06 copies into it, the record names it, FAA4.
    const auto target=world->dormant[second ? 1 : 0];
    if (!target) throw assets::BankError(second ? "7AD6 FF31B8 object unavailable" : "7AD6 FF31B4 object unavailable");
    auto& dormant=slot_at(*target).object;
    if (const auto* d=std::get_if<ReturnOnlyObject>(&dormant); !d || d->presentation.mode) throw assets::BankError("7AD6 target is not dormant");
    const auto r=next.carried.record;
    if (r>=world->records.size() || !world->records[r]) throw assets::BankError("delivered record unavailable");
    if (second) {
        // 7B06: the FF31C0 anchor's handler becomes 7B42 with +4A = A5 and +10 = 012C.
        if (!world->anchor) throw assets::BankError("7AD6 FF31C0 anchor unavailable");
        auto& anchor=slot_at(*world->anchor).object;
        const auto* a=std::get_if<ReturnOnlyObject>(&anchor);
        if (!a) throw assets::BankError("7AD6 FF31C0 anchor is not return-only");
        if (!globals->table_loop_count) throw assets::BankError("table motion input unavailable");
        world->spell=*target;globals->rise_gate=1; // FF31B0 names the object; consumers test it for zero.
        anchor=SpellCountdown{a->position,a->flags,a->presentation,a->target,0x12c,next.control};
    } else {
        world->activation=*target;world->ingredient_timer=0x50;globals->table_loop_count=0;
    }
    dormant=table;world->records[r]->object=*target;
    // The walk then reads the released copy's handler, now 7A88.
    auto residue=table;residue.presentation.mode=0;
    step_table_motion(residue,*globals->table_loop_count);
    slots_[i].object=residue;return true;
}
void MixedPool::mix_spell(PickupWorld& world, PrivateGlobals* globals) {
    if (!world.spell) return; // CMPI.L #0,FF31B0; then 7CF0/7D06 return with A1 zero.
    if (!globals || !globals->table_loop_count) throw assets::BankError("7CC8 FF31BC unavailable");
    auto next=*this;auto g=*globals;auto w=world;
    w.ingredient_timer=static_cast<std::uint16_t>(w.ingredient_timer-1U);
    if (w.ingredient_timer & 0x8000U) { g.table_loop_count=static_cast<std::uint16_t>(*g.table_loop_count+1U);w.ingredient_timer=0x28; }
    if (w.activation) {
        auto* a0=std::get_if<TableMotion>(&next.slot_at(*w.activation).object);
        auto* a1=std::get_if<TableMotion>(&next.slot_at(*w.spell).object);
        if (!a0 || !a1) throw assets::BankError("7CC8 objects are not table objects");
        // TST.W +32(A0); BPL: CMPA/BCS swaps when A1 is lower, else CMPA/BHI when higher.
        const bool lower=w.spell->slot<w.activation->slot;
        if ((a0->delta_x & 0x8000U) ? !lower && w.spell->slot!=w.activation->slot : lower) {
            std::swap(a0->presentation.words,a1->presentation.words);std::swap(a0->presentation.counter,a1->presentation.counter);
            std::swap(a0->presentation.reload,a1->presentation.reload);std::swap(a0->countdown,a1->countdown);std::swap(a0->toggle,a1->toggle);
            std::swap(a0->delta_x,a1->delta_x);std::swap(a0->cursor,a1->cursor);std::swap(a0->position,a1->position);
        }
    }
    *this=std::move(next);*globals=g;world=std::move(w);
}
bool MixedPool::walk_delivered(EffectId id, PrivateGlobals& globals, PickupWorld& world) {
    if (!std::holds_alternative<DeliveredPickup>(at(id).object)) throw assets::BankError("pool object is not a delivered pickup");
    auto next=*this;auto g=globals;auto w=world;
    const bool released=next.walk_delivered_slot(id.slot,&g,&w);
    if (released) next.free_.push_back(id.slot);
    *this=std::move(next);globals=g;world=std::move(w);return released;
}
std::vector<PoolEvent> MixedPool::step(ActorId owner,Position position,TrailRandom& random,std::size_t budget,PrivateGlobals* shared,
        const CollisionInputs* collision,PickupWorld* pickups,TransitionState* transition,HubWorld* hub_world) {
    auto next=*this;auto rng=random;std::vector<PoolEvent> events;std::size_t updates=0;
    std::optional<PickupWorld> world;if (pickups) world=*pickups;
    std::optional<PrivateGlobals> state;if (shared) state=*shared;
    PrivateGlobals* const globals=state ? &*state : nullptr;
    std::optional<TransitionState> fade;if (transition) fade=*transition;
    TransitionState* const timer=fade ? &*fade : nullptr;
    std::optional<HubWorld> hub;if (hub_world) hub=*hub_world;
    for (std::size_t i=0;i<next.slots_.size();++i) {
        auto& slot=next.slots_[i];
        if (!active(slot.object)) {
            if (std::holds_alternative<ReturnOnlyObject>(slot.object))
                events.push_back({PoolEventKind::inactive,{i,slot.generation},slot.object});
            continue;
        }
        if (updates++>=budget) throw assets::BankError("mixed pool phase budget exhausted");
        bool released=false;
        if (auto* e=std::get_if<ReversalEffect>(&slot.object)) released=step_reversal_effect(*e,owner,position);
        else if (auto* p=std::get_if<TrailParticle>(&slot.object)) released=step_trail_particle(*p);
        else if (auto* e=std::get_if<TrailEmitter>(&slot.object)) {
            const auto particle=step_trail_emitter(*e,rng,owner,position,next.available()!=0,true);
            if (particle) {
                const auto id=next.spawn(*particle);
                events.push_back({PoolEventKind::spawn,id,next.at(id).object});
            }
        }
        else if (auto* p=std::get_if<PrivateObject>(&slot.object)) {
            if (!globals) throw assets::BankError("private object globals unavailable");
            step_private_object(*p,*globals,true);
        }
        else if (auto* p=std::get_if<TableMotion>(&slot.object)) {
            if (!globals || !globals->table_loop_count) throw assets::BankError("table motion input unavailable");
            step_table_motion(*p,*globals->table_loop_count,true);
        }
        else if (std::holds_alternative<CollisionProbe>(slot.object)) {
            if (!collision) throw assets::BankError("collision inputs unavailable");
            if (const auto ids=next.walk_probe_slot(i,*collision,globals ? &globals->rise_gate : nullptr,world ? &*world : nullptr))
                for (auto id:{ids->sparkle,ids->copy}) events.push_back({PoolEventKind::spawn,id,next.at(id).object});
        }
        else if (std::holds_alternative<Pickup>(slot.object)) {
            if (!collision) throw assets::BankError("collision inputs unavailable");
            released=next.walk_pickup_slot(i,*collision,world ? &*world : nullptr);
        }
        else if (auto* p=std::get_if<ReturnOnlyObject>(&slot.object)) step_return_only_object(*p);
        else if (auto* p=std::get_if<GatedLead>(&slot.object)) step_gated_lead(*p);
        else if (std::holds_alternative<DeliveredPickup>(slot.object)) released=next.walk_delivered_slot(i,globals,world ? &*world : nullptr);
        else if (std::holds_alternative<SpellCountdown>(slot.object)) next.walk_anchor_slot(i,world ? &*world : nullptr,globals,timer,events);
        else if (std::holds_alternative<SpellSparkle>(slot.object)) released=next.walk_sparkle_slot(i,rng,events);
        else if (auto* p=std::get_if<ExitDoor>(&slot.object)) {
            if (!world) throw assets::BankError("exit door world unavailable");
            const auto step=step_exit_door(*p,collision,world->two_player);
            if (step.dressed) {
                // 6FCA: sound 95, then 4C08 on the +36 sign at the door's new position.
                auto* sign=std::get_if<DoorSign>(&next.slot_at(p->sign).object);
                if (!sign) throw assets::BankError("exit door sign unavailable");
                world->sounds.push_back({0x95,2,0xc0,1});raise_door_sign(*sign,p->position);
            }
            if (step.entered) next.enter_exit_door(i,*world,events);
        }
        else if (auto* p=std::get_if<DoorSign>(&slot.object)) step_door_sign(*p);
        else if (auto* p=std::get_if<HubDoor>(&slot.object)) {
            if (!hub) throw assets::BankError("hub door world unavailable");
            const auto step=step_hub_door(*p,collision,hub->two_player);
            released=step.released;
            if (step.touched) next.enter_hub_door(i,*step.touched,*hub,timer,events);
        }
        if (released) next.free_.push_back(i);
        events.push_back({released ? PoolEventKind::release : PoolEventKind::update,{i,slot.generation},slot.object});
    }
    *this=std::move(next);random=rng;if (pickups) *pickups=std::move(*world);if (shared) *shared=*state;if (transition) *transition=*fade;
    if (hub_world) *hub_world=std::move(*hub);
    return events;
}
void MixedPool::walk_anchor_slot(std::size_t i, PickupWorld* world, PrivateGlobals* globals, TransitionState* timer, std::vector<PoolEvent>& events) {
    auto& slot=slots_[i];auto* p=&std::get<SpellCountdown>(slot.object);
    const auto step=step_spell_countdown(*p,timer);
    if (step==SpellStep::complete) {
        if (!world || !globals) throw assets::BankError("spell completion world unavailable");
        complete_spell(i,*world,*globals,*timer,events);
    } else if (step==SpellStep::revealed) // 7B92: +16 = 12646.
        slot.object=ReturnOnlyObject{p->position,p->flags,p->presentation,p->target,p->countdown,p->control};
}
bool MixedPool::walk_sparkle_slot(std::size_t i, TrailRandom& random, std::vector<PoolEvent>& events) {
    const auto step=step_spell_sparkle(std::get<SpellSparkle>(slots_[i].object),random,available()!=0);
    if (step.particle) {
        const auto id=spawn(*step.particle);
        events.push_back({PoolEventKind::spawn,id,at(id).object});
    }
    return step.released;
}
std::vector<PoolEvent> MixedPool::walk_sparkle(EffectId id, TrailRandom& random) {
    if (!std::holds_alternative<SpellSparkle>(at(id).object)) throw assets::BankError("pool object is not the spell sparkle");
    auto next=*this;auto rng=random;std::vector<PoolEvent> events;
    if (active(next.slots_[id.slot].object)) {
        const bool released=next.walk_sparkle_slot(id.slot,rng,events);
        if (released) next.free_.push_back(id.slot);
        events.push_back({released ? PoolEventKind::release : PoolEventKind::update,id,next.slots_[id.slot].object});
    }
    *this=std::move(next);random=rng;return events;
}
std::vector<PoolEvent> MixedPool::walk_anchor(EffectId id, PickupWorld& world, PrivateGlobals& globals, TransitionState& timer) {
    if (!std::holds_alternative<SpellCountdown>(at(id).object)) throw assets::BankError("pool object is not the spell anchor");
    auto next=*this;auto w=world;auto g=globals;auto t=timer;std::vector<PoolEvent> events;
    next.walk_anchor_slot(id.slot,&w,&g,&t,events);
    *this=std::move(next);world=std::move(w);globals=g;timer=t;return events;
}
void MixedPool::enter_exit_door(std::size_t i, PickupWorld& world, std::vector<PoolEvent>& events) {
    const auto door=std::get<ExitDoor>(slots_[i].object);
    // 7082: FF0F00 = the control (A5, FF0690 tested first); the anchor's +16 = 12646.
    world.exit_control=world.controls[0];
    if (world.anchor) {
        auto& anchor=slot_at(*world.anchor).object;
        if (const auto* a=std::get_if<SpellCountdown>(&anchor)) anchor=ReturnOnlyObject{a->position,a->flags,a->presentation,a->target,a->countdown,a->control};
        else if (!std::holds_alternative<ReturnOnlyObject>(anchor)) throw assets::BankError("FF31C0 names another object");
    }
    // 4CA2: FAA4 releases the +3A sign, then 59BC and the move.
    auto& sign=slot_at(door.sign);auto* g=std::get_if<DoorSign>(&sign.object);
    if (!g || !(g->presentation.mode & 0x80U)) throw assets::BankError("exit door sign unavailable");
    g->presentation.mode=0;free_.push_back(door.sign.slot);events.push_back({PoolEventKind::release,door.sign,sign.object});
    const auto vanished=vanish_exit_door(door);slots_[i].object=vanished;
    // 709A: with FF33E2 clear, the camera words from the moved door.
    if (!world.two_player)
        world.exit_camera=Position{static_cast<std::uint16_t>((vanished.position.x-0x10cU) & 0xfff8U),static_cast<std::uint16_t>((vanished.position.y-0xe0U) & 0xfff8U)};
    // 70D2..70F4: P1's actor and tracking selector (the session applies them); 70F8: the +1A2 link.
    world.door_entered=true;
    if (world.links[0] && active(at(*world.links[0]).object)) throw assets::BankError("unsupported 70FE active link at door entry");
}
void MixedPool::enter_hub_door(std::size_t i, std::size_t touched, HubWorld& hub, TransitionState* timer, std::vector<PoolEvent>& events) {
    if (!timer) throw assets::BankError("hub door entry timer unavailable");
    if (hub.entry) throw assets::BankError("second hub door entry in one loop");
    auto& door=std::get<HubDoor>(slots_[i].object);
    // 623C: 17298 on A5 (the touching control), then FF4446/FF4448 and FF3398.
    hub.entry=HubEntry{touched,door.number};
    timer->requested_position=hub_requested_position(door);hub.selected=door.number;
    vanish_hub_door(door);
    // 62DA/62E4: FA8C (CLR.B, push) on +26, then +2A.
    for (const auto id:door.numbers) {
        // FA8C would push a slot already on the free stack a second time.
        auto& object=slot_at(id).object;
        if (std::find(free_.begin(),free_.end(),id.slot)!=free_.end()) throw assets::BankError("hub door number object already free");
        std::visit([](auto& o){
            using T=std::decay_t<decltype(o)>;
            if constexpr (!std::is_same_v<T,std::monostate> && !std::is_same_v<T,ExternalReservation>) o.presentation.mode=0;
        },object);
        free_.push_back(id.slot);events.push_back({PoolEventKind::release,id,object});
    }
    // 62EE..6302: 630A on FF0690 and FF0838 (the session's), then 13208.
    start_transition(*timer);
}
void MixedPool::complete_spell(std::size_t i, PickupWorld& world, PrivateGlobals& globals, TransitionState& timer, std::vector<PoolEvent>& events) {
    auto& anchor=std::get<SpellCountdown>(slots_[i].object);
    // 7B60: D269 ("SPELL COMPLETED! / DOOR OPEN!") to the anchor's +4A control.
    const auto k=std::find(world.controls.begin(),world.controls.end(),anchor.control)-world.controls.begin();
    if (k==2 || !world.messages[static_cast<std::size_t>(k)]) throw assets::BankError("spell control message unavailable");
    if (const auto clear=post_message(*world.messages[static_cast<std::size_t>(k)],SetupMessage::spell_completed,world.message_tilemap))
        world.clears.push_back(*clear);
    // 7E18: the fruit of the FF31AC and FF31B0 objects, then 7ED6 on each.
    if (!world.activation || !world.spell) throw assets::BankError("7E18 ingredients unavailable");
    const std::array<EffectId,2> ids{*world.activation,*world.spell};
    std::array<std::uint16_t,2> fruit{};
    for (std::size_t n=0;n<2;++n) {
        const auto* table=std::get_if<TableMotion>(&slot_at(ids[n]).object);
        if (!table) throw assets::BankError("7E18 ingredient is not a table object");
        fruit[n]=ingredient_fruit(table->presentation.words[1]);
    }
    world.recipe=fruit;
    if (world.spell_flags) throw assets::BankError("unsupported 7ED6 FF31A8 path");
    for (const auto id:ids) {
        std::get<TableMotion>(slot_at(id).object).presentation.mode=0;
        // +42 names the record; its object is cleared and its FF312C entry set to FFFF.
        const auto r=std::find_if(world.records.begin(),world.records.end(),[&](const auto& x){return x && x->object==id;});
        if (r==world.records.end() || (*r)->entry>=world.kinds.size()) throw assets::BankError("7ED6 ingredient record unavailable");
        world.kinds[(*r)->entry]=0xffff;r->reset();
    }
    world.spell_flags=0;world.activation.reset();world.spell.reset();globals.rise_gate=0;
    const auto effect=recipe_effect(fruit[0],fruit[1]);
    if (!effect) throw assets::BankError("unsupported 9288 recipe");
    world.sounds.push_back({0x9c,7,0xc0,1});
    if (*effect!=0x8652) throw assets::BankError("unsupported recipe effect");
    // 8652: FF316C set selects 9182.
    if (world.pair_request) throw assets::BankError("unsupported 9182 recipe path");
    const auto origin=world.control_origin;
    const auto sparkle=allocate(make_spell_sparkle({origin.x,static_cast<std::uint16_t>(origin.y+0x18U)}));
    events.push_back({PoolEventKind::spawn,sparkle,at(sparkle).object});
    world.sounds.push_back({0x90,0x0b,0xc0,1});world.pair_request=0xffff;
    // 6F02: two F9E2 pops; the lower becomes the sign, the higher the door.
    const auto first=allocate(make_door_sign());const auto second=allocate(make_door_sign());
    if (world.two_player) throw assets::BankError("unsupported two-player 6F44 door position");
    const auto sign=first.slot<second.slot ? first : second;const auto door=first.slot<second.slot ? second : first;
    slot_at(door).object=make_exit_door(origin,world.controls[0],sign);world.door=door;
    for (const auto id:{first,second}) events.push_back({PoolEventKind::spawn,id,at(id).object});
    // 95EE: FF31A6 selects 9682 and FF31A4 9614.
    if (globals.flags_gate) throw assets::BankError("unsupported 95EE 9682 path");
    if (globals.hide_gate) throw assets::BankError("unsupported 95EE 9614 path");
    // 7B7A: JSR 1324E; 7B80: +16 = 7B8A.
    start_tally_transition(timer);anchor.phase=SpellPhase::reveal;
}
namespace {
bool anchor_object(const PoolObject& object) {
    return std::holds_alternative<ReturnOnlyObject>(object) || std::holds_alternative<SpellCountdown>(object);
}
void require_anchor(const MixedSessionState& state) {
    if (state.return_only_anchor && !anchor_object(state.pool.at(*state.return_only_anchor).object))
        throw assets::BankError("return-only anchor names another object");
    // No native producer replaces a dormant object or pickup, so each identity must stay live.
    for (const auto& id:state.dormant_anchors) if (id) state.pool.at(*id);
    for (const auto& id:state.control_links) if (id) state.pool.at(*id);
    for (const auto& r:state.pickup_records) if (r) state.pool.at(r->object);
    if (const auto& w=state.world) {
        for (const auto& id:w->links) if (id) state.pool.at(*id);
        for (const auto& id:w->dormant) if (id) state.pool.at(*id);
        for (const auto& r:w->records) if (r) state.pool.at(r->object);
        if (w->activation) state.pool.at(*w->activation);
        if (w->spell) state.pool.at(*w->spell);
        // FF316E keeps naming the door after 7082 turned it into a vanishing object.
        if (w->door && !std::holds_alternative<ExitDoor>(state.pool.at(*w->door).object) && !(w->exit_control && std::holds_alternative<TrailParticle>(state.pool.at(*w->door).object)))
            throw assets::BankError("FF316E names another object");
        if (w->anchor && !anchor_object(state.pool.at(*w->anchor).object)) throw assets::BankError("return-only anchor names another object");
    }
}
}
std::optional<MessageRowClear> post_message(ControlMessage& m, SetupMessage text, std::uint32_t tilemap) noexcept {
    // CB72: CMP.B +53,D0 then BLT, with D0 the message's leading priority byte.
    const std::int8_t priority=text==SetupMessage::mix_those_fruit || text==SetupMessage::fruit_returned ? 0x64 : 0x01;
    if (priority<static_cast<std::int8_t>(m.priority)) { m.message.reset();return {}; }
    m.message=text;m.priority=static_cast<std::uint8_t>(priority);
    return MessageRowClear{static_cast<std::uint16_t>(tilemap + 14U + static_cast<std::uint16_t>(m.row << 7))};
}
ObjectPair initialize_return_only_pair(MixedSessionState& state) {
    auto pool=state.pool;const auto pair=pool.initialize_return_only_pair();
    state.pool=std::move(pool);state.return_only_anchor=pair.second;return pair;
}
EffectId initialize_dormant(MixedSessionState& state, DormantAnchor anchor) {
    auto pool=state.pool;const auto id=pool.initialize_dormant();
    state.pool=std::move(pool);state.dormant_anchors[static_cast<std::size_t>(anchor)]=id;return id;
}
LevelSetupPrefix initialize_level_setup_prefix(MixedSessionState& state, ActorId control) {
    auto next=state;LevelSetupPrefix out{};
    out.dormant={initialize_dormant(next,DormantAnchor::first),initialize_dormant(next,DormantAnchor::second)};
    out.rising=next.pool.initialize_rising_pair(control);
    out.quad=next.pool.initialize_collision_quad(control);
    out.return_only=initialize_return_only_pair(next);
    out.visibility=next.pool.initialize_visibility_pair();
    state=std::move(next);return out;
}
std::vector<EffectId> initialize_pickups(MixedSessionState& state, const PickupTables& tables, ActorId control) {
    auto next=state;std::vector<EffectId> ids;
    next.pickup_records={};next.activation_target.reset();
    if (next.private_globals) next.private_globals->rise_gate=0;
    for (std::size_t entry=0;entry<tables.kinds.size();++entry) {
        if (tables.kinds[entry]==0xffff) continue;
        // FF4C80 advances only for created pickups; the record cursor likewise.
        const auto record=ids.size();
        const auto id=next.pool.initialize_pickup(control,tables.positions[record],tables.kinds[entry],tables.counts[entry],record);
        next.pickup_records[record]=PickupRecord{id,entry};ids.push_back(id);
    }
    state=std::move(next);return ids;
}
EffectId initialize_control_link(MixedSessionState& state, std::size_t player) {
    if (player>=state.control_links.size()) throw assets::BankError("unknown control link");
    auto pool=state.pool;const auto id=pool.initialize_dormant();
    state.pool=std::move(pool);state.control_links[player]=id;return id;
}
LevelSetupTail initialize_level_setup_tail(MixedSessionState& state, const PickupTables& tables, ActorId control) {
    auto next=state;LevelSetupTail out{};
    out.pickups=initialize_pickups(next,tables,control);
    out.control_links={initialize_control_link(next,0),initialize_control_link(next,1)};
    state=std::move(next);return out;
}
SetupMessageResult continue_level_setup(MixedSessionState& state, const PickupTables& tables) {
    if (!state.setup_gates) throw assets::BankError("setup gates unavailable");
    auto next=state;auto& gates=*next.setup_gates;SetupMessageResult out{};
    if (!gates.two_player) {
        if (gates.fruit_returned) { gates.fruit_returned=0;out.selected=SetupMessage::fruit_returned; }
        else if (std::count_if(tables.kinds.begin(),tables.kinds.end(),[](auto k){return k!=0xffff;})>=2) out.selected=SetupMessage::mix_those_fruit;
    }
    if (out.selected) {
        if (!next.p1_message) throw assets::BankError("control message fields unavailable");
        out.clear=post_message(*next.p1_message,*out.selected,gates.message_tilemap);
    }
    if (gates.two_player || gates.pair_request) throw assets::BankError("unsupported 6EF0 pair allocation");
    state=std::move(next);return out;
}
LevelSetupPairs initialize_gated_pairs(MixedSessionState& state, const GatedPairInputs& inputs) {
    auto pool=state.pool;LevelSetupPairs out{};
    for (std::size_t i=0;i<inputs.gates.size();++i) {
        if (!inputs.gates[i]) continue;
        const auto pair=static_cast<GatedPair>(i);
        if (pair==GatedPair::p2_placed && !inputs.p2_origin) throw assets::BankError("P2 control origin unavailable");
        out.pairs[i]=pool.initialize_gated_pair(pair,pair==GatedPair::p2_placed ? inputs.caller : inputs.p1_control,inputs.p2_origin.value_or(Position{}));
    }
    state.pool=std::move(pool);return out;
}
void establish_world(MixedSessionState& state, const PickupTables& tables, std::array<ActorId,2> controls,
        ControlMessage p2, std::uint16_t ingredient_timer) {
    if (state.world) throw assets::BankError("world already established");
    if (!state.p1_message || !state.setup_gates) throw assets::BankError("setup message fields unavailable");
    // 6A94 cleared FF31B0; a nonzero value would name an object the world does not know.
    if (state.private_globals && state.private_globals->rise_gate) throw assets::BankError("FF31B0 names an unknown object");
    auto next=state;PickupWorld world;
    world.controls=controls;world.links=next.control_links;world.records=next.pickup_records;world.kinds=tables.kinds;
    world.activation=next.activation_target;world.dormant=next.dormant_anchors;world.messages={next.p1_message,p2};
    world.message_tilemap=next.setup_gates->message_tilemap;world.ingredient_timer=ingredient_timer;world.anchor=next.return_only_anchor;
    world.pair_request=next.setup_gates->pair_request;world.two_player=next.setup_gates->two_player!=0;
    next.control_links={};next.pickup_records={};next.activation_target.reset();next.dormant_anchors={};next.p1_message.reset();next.return_only_anchor.reset();
    next.world=std::move(world);
    require_anchor(next);
    state=std::move(next);
}
MixedPool reset_object_pool() {
    std::vector<std::size_t> free(68);
    for (std::size_t i=0;i<free.size();++i) free[i]=i;
    return MixedPool(std::vector<PoolObject>(free.size()),free);
}
HubSceneEntry enter_hub_scene(MixedSessionState& state, const HubSceneInputs& inputs) {
    if (!state.p1.transition || !state.p1.actions) throw assets::BankError("scene change timer or action globals unavailable");
    if (state.p1.effects) throw assets::BankError("scene change with a dedicated effect pool");
    if (inputs.two_player) throw assets::BankError("unsupported two-player scene change");
    auto next=state;HubSceneEntry out;auto& p1=next.p1;auto& timer=*p1.transition;
    // 0x488, then 9880's 98DE/9952 on FF0690.
    p1.actor=make_hub_actor(timer.requested_position);p1.tracking.selector=0;
    out.parameters=hub_actor_parameters(inputs.slow);
    // 16EA4: 17024 and F850, FF0F16 cleared (`acceleration_gate` stays 0), then 131C2 and FF0B92 = 001E.
    next.pool=reset_object_pool();out.acceleration_gate=0;
    start_fade_in(timer);timer.countdown=0x1e;
    next.world.reset();next.private_globals.reset();next.return_only_anchor.reset();next.dormant_anchors={};next.control_links={};
    next.pickup_records={};next.activation_target.reset();next.p1_message.reset();next.setup_gates.reset();
    p1.actions->mode=7; // 5D58
    next.hub=HubWorld{inputs.table,inputs.two_player,{},{}};
    out.doors=initialize_hub(next,inputs.stage);
    // 5E8E: single player, 63E2 with D1 = 000D.
    out.banner=request_level_banner(inputs.banner,p1.scratch);
    timer.countdown=0x0a; // 5ED4
    state=std::move(next);return out;
}
namespace {
// 16EA4 as it changes the carried session: 17024 and F850, FF0F16 cleared, then
// 131C2 and FF0B92 = 001E. Every world the session carried is dropped.
void reset_scene(MixedSessionState& state) {
    state.p1.actor={};state.p1.actor.motion.update=MotionUpdate::return_only;state.p1.actor.service=ActorService::return_only;
    state.pool=reset_object_pool();
    start_fade_in(*state.p1.transition);state.p1.transition->countdown=0x1e;
    state.world.reset();state.private_globals.reset();state.return_only_anchor.reset();state.dormant_anchors={};state.control_links={};
    state.pickup_records={};state.activation_target.reset();state.p1_message.reset();state.setup_gates.reset();state.hub.reset();
}
}
HintScreen enter_hint_screen(MixedSessionState& state) {
    if (!state.p1.transition || !state.p1.actions) throw assets::BankError("hint screen timer or action globals unavailable");
    if (state.p1.effects) throw assets::BankError("hint screen with a dedicated effect pool");
    auto next=state;reset_scene(next);
    state=std::move(next);return {};
}
std::uint16_t choose_action_cooldown(std::uint16_t range, TrailRandom& random) noexcept {
    if (static_cast<std::int16_t>(range)>0x0a) return 0xffff;
    if (!range) return 0;
    return static_cast<std::uint16_t>((next_trail_random(random) & 0xffffU) % range + 2U);
}
SecondLevelEntry enter_second_level(MixedSessionState& state, const SecondLevelInputs& inputs) {
    if (!state.p1.transition || !state.p1.actions) throw assets::BankError("second level timer or action globals unavailable");
    if (state.p1.effects) throw assets::BankError("second level with a dedicated effect pool");
    if (inputs.two_player) throw assets::BankError("unsupported two-player second level");
    if (!inputs.random_before) throw assets::BankError("54BA draws E918 at least once");
    auto next=state;auto& p1=next.p1;
    reset_scene(next); // E2A's 16EA4
    p1.transition->saved_position={};p1.actor=make_hub_actor(p1.transition->saved_position);p1.tracking.selector=0; // +A2/+A4 cleared, 9880
    for (unsigned n=0;n<inputs.random_before;++n) next_trail_random(next.random); // 54BA
    p1.actions->cooldown=choose_action_cooldown(inputs.cooldown_range,next.random);
    for (unsigned n=0;n<inputs.random_after;++n) next_trail_random(next.random);
    reset_actor_appearance(p1.actor); // 9952
    p1.actions->mode=0x13; // 0x774
    state=std::move(next);
    return {hub_actor_parameters(inputs.slow),0};
}
std::vector<EffectId> initialize_hub(MixedSessionState& state, std::uint16_t stage) {
    if (!state.hub) throw assets::BankError("hub world unavailable");
    if (state.world) throw assets::BankError("hub world beside a level world");
    auto next=state;auto& hub=*next.hub;
    update_hub_door_states(hub.table,stage,hub.two_player);
    const auto ids=next.pool.initialize_hub_doors(hub.table,hub.two_player);
    state=std::move(next);return ids;
}
WorldPhaseResult step_world_phase(MixedSessionState& state, ActorId owner, Position position,
        const CollisionInputs* collision, std::size_t budget, const WorldUpdates& updates) {
    if (state.hub && state.world) throw assets::BankError("hub world beside a level world");
    auto next=state;WorldPhaseResult out;
    for (std::size_t k=0;k<updates.messages.size();++k) if (updates.messages[k]) {
        if (!next.world) throw assets::BankError("message update without a world");
        next.world->messages[k]=updates.messages[k];
    }
    for (unsigned n=0;n<updates.random_calls;++n) next_trail_random(next.random);
    // The frame's 7CC8 call (BSR at 6972) precedes P1's last input conversion;
    // P1 reads nothing it changes, so it runs here, before the loop.
    if (next.world) next.pool.mix_spell(*next.world,next.private_globals ? &*next.private_globals : nullptr);
    out.events=next.pool.step(owner,position,next.random,budget,next.private_globals ? &*next.private_globals : nullptr,collision,
        next.world ? &*next.world : nullptr,next.p1.transition ? &*next.p1.transition : nullptr,next.hub ? &*next.hub : nullptr);
    if (next.hub && next.hub->entry) {
        // 62EE: 630A on FF0690 (P1; the FF0838 call is reported, not native).
        begin_coasting(next.p1.actor,next.p1.tracking);out.hub_entry=next.hub->entry;next.hub->entry.reset();
    }
    if (next.world && next.world->door_entered) {
        // 7082's tail on the control's actor, as 630A does for coasting.
        begin_exit_transition(next.p1.actor,next.p1.tracking);next.world->door_entered=false;
    }
    if (next.world) {
        out.sounds=std::move(next.world->sounds);next.world->sounds.clear();
        out.clears=std::move(next.world->clears);next.world->clears.clear();
    }
    require_anchor(next);
    state=std::move(next);return out;
}
MixedSessionResult step_mixed_session(const assets::SceneResource& scene,const assets::PatternBank& bank,
        MixedSessionState& state,const P1SessionConfig& config,ThreeButtonPad held,const WorldUpdates& updates) {
    if (state.p1.effects) throw assets::BankError("mixed session cannot also own a dedicated effect pool");
    if (state.p1.invocations>=config.max_invocations) throw assets::BankError("mixed session invocation budget exhausted");
    auto next=state;auto& p1=next.p1;MixedSessionResult result;
    if (p1.transition) { step_transition_timer(*p1.transition);result.p1.transition=p1.transition; }
    if (config.banner) result.p1.banner=request_level_banner(*config.banner,p1.scratch);
    p1.control=produce_pad_control(held);
    // The level loop's 179F8 (6554) is not native; the hub loop has none, so
    // there Up/Down reach only P1's actor (its action globals are required).
    if (p1.control.start || ((p1.control.up || p1.control.down) && !(next.hub && p1.actions)))
        throw assets::BankError("mixed session pause/up/down world scheduling unsupported");
    // The wrapper only produces reversals; it never reads or updates an existing
    // object. Stage its allocations with exactly the shared available capacity,
    // then map requests in order to shared identities before any world object runs.
    ReversalEffects pending(next.pool.available());
    result.p1.actor=step_actor_dispatch(scene,bank,p1.actor,p1.tracking,config.parameters,
        actor_input(p1.control,config.acceleration_gate),p1.scratch,config.actor_budget,{&pending,config.owner},
        p1.actions ? &*p1.actions : nullptr,p1.transition ? &*p1.transition : nullptr);
    result.p1.wrapper_actor=p1.actor;result.p1.wrapper_tracking=p1.tracking;
    for (auto& id:result.p1.actor.spawned_effects) {
        id=next.pool.spawn(pending.at(id));
        result.events.push_back({PoolEventKind::spawn,id,next.pool.at(id).object});
    }
    // AC5E consumes the wrapper's control coordinates, not actor coordinates.
    std::optional<CollisionInputs> collision;
    if (next.collision) collision=CollisionInputs{p1.tracking.position,*next.collision};
    auto phase=step_world_phase(next,config.owner,p1.actor.motion.position,collision ? &*collision : nullptr,config.effect_budget,updates);
    result.events.insert(result.events.end(),phase.events.begin(),phase.events.end());++p1.invocations;
    result.world_sounds=std::move(phase.sounds);result.clears=std::move(phase.clears);result.hub_entry=phase.hub_entry;
    if (next.hub) {
        if (!p1.transition) throw assets::BankError("hub loop timer unavailable");
        result.scene_ended=hub_loop_ends(p1.tracking.selector,*p1.transition);
    }
    static_assert(std::is_nothrow_move_assignable_v<MixedSessionState>);
    state=std::move(next);return result;
}
} // namespace wiz::sim
