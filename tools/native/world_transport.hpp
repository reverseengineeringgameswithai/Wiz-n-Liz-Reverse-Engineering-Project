#pragma once
#include "delivery_transport.hpp"

namespace wiz::transport {
// A world object: its variant index, then its fields by type. 3 particle: x y
// flags mode w06 w08 w0a c0c r0d target; 4 emitter: the eleven fields (+10 the
// carried count), +36, ten history words, owner, extents, record; 5 private:
// update and the eleven fields, control; 6 table: the eleven fields, control,
// cursor, +32, +36; 7 probe: the eleven fields, control, extents; 8
// return-only: the eleven fields, control; 9 pickup: the eleven fields,
// control, extents, record, phase; 10 lead: the eleven fields, control, pair,
// partner slot and generation; 11 copy: the eleven fields (+10 the carried
// count), control, frames, extents, record; 12 spell anchor: the eleven
// fields (+10 the countdown), control, phase; 13 sparkle: the eleven fields
// (+10 the countdown), extents; 14 door: phase, the eleven fields, extents,
// control, sign slot; 15 sign: raised, x, y, flags, mode, frame, cursor; 2
// reversal effect (P1's): side, x, y, flags, mode, frames, counter, reload,
// target, owner (the session's logical P1).
inline void print_world_object(const sim::PoolObject& object) {
    std::cout<<' '<<object.index();
    std::visit([](const auto& o) {
        using T=std::decay_t<decltype(o)>;
        if constexpr (std::is_same_v<T,sim::ReversalEffect>) {
            const auto& q=o.presentation;
            for(auto v:std::array<unsigned,11>{static_cast<unsigned>(o.side),o.position.x,o.position.y,o.flags,q.mode,q.words[0],q.words[1],q.words[2],q.counter,q.reload,o.target})std::cout<<' '<<v;
            std::cout<<' '<<o.owner.value;
        } else if constexpr (std::is_same_v<T,sim::TrailParticle>) {
            const auto& q=o.presentation;
            for(auto v:std::array<unsigned,10>{o.position.x,o.position.y,o.flags,q.mode,q.words[0],q.words[1],q.words[2],q.counter,q.reload,o.target})std::cout<<' '<<v;
        } else if constexpr (std::is_same_v<T,sim::TrailEmitter>) {
            if(!o.carried) throw assets::BankError("world emitter without carried pickup");
            print_hit_fields(o,o.carried->count);std::cout<<' '<<o.countdown;
            for(const auto& h:o.history)std::cout<<' '<<h.x<<' '<<h.y;
            std::cout<<' '<<o.owner.value<<' '<<o.carried->x_extent<<' '<<o.carried->y_extent<<' '<<o.carried->record;
        } else if constexpr (std::is_same_v<T,sim::PrivateObject>) {
            std::cout<<' '<<static_cast<unsigned>(o.update);print_hit_fields(o,o.countdown);std::cout<<' '<<o.control.value;
        } else if constexpr (std::is_same_v<T,sim::TableMotion>) {
            print_hit_fields(o,o.countdown);std::cout<<' '<<o.control.value<<' '<<o.cursor<<' '<<o.delta_x<<' '<<o.toggle;
        } else if constexpr (std::is_same_v<T,sim::CollisionProbe>) {
            print_hit_fields(o,o.countdown);std::cout<<' '<<o.control.value<<' '<<o.x_extent<<' '<<o.y_extent;
        } else if constexpr (std::is_same_v<T,sim::ReturnOnlyObject>) {
            print_hit_fields(o,o.countdown);std::cout<<' '<<o.control.value;
        } else if constexpr (std::is_same_v<T,sim::Pickup>) {
            print_hit_fields(o,o.countdown);std::cout<<' '<<o.control.value<<' '<<o.x_extent<<' '<<o.y_extent<<' '<<o.record<<' '<<static_cast<unsigned>(o.phase);
        } else if constexpr (std::is_same_v<T,sim::GatedLead>) {
            print_hit_fields(o,o.countdown);std::cout<<' '<<o.control.value<<' '<<static_cast<unsigned>(o.pair)<<' '<<o.partner.slot<<' '<<o.partner.generation;
        } else if constexpr (std::is_same_v<T,sim::SpellCountdown>) {
            print_hit_fields(o,o.countdown);std::cout<<' '<<o.control.value<<' '<<static_cast<unsigned>(o.phase);
        } else if constexpr (std::is_same_v<T,sim::SpellSparkle>) {
            print_hit_fields(o,o.countdown);std::cout<<' '<<o.x_extent<<' '<<o.y_extent;
        } else if constexpr (std::is_same_v<T,sim::ExitDoor>) {
            std::cout<<' '<<static_cast<unsigned>(o.phase);print_hit_fields(o,o.countdown);std::cout<<' '<<o.x_extent<<' '<<o.y_extent<<' '<<o.control.value<<' '<<o.sign.slot;
        } else if constexpr (std::is_same_v<T,sim::DoorSign>) {
            std::cout<<' '<<o.bobbing<<' '<<o.position.x<<' '<<o.position.y<<' '<<o.flags<<' '<<unsigned(o.presentation.mode)<<' '<<o.presentation.words[0]<<' '<<o.cursor;
        } else if constexpr (std::is_same_v<T,sim::DeliveredPickup>) {
            print_hit_fields(o,o.carried.count);
            std::cout<<' '<<o.control.value<<' '<<o.frames[0]<<' '<<o.frames[1]<<' '<<o.carried.x_extent<<' '<<o.carried.y_extent<<' '<<o.carried.record;
        } else throw assets::BankError("unexpected world object");
    },object);
}
inline unsigned message_code(const std::optional<sim::ControlMessage>& m) {
    if(!m) throw assets::BankError("world control message unavailable");
    return m->message ? static_cast<unsigned>(*m->message)+1 : 0U;
}
inline sim::ControlMessage world_message(std::uint32_t code, std::uint32_t priority, std::uint32_t row) {
    if(code>4 || priority>255 || row>65535) throw assets::BankError("world message outside range");
    return {code ? std::optional{static_cast<sim::SetupMessage>(code-1)} : std::nullopt,static_cast<std::uint8_t>(priority),static_cast<std::uint16_t>(row)};
}
// Free stack, E918 state and mirror, sixteen records (present slot generation
// entry), FF31AC, both +1A2 links, FF31B4/FF31B8, FF31C0, FF31B0 and FF316E
// (present slot generation each), both controls' +46 code, +53 and +56, FF31BE,
// the private globals (FF31B0 nonzero, FF31A6, FF31A4, FF31BC presence and
// value), FF316C, FF31A8, FF31C4/FF31C6 (presence and both), FF0F00 (the exit
// control, 0 until 7082), FF444A/FF444C (presence and both), the loop's FCB32
// requests and CB9A row clears, then each link's object.
inline void print_world_state(const sim::MixedSessionState& state, const std::vector<sim::SoundRequest>& sounds,
        const std::vector<sim::MessageRowClear>& clears) {
    const auto& pool=state.pool;const auto& world=*state.world;const auto& globals=*state.private_globals;
    std::cout<<' '<<pool.available();for(auto i:pool.free_stack())std::cout<<' '<<i;
    std::cout<<' '<<state.random.state<<' '<<state.random.mirror;
    for(const auto& r:world.records) std::cout<<' '<<bool(r)<<' '<<(r ? r->object.slot : 0)<<' '<<(r ? r->object.generation : 0)<<' '<<(r ? r->entry : 0);
    print_anchor(world.activation);
    for(const auto& l:world.links) print_anchor(l);
    for(const auto& d:world.dormant) print_anchor(d);
    print_anchor(world.anchor);print_anchor(world.spell);print_anchor(world.door);
    for(const auto& m:world.messages) std::cout<<' '<<message_code(m)<<' '<<unsigned(m->priority)<<' '<<m->row;
    std::cout<<' '<<world.ingredient_timer<<' '<<bool(globals.rise_gate)<<' '<<globals.flags_gate<<' '<<globals.hide_gate<<' '<<bool(globals.table_loop_count)<<' '<<globals.table_loop_count.value_or(0);
    std::cout<<' '<<world.pair_request<<' '<<world.spell_flags<<' '<<bool(world.recipe)<<' '<<(world.recipe ? (*world.recipe)[0] : 0)<<' '<<(world.recipe ? (*world.recipe)[1] : 0);
    std::cout<<' '<<(world.exit_control ? world.exit_control->value : 0U)<<' '<<bool(world.exit_camera)<<' '<<(world.exit_camera ? world.exit_camera->x : 0)<<' '<<(world.exit_camera ? world.exit_camera->y : 0);
    std::cout<<' '<<sounds.size();
    for(const auto& q:sounds)std::cout<<' '<<q.id<<' '<<q.priority<<' '<<q.parameter<<' '<<q.selector;
    std::cout<<' '<<clears.size();for(const auto& c:clears)std::cout<<' '<<c.vram;
    for(const auto& l:world.links) if(l) print_world_object(pool.at(*l).object);
}
// The rows of a retained world's [6886,68D4) setup, read and checked before
// anything runs: the 6886-entry free row and slot rows (tag 9 carries verified
// inheritance), the 64 table words, 7DB8's "two_player fruit_returned
// pair_request tilemap p1_code p1_priority p1_row", [68C4,68D4)'s "g3172 g3174
// g3176 g3178 p2_present p2x p2y caller" and the world's "p2_code p2_priority
// p2_row FF31B0 FF31A6 FF31A4 FF31BE random mirror FF31A8 origin_x origin_y"
// (FF31BC starts absent; the origin is FF0690's +3C/+3E).
struct WorldRows {
    sim::MixedPool pool;
    sim::PickupTables tables;
    std::vector<std::uint32_t> message, gated, world;
};
inline WorldRows world_rows(std::istream& input, std::uint32_t slots, std::uint32_t free_count) {
    if(slots>4096 || free_count>slots) throw assets::BankError("invalid world pool header");
    WorldRows r{pool_seed(input,slots,free_count),{},{},{},{}};
    r.tables=pickup_tables(pool_row(input),0);
    r.message=pool_row(input);
    if(r.message.size()!=7 || r.message[0]>65535 || r.message[1]>65535 || r.message[2]>65535) throw assets::BankError("invalid world setup message row");
    r.gated=pool_row(input);
    if(r.gated.size()!=8 || r.gated[4]>1 || (r.gated[7]!=1 && r.gated[7]!=2)) throw assets::BankError("invalid world gated pair row");
    for(std::size_t i=0;i<7;++i) if(r.gated[i]>65535) throw assets::BankError("world gated pair word outside range");
    r.world=pool_row(input);
    if(r.world.size()!=12 || r.world[4]>65535 || r.world[5]>65535 || r.world[6]>65535 || r.world[9]>65535 || r.world[10]>65535 || r.world[11]>65535)
        throw assets::BankError("invalid world row");
    return r;
}
// Runs the setup with logical controls 1 (FF0690) and 2 (FF0838), establishes
// the world and prints the setup line: the identities (twelve prefix, the
// pickups, two links, any open gated pair's partner and lead), 7DB8's selection,
// clear presence and VRAM, the open-gate mask, the world state and every setup
// member. `p1` seeds a session's player; codes are 0 none, 1 MIX THOSE FRUIT,
// 2 FRUIT RETURNED, 3 FIRST and 4 SECOND INGREDIENT.
inline sim::MixedSessionState world_setup(WorldRows rows, sim::P1SessionState p1 = {}) {
    const auto& m=rows.message;const auto& g=rows.gated;const auto& w=rows.world;const auto& t=rows.tables;
    const sim::ActorId control{1},second{2};
    sim::MixedSessionState state{std::move(p1),std::move(rows.pool),{w[7],w[8]}};
    state.private_globals=sim::PrivateGlobals{w[3],static_cast<std::uint16_t>(w[4]),static_cast<std::uint16_t>(w[5])};
    state.setup_gates=sim::SetupGates{static_cast<std::uint16_t>(m[0]),static_cast<std::uint16_t>(m[1]),static_cast<std::uint16_t>(m[2]),m[3]};
    state.p1_message=world_message(m[4],m[5],m[6]);
    const auto prefix=sim::initialize_level_setup_prefix(state,control);
    const auto tail=sim::initialize_level_setup_tail(state,t,control);
    const auto selected=sim::continue_level_setup(state,t);
    sim::GatedPairInputs inputs{{},{},{g[7]},control};
    for(std::size_t i=0;i<4;++i) inputs.gates[i]=static_cast<std::uint16_t>(g[i]);
    if(g[4]) inputs.p2_origin=sim::Position{static_cast<std::uint16_t>(g[5]),static_cast<std::uint16_t>(g[6])};
    else if(g[5] || g[6]) throw assets::BankError("unconsumed P2 origin");
    const auto pairs=sim::initialize_gated_pairs(state,inputs);
    sim::establish_world(state,t,{control,second},world_message(w[0],w[1],w[2]),static_cast<std::uint16_t>(w[6]));
    state.world->spell_flags=static_cast<std::uint16_t>(w[9]);state.world->control_origin={static_cast<std::uint16_t>(w[10]),static_cast<std::uint16_t>(w[11])};
    auto members=group_ids(prefix);
    members.insert(members.end(),tail.pickups.begin(),tail.pickups.end());
    members.insert(members.end(),tail.control_links.begin(),tail.control_links.end());
    for(auto id:group_ids(pairs)) members.push_back(id);
    for(std::size_t i=0;i<members.size();++i) std::cout<<(i ? " " : "")<<members[i].slot<<' '<<members[i].generation;
    unsigned mask=0;for(std::size_t i=0;i<4;++i) mask|=pairs.pairs[i] ? 1U<<i : 0U;
    std::cout<<' '<<(selected.selected ? static_cast<unsigned>(*selected.selected)+1 : 0U)<<' '<<bool(selected.clear)<<' '<<(selected.clear ? selected.clear->vram : 0)<<' '<<mask;
    print_world_state(state,{},{});
    for(const auto& id:members) print_world_object(state.pool.at(id).object);
    std::cout<<'\n';
    return state;
}
// Per-control "present code priority row" message updates starting at f[j]:
// the non-native producer's change of that control's fields (0 keeps them).
inline std::array<std::optional<sim::ControlMessage>,2> world_message_updates(const std::vector<std::uint32_t>& f, std::size_t j) {
    std::array<std::optional<sim::ControlMessage>,2> out;
    for(std::size_t k=0;k<2;++k,j+=4) {
        if(f[j]>1) throw assets::BankError("invalid message update presence");
        if(f[j]) out[k]=world_message(f[j+1],f[j+2],f[j+3]);
        else if(f[j+1] || f[j+2] || f[j+3]) throw assets::BankError("message fields without update");
    }
    return out;
}
// One loop's events (kind slot generation and the object), then the world state.
inline void print_world_phase(const sim::MixedSessionState& state, const std::vector<sim::PoolEvent>& events,
        const std::vector<sim::SoundRequest>& sounds, const std::vector<sim::MessageRowClear>& clears) {
    std::cout<<events.size();
    for(const auto& e:events){std::cout<<' '<<static_cast<unsigned>(e.kind)<<' '<<e.id.slot<<' '<<e.id.generation;print_world_object(e.object);}
    print_world_state(state,sounds,clears);
}
// A loop with P1's effects supplied: "p1x p1y mask gate present p2x p2y
// owner_present ox oy calls" and the two message updates. The owner is the
// resolved (FF0690)+02/+04, consumed only by an emitter; `calls` counts E918
// calls by non-world code since the previous loop.
struct SuppliedPhase { sim::CollisionInputs collision; std::optional<sim::Position> owner; sim::WorldUpdates updates; };
inline SuppliedPhase supplied_phase(const std::vector<std::uint32_t>& f) {
    if(f.size()!=19 || f[4]>1 || f[7]>1 || f[10]>64) throw assets::BankError("invalid world phase");
    for(std::size_t i=0;i<10;++i) if(f[i]>65535) throw assets::BankError("world phase word outside range");
    auto v=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
    SuppliedPhase p{{{v(0),v(1)},{v(2),v(3),{}}},{},{f[10],world_message_updates(f,11)}};
    if(f[4]) p.collision.config.secondary=sim::Position{v(5),v(6)};
    else if(f[5] || f[6]) throw assets::BankError("unconsumed secondary coordinates in phase");
    if(f[7]) p.owner=sim::Position{v(8),v(9)};
    else if(f[8] || f[9]) throw assets::BankError("owner coordinates without owner");
    return p;
}
// Runs and prints one supplied loop; an owner position no emitter consumes rejects.
inline void step_supplied_phase(sim::MixedSessionState& state, const SuppliedPhase& p) {
    const auto phase=sim::step_world_phase(state,p.owner ? sim::ActorId{1} : sim::ActorId{},p.owner.value_or(sim::Position{}),&p.collision,state.pool.slots().size(),p.updates);
    const bool emitted=std::any_of(phase.events.begin(),phase.events.end(),[](const auto& e){return e.kind!=sim::PoolEventKind::spawn && std::holds_alternative<sim::TrailEmitter>(e.object);});
    if(p.owner && !emitted) throw assets::BankError("unconsumed owner position");
    print_world_phase(state,phase.events,phase.sounds,phase.clears);
    std::cout<<'\n';
}
// The retained level world without a native player: "slots free phases", the
// world_rows rows, then one supplied_phase row per phase. Prints the setup line,
// then one world_phase line per phase.
inline void world_pool(std::istream& input) {
    const auto h=pool_row(input);
    if(h.size()!=3 || h[2]>4096) throw assets::BankError("invalid world pool header");
    auto rows=world_rows(input,h[0],h[1]);
    std::vector<SuppliedPhase> phases;
    for(unsigned n=0;n<h[2];++n) phases.push_back(supplied_phase(pool_row(input)));
    if(input.peek()!=std::char_traits<char>::eof()) throw assets::BankError("unconsumed world pool input");
    auto state=world_setup(std::move(rows));
    for(const auto& p:phases) step_supplied_phase(state,p);
}
} // namespace wiz::transport
