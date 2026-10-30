#include "sim/session.hpp"
#include "hub_transport.hpp"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string_view>

namespace {
using namespace wiz;
template<std::size_t N> std::array<unsigned,N> fields(const std::string& line) {
    if (line.size()>512) throw assets::BankError("session row exceeds limit");
    std::array<unsigned,N> values{};std::istringstream input(line);std::string extra;
    for (auto& v:values) if (!(input>>v)) throw assets::BankError("incomplete session row");
    if (input>>extra) throw assets::BankError("extra session field");
    return values;
}
void print_control(sim::PadControl p) {
    for (auto v:{p.raw,p.any_action,p.jump,p.drop,p.up,p.down,p.left,p.right,p.a,p.b,p.c,p.start})
        std::cout<<unsigned(v)<<' ';
}
void print_banner(const sim::LevelBannerRequest& r) {
    std::cout<<unsigned(r.label)<<' '<<r.destination<<' '
        <<bool(r.number)<<' '<<(r.number ? r.number->value : 0)<<' '<<(r.number ? r.number->destination : 0);
}
std::vector<std::uint8_t> resource(const char* path,std::size_t limit) {
    std::ifstream input(path,std::ios::binary|std::ios::ate);const auto size=input.tellg();
    if (!input || size<2 || size>static_cast<std::streamoff>(limit)) throw assets::BankError("session resource outside limits");
    std::vector<std::uint8_t> data(static_cast<std::size_t>(size));input.seekg(0);
    if (!input.read(reinterpret_cast<char*>(data.data()),static_cast<std::streamsize>(data.size())) || input.peek()!=std::char_traits<char>::eof())
        throw assets::BankError("session resource changed");
    return data;
}
}
int main(int argc,char** argv) {
    using namespace wiz;
    try {
        std::string line;
        if (argc==2 && std::string_view(argv[1])=="--pad") {
            std::size_t count=0;
            while (std::getline(std::cin,line)) {
                const auto f=fields<1>(line);
                if (f[0]>255 || ++count>1000000) throw assets::BankError("invalid raw pad byte");
                print_control(sim::convert_pad_byte(static_cast<std::uint8_t>(f[0])));std::cout<<'\n';
            }
        } else if (argc==2 && std::string_view(argv[1])=="--banner") {
            std::size_t count=0;
            while (std::getline(std::cin,line)) {
                const auto f=fields<5>(line);
                if (++count>1000000 || f[0]>3 || f[1]>65535 || f[2]>65535 || f[3]>65535 || f[4]>65535)
                    throw assets::BankError("invalid level banner input");
                sim::TerrainScratch scratch{static_cast<std::uint16_t>(f[3]),static_cast<std::uint16_t>(f[4])};
                const auto r=sim::request_level_banner({static_cast<sim::Difficulty>(f[0]),static_cast<std::uint16_t>(f[1]),static_cast<std::uint16_t>(f[2])},scratch);
                std::cout<<scratch.x<<' '<<scratch.y<<' ';print_banner(r);std::cout<<'\n';
            }
        } else {
            // --world-session: after the seed, the 1345A timer row "direction
            // countdown reload level"; the retained level world from its setup
            // (world_rows rows and a collision config row "mask gate present p2x
            // p2y"), then a count row and that many supplied_phase loops before P1
            // runs natively, then per frame "held calls" and the two
            // world_message_updates: the timer, P1 from the seed row and every
            // object loop with P1's own effects. Each frame prints the timer's
            // four words after the banner.
            // --hub-session: after the seed and the timer row, the scene between
            // levels: "two_player stage record" (FF3398) and nine FF330C records of
            // seven words, the free stack "depth slots..." (68 slots, bottom
            // first), the collision row; then per frame the held set. It prints
            // the setup's pool image and record states, then per frame P1, the
            // timer after 1345A, FF4446/FF4448, FF3398, the loop's 623C entry
            // ("0" or "1 control number"), whether 6024 ends the scene and the
            // pool image.
            // --game-session (with the hub's scene and bank after it): the
            // --world-session rows with a "frames" row before the level's frames,
            // then the scene change "two_player slow stage difficulty record" and
            // nine records (enter_hub_scene; the hub's terrain from then on), then
            // the hub's held sets. It prints the level's lines, the scene change
            // (P1 as a 32-field seed, the 14-field timer row, the banner request,
            // the pool image and record states) and the hub's lines.
            // With the second level's scene and bank as well, after the hub's
            // last loop: "hint two_player slow cooldown_range random_before
            // random_after", then a held set per hint-screen loop
            // (step_hint_screen) and per second-level loop (P1 alone on that
            // terrain). It prints per hint loop the timer, FF0F10 and FF0F0E
            // after the loop and whether the screen returned; the entry (P1 as a
            // 32-field seed, the 14-field timer row, E918's state and mirror);
            // per second-level loop P1's line with the timer after 1345A and
            // FF33D8/FF33E0.
            const bool game=(argc==8 || argc==10) && std::string_view(argv[5])=="--game-session";
            const bool hub=argc==6 && std::string_view(argv[5])=="--hub-session";
            const bool carried=game || (argc==6 && std::string_view(argv[5])=="--world-session");
            const bool mixed=carried || hub || (argc==6 && std::string_view(argv[5])=="--mixed-session");
            const bool effects=argc==6 && std::string_view(argv[5])=="--reversal-session";
            const bool banner=(mixed && !hub) || effects || (argc==6 && std::string_view(argv[5])=="--level-banner");
            if (argc!=5 && !banner && !hub) throw assets::BankError("usage: wiznliz-session --pad|--banner OR scene-id scene.bin bank-id bank.bin [--level-banner|--reversal-session|--mixed-session|--world-session|--hub-session|--game-session hub-scene.bin hub-bank.bin [second-scene.bin second-bank.bin]]");
            const auto scene=assets::parse_scene(argv[1],argv[3],resource(argv[2],assets::max_scene_v1_bytes));
            const auto bank=assets::parse_pattern_bank(argv[3],resource(argv[4],assets::max_bank_v1_bytes));
            std::optional<std::decay_t<decltype(scene)>> hub_scene,second_scene;std::optional<std::decay_t<decltype(bank)>> hub_bank,second_bank;
            if (game) {
                hub_scene.emplace(assets::parse_scene(argv[1],argv[3],resource(argv[6],assets::max_scene_v1_bytes)));
                hub_bank.emplace(assets::parse_pattern_bank(argv[3],resource(argv[7],assets::max_bank_v1_bytes)));
            }
            if (game && argc==10) {
                second_scene.emplace(assets::parse_scene(argv[1],argv[3],resource(argv[8],assets::max_scene_v1_bytes)));
                second_bank.emplace(assets::parse_pattern_bank(argv[3],resource(argv[9],assets::max_bank_v1_bytes)));
            }
            const auto* terrain=&scene;const auto* patterns=&bank;
            if (!std::getline(std::cin,line)) throw assets::BankError("missing session seed");
            std::array<unsigned,36> f{};
            if (effects) f=fields<36>(line);
            else if (banner) { const auto seed=fields<35>(line);std::copy(seed.begin(),seed.end(),f.begin()); }
            else { const auto seed=fields<32>(line);std::copy(seed.begin(),seed.end(),f.begin()); }
            for (std::size_t i=0;i<f.size();++i)
                if (f[i]>65535 || ((i==7 || i==11 || i==12) && f[i]>255)) throw assets::BankError("session seed field outside range");
            if (f[0]>20 || f[15]>11 || f[28]>1) throw assets::BankError("invalid session selector");
            auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
            auto b=[&](std::size_t i){return static_cast<std::uint8_t>(f[i]);};
            sim::P1SessionState state;
            state.actor={{{w(1),w(2)},w(3),w(4),w(5),{b(7),{w(8),w(9),w(10)},b(11),b(12)},
                static_cast<sim::MotionUpdate>(f[0]),w(6)},w(13),w(14),static_cast<sim::PresentationCallback>(f[15]),static_cast<sim::ActorService>(f[28])};
            state.tracking={w(29),{w(30),w(31)}};state.scratch={w(26),w(27)};
            sim::P1SessionConfig config{{{{w(16),w(17),w(18)},w(19),w(20),w(21)},w(22),w(23),w(24)},w(25),600,{32,65536,4096},{},{1},64};
            if (effects) state.effects.emplace(f[35]);
            // A joined level run spans more frames than the other sessions' cap.
            if (carried || hub) config.max_invocations=4096;
            if (banner) {
                if (f[32]>3) throw assets::BankError("invalid level banner difficulty");
                config.banner=sim::LevelBannerConfig{static_cast<sim::Difficulty>(f[32]),w(33),w(34)};
            }
            std::optional<sim::MixedSessionState> world;
            bool anchored=false,ended=false,level=carried,in_hub=hub,second=false;std::uint32_t record=0;std::size_t level_frames=0,level_limit=0;
            std::optional<sim::HintScreen> hint;std::optional<sim::SecondLevelInputs> after_hub;
            const auto print_seed=[&]() {
                const auto& a=state.actor;const auto& m=a.motion;const auto& q=m.presentation;const auto& c=config.parameters;
                for (auto v:std::array<unsigned,32>{static_cast<unsigned>(m.update),m.position.x,m.position.y,m.horizontal_speed,m.vertical_motion,m.airborne_delay,m.flags,
                        q.mode,q.words[0],q.words[1],q.words[2],q.counter,q.reload,a.presentation_target,a.presentation_cycles,static_cast<unsigned>(a.callback),
                        c.airborne.motion.positive_limit,c.airborne.motion.negative_limit,c.airborne.motion.damping_count_minus_one,c.airborne.acceleration,
                        c.airborne.contact_damping_count_minus_one,c.airborne.gravity,c.ground_acceleration,c.jump_impulse,c.jump_delay,config.acceleration_gate,
                        state.scratch.x,state.scratch.y,static_cast<unsigned>(a.service),state.tracking.selector,state.tracking.position.x,state.tracking.position.y}) std::cout<<v<<' ';
                const auto& t=*state.transition;
                std::cout<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
                for (auto v:t.curves) std::cout<<' '<<static_cast<unsigned>(v);
                std::cout<<' '<<t.requested_position.x<<' '<<t.requested_position.y<<' '<<t.saved_position.x<<' '<<t.saved_position.y<<' '
                         <<state.actions->cooldown<<' '<<state.actions->interval<<' '<<state.actions->mode;
            };
            const auto enter_second=[&]() {
                const auto entry=sim::enter_second_level(*world,*after_hub);
                config.parameters=entry.parameters;config.acceleration_gate=entry.acceleration_gate;config.banner.reset();state=world->p1;
                second=true;terrain=&*second_scene;patterns=&*second_bank;
                print_seed();std::cout<<' '<<world->random.state<<' '<<world->random.mirror<<'\n';
            };
            if (carried || hub) {
                // "direction countdown reload level curve curve curve requested_x requested_y
                // saved_x saved_y cooldown interval mode": FF0B90..FF0BA3 (curve codes 0
                // retained, 1 1356A, 2 135AA, 3 135EA), FF4446/48, FF0732/34 and FF33D8/DA/E0.
                const auto t=transport::pool_row(std::cin);
                if (t.size()!=14 || std::any_of(t.begin(),t.end(),[](auto v){return v>65535;}) || t[4]>3 || t[5]>3 || t[6]>3) throw assets::BankError("invalid transition timer row");
                auto v=[&](std::size_t i){return static_cast<std::uint16_t>(t[i]);};
                sim::TransitionState timer{v(0),v(1),v(2),v(3)};
                for (std::size_t i=0;i<3;++i) timer.curves[i]=static_cast<sim::TransitionCurve>(t[4+i]);
                timer.requested_position={v(7),v(8)};timer.saved_position={v(9),v(10)};
                state.transition=timer;state.actions=sim::ActionGlobals{v(13),v(11),v(12)};
            }
            if (hub) {
                const auto h=transport::pool_row(std::cin);
                if (h.size()!=3+9*7 || h[0]>65535 || h[1]>65535) throw assets::BankError("invalid hub row");
                record=h[2];
                sim::HubWorld hub_world;hub_world.two_player=h[0]!=0;hub_world.table=transport::hub_table(h,3);
                const auto o=transport::pool_row(std::cin);
                if (o.size()!=1+transport::pair_pool_slots || o[0]>transport::pair_pool_slots) throw assets::BankError("invalid hub pool row");
                std::vector<sim::PoolObject> objects(transport::pair_pool_slots,sim::ExternalReservation{});std::vector<std::size_t> free;std::vector<bool> used(objects.size());
                for (std::size_t i=0;i<o[0];++i) {
                    if (o[1+i]>=objects.size() || used[o[1+i]]) throw assets::BankError("invalid hub free stack");
                    used[o[1+i]]=true;objects[o[1+i]]=std::monostate{};free.push_back(o[1+i]);
                }
                const auto c=transport::pool_row(std::cin);
                if (c.size()!=5 || c[0]>65535 || c[1]>65535 || c[2]>1 || c[3]>65535 || c[4]>65535) throw assets::BankError("invalid hub collision row");
                sim::CollisionConfig collision{static_cast<std::uint16_t>(c[0]),static_cast<std::uint16_t>(c[1]),{}};
                if (c[2]) collision.secondary=sim::Position{static_cast<std::uint16_t>(c[3]),static_cast<std::uint16_t>(c[4])};
                else if (c[3] || c[4]) throw assets::BankError("unconsumed secondary coordinates in hub session");
                world.emplace(sim::MixedSessionState{state,sim::MixedPool(std::move(objects),free),{}});
                world->collision=collision;world->hub=std::move(hub_world);
                const auto stage=static_cast<std::uint16_t>(h[1]);
                sim::initialize_hub(*world,stage);
                transport::print_hub_pool(world->pool);
                for (const auto& r:world->hub->table) std::cout<<' '<<r.state;
                std::cout<<'\n';
            } else if (carried) {
                const auto h=transport::pool_row(std::cin);
                if (h.size()!=2) throw assets::BankError("invalid world session header");
                auto rows=transport::world_rows(std::cin,h[0],h[1]);
                const auto c=transport::pool_row(std::cin);
                if (c.size()!=5 || c[0]>65535 || c[1]>65535 || c[2]>1 || c[3]>65535 || c[4]>65535) throw assets::BankError("invalid world session collision row");
                sim::CollisionConfig collision{static_cast<std::uint16_t>(c[0]),static_cast<std::uint16_t>(c[1]),{}};
                if (c[2]) collision.secondary=sim::Position{static_cast<std::uint16_t>(c[3]),static_cast<std::uint16_t>(c[4])};
                else if (c[3] || c[4]) throw assets::BankError("unconsumed secondary coordinates in world session");
                const auto n=transport::pool_row(std::cin);
                if (n.size()!=1 || n[0]>4096) throw assets::BankError("invalid supplied loop count");
                std::vector<transport::SuppliedPhase> supplied;
                for (unsigned i=0;i<n[0];++i) supplied.push_back(transport::supplied_phase(transport::pool_row(std::cin)));
                world=transport::world_setup(std::move(rows),state);world->collision=collision;
                for (const auto& p:supplied) transport::step_supplied_phase(*world,p);
                if (game) {
                    const auto l=transport::pool_row(std::cin);
                    if (l.size()!=1 || l[0]>4096) throw assets::BankError("invalid level frame count");
                    level_limit=l[0];
                }
            } else if (mixed) world=transport::mixed_seed(std::cin,state,&anchored);
            // Only this first row seeds state. Later rows contain logical held
            // buttons U,D,L,R,A,B,C,Start in bits 0..7, never original state.
            while (std::getline(std::cin,line)) {
                if (game && level && level_frames==level_limit) {
                    // The scene change, then the hub's loops on its terrain.
                    std::istringstream row(line);const auto h=transport::pool_row(row);
                    if (h.size()!=5+9*7 || h[0]>1 || h[1]>65535 || h[2]>65535 || h[3]>3) throw assets::BankError("invalid scene change row");
                    record=h[4];
                    sim::HubSceneInputs inputs{transport::hub_table(h,5),h[0]!=0,h[1]!=0,static_cast<std::uint16_t>(h[2]),
                        {static_cast<sim::Difficulty>(h[3]),static_cast<std::uint16_t>(h[2]),0x0d}};
                    const auto entry=sim::enter_hub_scene(*world,inputs);
                    config.parameters=entry.parameters;config.acceleration_gate=entry.acceleration_gate;config.banner.reset();state=world->p1;
                    level=false;in_hub=true;terrain=&*hub_scene;patterns=&*hub_bank;
                    print_seed();std::cout<<' ';
                    print_banner(*entry.banner);
                    transport::print_hub_pool(world->pool);
                    for (const auto& r:world->hub->table) std::cout<<' '<<r.state;
                    std::cout<<'\n';continue;
                }
                if (game && in_hub && ended && second_scene) {
                    // After the hub: the hint screen (unless skipped), then the second level.
                    std::istringstream row(line);const auto h=transport::pool_row(row);
                    if (h.size()!=6 || h[0]>1 || h[1]>1 || h[2]>1 || h[3]>65535 || h[4]>4096 || h[5]>4096) throw assets::BankError("invalid after-hub row");
                    after_hub=sim::SecondLevelInputs{h[1]!=0,h[2]!=0,static_cast<std::uint16_t>(h[3]),static_cast<unsigned>(h[4]),static_cast<unsigned>(h[5])};
                    in_hub=false;
                    if (h[0]) { hint=sim::enter_hint_screen(*world);state=world->p1; }
                    else enter_second();
                    continue;
                }
                if (hint) {
                    const auto mask=fields<1>(line)[0];
                    if (mask>255) throw assets::BankError("invalid logical pad mask");
                    const sim::ThreeButtonPad held{bool(mask&1),bool(mask&2),bool(mask&4),bool(mask&8),bool(mask&16),bool(mask&32),bool(mask&64),bool(mask&128)};
                    const bool done=sim::step_hint_screen(*hint,*world->p1.transition,world->p1.control,held);state=world->p1;
                    const auto& t=*state.transition;
                    std::cout<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level<<' '<<hint->countdown<<' '<<hint->ending<<' '<<done<<'\n';
                    if (done) { hint.reset();enter_second(); }
                    continue;
                }
                sim::WorldUpdates updates;unsigned mask=0;
                if (level) {
                    const auto row=fields<10>(line);mask=row[0];
                    if (row[1]>64) throw assets::BankError("world session E918 count outside limit");
                    updates={row[1],transport::world_message_updates({row.begin(),row.end()},2)};
                } else mask=fields<1>(line)[0];
                if (mask>255) throw assets::BankError("invalid logical pad mask");
                const sim::ThreeButtonPad held{bool(mask&1),bool(mask&2),bool(mask&4),bool(mask&8),bool(mask&16),bool(mask&32),bool(mask&64),bool(mask&128)};
                sim::P1SessionResult result;std::vector<sim::PoolEvent> events;std::vector<sim::SoundRequest> world_sounds;std::vector<sim::MessageRowClear> clears;
                if (ended && !second) throw assets::BankError("hub scene already ended");
                std::optional<sim::HubEntry> entry;
                if (mixed && !second) {
                    auto r=sim::step_mixed_session(*terrain,*patterns,*world,config,held,updates);
                    entry=r.hub_entry;ended=r.scene_ended;
                    result=std::move(r.p1);events=std::move(r.events);world_sounds=std::move(r.world_sounds);clears=std::move(r.clears);state=world->p1;
                }
                else result=sim::step_p1_session(*terrain,*patterns,state,config,held);
                const auto& r=result.actor;
                // P1 as its wrapper returned (a world phase may hand it to 710E afterwards).
                const auto& a=result.wrapper_actor ? *result.wrapper_actor : state.actor;const auto& m=a.motion;const auto& p=m.presentation;
                const auto& tracked=result.wrapper_tracking ? *result.wrapper_tracking : state.tracking;
                std::cout<<state.invocations<<' ';
                for (auto v:std::array<unsigned,16>{static_cast<unsigned>(m.update),m.position.x,m.position.y,m.horizontal_speed,m.vertical_motion,m.airborne_delay,m.flags,
                    p.mode,p.words[0],p.words[1],p.words[2],p.counter,p.reload,a.presentation_target,a.presentation_cycles,static_cast<unsigned>(a.callback)}) std::cout<<v<<' ';
                std::cout<<state.scratch.x<<' '<<state.scratch.y<<' '<<static_cast<unsigned>(a.service)<<' '<<tracked.selector<<' '
                    <<tracked.position.x<<' '<<tracked.position.y<<' ';
                print_control(state.control);
                std::cout<<r.handler_entries<<' '<<r.horizontal_steps<<' '<<r.settle_calls<<' '<<r.landings<<' '<<r.sound_requests.size();
                for (const auto& s:r.sound_requests) std::cout<<' '<<s.id<<' '<<s.priority<<' '<<s.parameter<<' '<<s.selector;
                if (banner && !in_hub && !second) { std::cout<<' ';print_banner(*result.banner); }
                if (effects) {
                    std::cout<<' '<<state.effects->available()<<' '<<r.spawned_effects.size();
                    for (const auto id:r.spawned_effects) std::cout<<' '<<id.slot<<' '<<id.generation;
                    std::cout<<' '<<result.effects.size();
                    for (const auto& update:result.effects) {
                        const auto& e=update.state;const auto& p=e.presentation;
                        std::cout<<' '<<update.id.slot<<' '<<update.id.generation<<' '<<e.owner.value;
                        for (auto v:std::array<unsigned,12>{static_cast<unsigned>(e.side),e.position.x,e.position.y,e.flags,p.mode,
                                p.words[0],p.words[1],p.words[2],p.counter,p.reload,e.target,unsigned(update.released)}) std::cout<<' '<<v;
                    }
                }
                if (level) {
                    // The timer as the frame's 1345A left it (the world's 13294/1324E and
                    // P1's 13208 follow), then the saved position and FF33E0 after the frame.
                    const auto& t=*result.transition;const auto& f=*state.transition;
                    std::cout<<' '<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
                    for (auto c:t.curves) std::cout<<' '<<static_cast<unsigned>(c);
                    std::cout<<' '<<f.saved_position.x<<' '<<f.saved_position.y<<' '<<state.actions->mode<<' ';
                    transport::print_world_phase(*world,events,world_sounds,clears);
                }
                else if (in_hub) {
                    const auto& t=*result.transition;const auto& f=*state.transition;
                    std::cout<<' '<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
                    for (auto c:t.curves) std::cout<<' '<<static_cast<unsigned>(c);
                    std::cout<<' '<<f.requested_position.x<<' '<<f.requested_position.y<<' '
                             <<(world->hub->selected ? transport::hub_record_address(*world->hub->selected) : record);
                    if (entry) std::cout<<" 1 "<<entry->control<<' '<<entry->number;
                    else std::cout<<" 0";
                    std::cout<<' '<<ended;
                    transport::print_hub_pool(world->pool);
                }
                else if (second) {
                    const auto& t=*result.transition;
                    std::cout<<' '<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
                    for (auto c:t.curves) std::cout<<' '<<static_cast<unsigned>(c);
                    std::cout<<' '<<state.actions->cooldown<<' '<<state.actions->mode;
                }
                else if (mixed) transport::print_mixed(*world,events,anchored);
                std::cout<<'\n';
                if (level) ++level_frames;
            }
            if (game && level) throw assets::BankError("game session ended before the scene change");
            if (hint) throw assets::BankError("game session ended inside the hint screen");
            if (second_scene && !second) throw assets::BankError("game session ended before the second level");
        }
        std::cout.flush();if (std::cin.bad() || !std::cout) throw assets::BankError("session I/O failed");
        return 0;
    } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 2;}
}
