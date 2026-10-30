#include "sim/presentation.hpp"

#include <fstream>
#include <iostream>
#include <sstream>
#include <optional>
#include <string_view>

namespace {
std::array<unsigned,16> actor_fields(const wiz::sim::ActorState& state) {
    const auto& m=state.motion;const auto& p=m.presentation;
    return {static_cast<unsigned>(m.update),m.position.x,m.position.y,m.horizontal_speed,
        m.vertical_motion,m.airborne_delay,m.flags,p.mode,p.words[0],p.words[1],p.words[2],
        p.counter,p.reload,state.presentation_target,state.presentation_cycles,static_cast<unsigned>(state.callback)};
}
std::array<unsigned,12> effect_fields(const wiz::sim::ReversalEffect& e) {
    const auto& p=e.presentation;
    return {static_cast<unsigned>(e.owner.value),static_cast<unsigned>(e.side),e.position.x,e.position.y,
        e.flags,p.mode,p.words[0],p.words[1],p.words[2],p.counter,p.reload,e.target};
}
void effect_cases(bool sequence) {
    using namespace wiz;
    std::string line;std::optional<sim::ReversalEffect> retained;std::size_t cases=0;
    while (std::getline(std::cin,line)) {
        std::istringstream input(line);std::array<unsigned,16> f{};std::string extra;
        for (auto& field:f) if (!(input>>field)) throw assets::BankError("incomplete effect case");
        if (line.size()>512 || input>>extra || ++cases>1000000 || f[1]>1 || !f[15] || f[15]>256)
            throw assets::BankError("invalid effect case");
        for (std::size_t i=0;i<15;++i)
            if (f[i]>65535 || ((i==5 || i==9 || i==10) && f[i]>255)) throw assets::BankError("effect field outside range");
        auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
        sim::ReversalEffect e{{f[0]},{w(2),w(3)},
            {static_cast<std::uint8_t>(f[5]),{w(6),w(7),w(8)},static_cast<std::uint8_t>(f[9]),static_cast<std::uint8_t>(f[10])},
            w(11),w(4),static_cast<sim::ReversalSide>(f[1])};
        if (sequence && retained) {
            if (effect_fields(e)!=effect_fields(*retained)) throw assets::BankError("effect sequence continuity mismatch");
            e=*retained;
        }
        unsigned released=0;
        for (unsigned i=0;i<f[15];++i) released+=sim::step_reversal_effect(e,{f[12]},{w(13),w(14)}) ? 1U : 0U;
        if (sequence) retained=e;
        for (auto field:effect_fields(e)) std::cout<<field<<' ';
        std::cout<<released<<' '<<f[15]<<'\n';
    }
}
std::vector<std::uint8_t> read_input(const char* path, std::size_t limit) {
    std::ifstream input(path,std::ios::binary|std::ios::ate);
    const auto extent=input.tellg();
    if (!input || extent<2 || extent>static_cast<std::streamoff>(limit))
        throw wiz::assets::BankError("actor resource unavailable or outside limits");
    std::vector<std::uint8_t> data(static_cast<std::size_t>(extent));input.seekg(0);
    if (!input.read(reinterpret_cast<char*>(data.data()),static_cast<std::streamsize>(data.size()))
        || input.peek()!=std::char_traits<char>::eof()) throw wiz::assets::BankError("actor resource changed");
    return data;
}
}
int main(int argc,char** argv) {
    using namespace wiz;
    const std::string_view mode=argc==6 ? argv[5] : "";
    const bool reversal=mode=="--reversal" || mode=="--reversal-scheduled" || mode=="--reversal-sequence" || mode=="--reversal-empty";
    const bool score=mode=="--score" || mode=="--score-sequence";
    const bool exit_tally=score || mode=="--exit-tally" || mode=="--exit-tally-sequence";
    const bool bonus=mode=="--bonus" || mode=="--bonus-sequence";
    const bool palette=mode=="--palette" || mode=="--palette-sequence";
    const bool tally=exit_tally || bonus || palette || mode=="--tally" || mode=="--tally-sequence";
    const bool coast_entry=mode=="--coast-entry";
    const bool coast_sequence=mode=="--coast-sequence";
    const bool transition=tally || coast_entry || coast_sequence || mode=="--transition" || mode=="--transition-sequence" || mode=="--transition-timer";
    const bool dispatch=transition || mode=="--dispatch" || mode=="--dispatch-sequence";
    const bool actions=dispatch || mode=="--actions" || mode=="--actions-scheduled" || mode=="--actions-presentation" || mode=="--actions-sequence";
    const bool sequence=mode=="--score-sequence" || mode=="--exit-tally-sequence" || mode=="--bonus-sequence" ||mode=="--palette-sequence" || mode=="--tally-sequence" || coast_sequence || mode=="--transition-sequence" || mode=="--sequence" || mode=="--reversal-sequence" || mode=="--actions-sequence" || mode=="--dispatch-sequence";
    const bool effect=mode=="--effect" || mode=="--effect-sequence";
    if ((argc!=5 && argc!=6) || (mode!="" && mode!="--presentation" && mode!="--scheduled" && !sequence && !reversal && !effect && !actions)) {
        std::cerr<<"usage: wiznliz-actor scene-id scene.bin bank-id bank.bin [--presentation|--scheduled|--sequence|--reversal|--reversal-scheduled|--reversal-sequence|--effect|--effect-sequence|--actions|--actions-scheduled|--actions-presentation|--actions-sequence|--dispatch|--dispatch-sequence|--transition|--transition-sequence|--transition-timer|--coast-entry|--coast-sequence|--tally|--tally-sequence|--palette|--palette-sequence|--bonus|--bonus-sequence|--exit-tally|--exit-tally-sequence|--score|--score-sequence]\n";return 2;
    }
    try {
        const auto scene=assets::parse_scene(argv[1],argv[3],read_input(argv[2],assets::max_scene_v1_bytes));
        const auto bank=assets::parse_pattern_bank(argv[3],read_input(argv[4],assets::max_bank_v1_bytes));
        if (effect) {
            effect_cases(mode=="--effect-sequence");std::cout.flush();
            if (std::cin.bad() || !std::cout) throw assets::BankError("effect I/O failed");
            return 0;
        }
        std::string line;std::size_t cases=0;std::optional<sim::ActorState> retained;std::optional<sim::Position> retained_tracking;
        const std::size_t capacity=mode=="--reversal-empty" ? 0 : 16;
        sim::ReversalEffects objects(capacity);
        std::optional<sim::TallyState> retained_tally;
        std::optional<sim::PalettePreparation> retained_palette;
        while (std::getline(std::cin,line)) {
            std::istringstream input(line);std::array<unsigned,131> f{};
            for (std::size_t i=0;i<(score ? 77U : exit_tally ? 72U : bonus ? 91U : palette ? 131U : tally ? 67U : transition ? 60U : dispatch ? 47U : actions ? 43U : 35U);++i) if (!(input>>f[i])) throw assets::BankError("incomplete actor case");
            std::string extra;
            if (line.size()>((palette || bonus) ? 1024U : 512U) || input>>extra || ++cases>1000000 || !f[0] || f[0]>(exit_tally ? 28U : palette ? 26U : tally ? 25U : transition ? 23U : 20U)
                || f[15]>11 || !f[34] || f[34]>16) throw assets::BankError("invalid actor case");
            for (std::size_t i=1;i<34;++i)
                if (f[i]>65535 || ((i==7 || i==11 || i==12 || (i>=25 && i<=30)) && f[i]>255))
                    throw assets::BankError("actor field outside range");
            for (std::size_t i=35;i<67;++i)
                if (f[i]>65535 || ((i==38 || i==66) && f[i]>255)) throw assets::BankError("action field outside range");
            auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
            auto b=[&](std::size_t i){return static_cast<std::uint8_t>(f[i]);};
            sim::ActorState state{{{w(1),w(2)},w(3),w(4),w(5),{b(7),{w(8),w(9),w(10)},b(11),b(12)},
                static_cast<sim::MotionUpdate>(f[0]),w(6)},w(13),w(14),static_cast<sim::PresentationCallback>(f[15])};
            if (dispatch && f[43]>1) throw assets::BankError("invalid actor service selector");
            state.service=static_cast<sim::ActorService>(f[43]);
            sim::ActorTracking tracking{w(44),{w(45),w(46)}};
            if (dispatch && sequence && retained_tracking) {
                if (tracking.position.x!=retained_tracking->x || tracking.position.y!=retained_tracking->y)
                    throw assets::BankError("tracking sequence continuity mismatch");
                tracking.position=*retained_tracking;
            }
            if (sequence && retained) {
                // Subsequent actor columns are assertions, never replacement
                // state. Inputs/parameters/global terrain scratch are supplied
                // by the surrounding environment at each invocation boundary.
                if (actor_fields(state)!=actor_fields(*retained) || state.service!=retained->service) throw assets::BankError("actor sequence continuity mismatch");
                state=*retained;
            }
            sim::ActorParameters parameters{{{w(16),w(17),w(18)},w(19),w(20),w(21)},w(22),w(23),w(24)};
            sim::ActorInput controls{b(25),b(26),b(27),b(28),b(29),b(30),w(31),actions ? b(38) : std::uint8_t{0xff}};
            controls.start=b(66);
            sim::TallyState totals{w(60),w(61),w(62),w(63),w(64),w(65)};
            if (bonus) {
                for (std::size_t i=67;i<91;++i) if (f[i]>65535) throw assets::BankError("bonus field outside range");
                totals.bonus=sim::BonusSlots{{},{},w(67),w(68)};
                for (std::size_t i=0;i<11;++i) {
                    totals.bonus->assigned.push_back(w(69+i));totals.bonus->choices.push_back(w(80+i));
                }
            }
            if (exit_tally) {
                for (std::size_t i=67;i<72;++i) if (f[i]>65535) throw assets::BankError("exit tally field outside range");
                totals.exit_state=sim::ExitTallyState{w(67),w(68),w(69),w(70),w(71)};
            }
            if (score) {
                if (f[75]>65535) throw assets::BankError("score reward outside range");
                totals.score=sim::ScoreState{f[72],f[73],f[74],f[76],w(75)};
            }
            if (sequence && retained_tally) {
                const auto& previous=*retained_tally;
                if (totals.remaining!=previous.remaining || totals.skip!=previous.skip || totals.countdown!=previous.countdown || totals.credit!=previous.credit)
                    throw assets::BankError("tally sequence continuity mismatch");
                // Palette routing is a world feed; bonus mode owns the special gate.
                const auto palette_gate=totals.palette_gate, special_gate=totals.special_gate;
                if (bonus) {
                    if (special_gate!=previous.special_gate || totals.bonus->assigned!=previous.bonus->assigned || totals.bonus->cursor!=previous.bonus->cursor)
                        throw assets::BankError("bonus sequence continuity mismatch");
                    totals.bonus->assigned=previous.bonus->assigned;totals.bonus->cursor=previous.bonus->cursor;
                    // Choices/count are explicit world feeds; special gate is retained.
                    totals.remaining=previous.remaining;totals.skip=previous.skip;totals.countdown=previous.countdown;totals.credit=previous.credit;
                } else {
                    const auto exit_state=totals.exit_state;
                    const auto score_state=totals.score;
                    if (score && (exit_state->secondary_remaining!=previous.exit_state->secondary_remaining || score_state!=previous.score))
                        throw assets::BankError("score sequence continuity mismatch");
                    if (exit_tally && exit_state->marker!=previous.exit_state->marker)
                        throw assets::BankError("exit tally sequence continuity mismatch");
                    totals=previous;totals.palette_gate=palette_gate;totals.special_gate=special_gate;
                    if (exit_tally) { totals.exit_state=exit_state;totals.exit_state->marker=previous.exit_state->marker; }
                    if (score) totals.exit_state->secondary_remaining=previous.exit_state->secondary_remaining;
                }
            }
            sim::PalettePreparation prepared;
            if (palette) {
                for (std::size_t i=67;i<131;++i)
                    if (f[i]>(i<83 ? 65535U : 255U)) throw assets::BankError("palette field outside range");
                for (std::size_t i=0;i<16;++i) {
                    prepared.colors[i]=w(67+i);
                    for (std::size_t j=0;j<3;++j) prepared.components[i][j]=b(83+3*i+j);
                }
                if (sequence && retained_palette) {
                    if (prepared.components!=retained_palette->components)
                        throw assets::BankError("palette sequence continuity mismatch");
                    prepared.components=retained_palette->components; // Source colors are explicit world inputs.
                }
            }
            sim::ActionGlobals globals{w(35),w(36),w(37)};
            for (std::size_t i=51;i<54;++i) if (f[i]>3) throw assets::BankError("invalid transition curve");
            sim::TransitionState fade{w(47),w(48),w(49),w(50),
                {static_cast<sim::TransitionCurve>(f[51]),static_cast<sim::TransitionCurve>(f[52]),static_cast<sim::TransitionCurve>(f[53])},
                w(54),w(55),{w(56),w(57)},{w(58),w(59)}};
            std::array<unsigned,4> mailbox{f[39],f[40],f[41],f[42]};
            sim::TerrainScratch scratch{w(32),w(33)};sim::ActorResult result;
            if (!sequence) objects=sim::ReversalEffects(capacity);
            const sim::ReversalContext context{reversal ? &objects : nullptr,{1}};
            for (unsigned repeat=0;repeat<f[34];++repeat) {
                sim::ActorResult step;
                if (coast_entry || (coast_sequence && !retained)) sim::begin_coasting(state,tracking);
                else if (mode=="--transition-timer") sim::step_transition_timer(fade);
                else if (dispatch) step=sim::step_actor_dispatch(scene,bank,state,tracking,parameters,controls,scratch,{32,65536,4096},context,&globals,transition ? &fade : nullptr,tally ? &totals : nullptr,palette ? &prepared : nullptr);
                else if (mode=="--presentation") sim::step_presentation(state);
                else if (mode=="--actions-presentation") step=sim::step_actor_presentation(scene,bank,state,parameters,controls,scratch,{32,65536,4096},context,&globals);
                else if (mode.empty() || mode=="--reversal" || mode=="--reversal-empty" || mode=="--actions") step=sim::step_actor(scene,bank,state,parameters,controls,scratch,{32,65536,4096},context,actions ? &globals : nullptr);
                else step=sim::step_scheduled_actor(scene,bank,state,parameters,controls,scratch,{32,65536,4096},context,actions ? &globals : nullptr);
                for (const auto& request:step.sample_requests) {
                    if (request.sample==sim::ActionSample::up_action) mailbox={request.count,request.parameter,0x8000,30};
                    else if (request.sample==sim::ActionSample::score_reward) mailbox={request.count,request.parameter,0xa5ea,30};
                    else throw assets::BankError("unknown sample adapter resource"); // Research-only original resource adapter.
                }
                result.sample_requests.insert(result.sample_requests.end(),step.sample_requests.begin(),step.sample_requests.end());
                result.horizontal_steps+=step.horizontal_steps;result.settle_calls+=step.settle_calls;result.landings+=step.landings;
                result.sound_requests.insert(result.sound_requests.end(),step.sound_requests.begin(),step.sound_requests.end());
                result.bonus_assignments.insert(result.bonus_assignments.end(),step.bonus_assignments.begin(),step.bonus_assignments.end());
                result.bonus_probes+=step.bonus_probes;result.score_advances+=step.score_advances;
                result.spawned_effects.insert(result.spawned_effects.end(),step.spawned_effects.begin(),step.spawned_effects.end());
            }
            if (sequence && tally) retained_tally=totals;
            if (sequence && palette) retained_palette=prepared;
            if (sequence) { retained=state; if (dispatch) retained_tracking=tracking.position; }
            for (auto field:actor_fields(state)) std::cout<<field<<' ';
            std::cout<<scratch.x<<' '<<scratch.y<<' '<<result.horizontal_steps<<' '<<result.settle_calls<<' '<<result.landings<<' '
                <<result.sound_requests.size()<<' '<<f[34];
            for (const auto& r:result.sound_requests) std::cout<<' '<<r.id<<' '<<r.priority<<' '<<r.parameter<<' '<<r.selector;
            if (reversal) {
                std::cout<<' '<<result.spawned_effects.size();
                for (auto id:result.spawned_effects) for (auto field:effect_fields(objects.at(id))) std::cout<<' '<<field;
            }
            if (actions) {
                std::cout<<' '<<globals.mode<<' '<<globals.cooldown<<' '<<globals.interval;
                for (auto field:mailbox) std::cout<<' '<<field;
                std::cout<<' '<<result.sample_requests.size();
                for (const auto& request:result.sample_requests)
                    std::cout<<' '<<static_cast<unsigned>(request.sample)<<' '<<request.count<<' '<<request.parameter;
            }
            if (dispatch) std::cout<<' '<<static_cast<unsigned>(state.service)<<' '<<tracking.selector<<' '<<tracking.position.x<<' '<<tracking.position.y;
            if (transition) {
                std::cout<<' '<<fade.direction<<' '<<fade.countdown<<' '<<fade.reload<<' '<<fade.level;
                for (auto curve:fade.curves) std::cout<<' '<<static_cast<unsigned>(curve);
                std::cout<<' '<<fade.dirty<<' '<<fade.palette_scope<<' '<<fade.requested_position.x<<' '<<fade.requested_position.y
                         <<' '<<fade.saved_position.x<<' '<<fade.saved_position.y;
            }
            if (tally) std::cout<<' '<<totals.palette_gate<<' '<<totals.remaining<<' '<<totals.skip<<' '<<totals.countdown<<' '<<totals.credit<<' '<<totals.special_gate;
            if (palette) {
                for (auto color:prepared.colors) std::cout<<' '<<color;
                for (const auto& color:prepared.components) for (auto component:color) std::cout<<' '<<unsigned(component);
            }
            if (exit_tally) {
                const auto& e=*totals.exit_state;
                std::cout<<' '<<e.secondary_gate<<' '<<e.secondary_remaining<<' '<<e.marker<<' '<<e.selection<<' '<<e.target_selection;
            }
            if (score) {
                const auto& q=*totals.score;
                std::cout<<' '<<q.value<<' '<<q.threshold<<' '<<q.increment<<' '<<q.rewards<<' '<<q.scratch<<' '<<result.score_advances;
            }
            if (bonus) {
                std::cout<<' '<<totals.bonus->count<<' '<<totals.bonus->cursor;
                for (auto field:totals.bonus->assigned) std::cout<<' '<<field;
                for (auto field:totals.bonus->choices) std::cout<<' '<<field;
                std::cout<<' '<<result.bonus_probes<<' '<<result.bonus_assignments.size();
                for (const auto& assignment:result.bonus_assignments) std::cout<<' '<<assignment.slot<<' '<<assignment.value;
            }
            std::cout<<'\n';
        }
        std::cout.flush();if (std::cin.bad() || !std::cout) throw assets::BankError("actor I/O failed");
        return 0;
    } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 2;}
}
