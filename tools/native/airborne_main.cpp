#include "sim/airborne.hpp"

#include <fstream>
#include <iostream>
#include <sstream>

namespace {
std::vector<std::uint8_t> read_input(const char* path, std::size_t limit) {
    std::ifstream input(path,std::ios::binary|std::ios::ate);
    const auto extent=input.tellg();
    if (!input || extent<2 || extent>static_cast<std::streamoff>(limit))
        throw wiz::assets::BankError("airborne resource unavailable or outside limits");
    std::vector<std::uint8_t> data(static_cast<std::size_t>(extent));input.seekg(0);
    if (!input.read(reinterpret_cast<char*>(data.data()),static_cast<std::streamsize>(data.size()))
        || input.peek()!=std::char_traits<char>::eof()) throw wiz::assets::BankError("airborne resource changed");
    return data;
}
}
int main(int argc,char** argv) {
    using namespace wiz;
    if (argc!=5) {std::cerr<<"usage: wiznliz-airborne scene-id scene.bin bank-id bank.bin\n";return 2;}
    try {
        const auto scene=assets::parse_scene(argv[1],argv[3],read_input(argv[2],assets::max_scene_v1_bytes));
        const auto bank=assets::parse_pattern_bank(argv[3],read_input(argv[4],assets::max_bank_v1_bytes));
        std::string line;std::size_t cases=0;
        while (std::getline(std::cin,line)) {
            std::istringstream input(line);std::array<unsigned,21> f{};
            for (auto& field:f) if (!(input>>field)) throw assets::BankError("incomplete airborne case");
            std::string extra;
            if (line.size()>256 || input>>extra || ++cases>1000000 || f[0]>6 || (f[7]!=1 && f[7]!=2)
                || !f[20] || f[20]>16 || (f[0] && f[20]!=1)) throw assets::BankError("invalid airborne case");
            for (std::size_t i=1;i<20;++i)
                if (f[i]>65535 || (i>=14 && i<=16 && f[i]>255)) throw assets::BankError("airborne field outside range");
            auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
            sim::MotionState state{{w(1),w(2)},w(3),w(4),w(5),{0xa5,{0xa5a5,0xa5a5,0xa5a5},0xa5,0xa5},
                static_cast<sim::MotionUpdate>(f[7]),w(6)};
            sim::AirborneParameters parameters{{w(8),w(9),w(10)},w(11),w(12),w(13)};
            sim::AirborneInput controls{static_cast<std::uint8_t>(f[14]),static_cast<std::uint8_t>(f[15]),static_cast<std::uint8_t>(f[16]),w(17)};
            sim::TerrainScratch scratch{w(18),w(19)};sim::AirborneResult result;unsigned completed=0;
            for (unsigned repeat=0;repeat<f[20];++repeat) {
                sim::AirborneResult step;
                switch (f[0]) {
                case 0: step=sim::step_airborne(scene,bank,state,parameters,controls,scratch,{65536,4096});break;
                case 1: step=sim::step_airborne_horizontal(scene,bank,state,parameters,scratch,65536);break;
                case 2: step=sim::step_airborne_left(scene,bank,state,parameters,scratch);break;
                case 3: step=sim::step_airborne_right(scene,bank,state,parameters,scratch);break;
                case 4: step=sim::resolve_landing(state,parameters.motion);break;
                case 5: sim::set_right_motion_reload(state);break;
                case 6: sim::set_left_motion_reload(state);break;
                }
                ++completed;result.horizontal_steps+=step.horizontal_steps;result.settle_calls+=step.settle_calls;
                result.landings+=step.landings;result.immediate_continuation=step.immediate_continuation;
                result.horizontal_contact=f[0]==1 && step.horizontal_contact;
                if (result.immediate_continuation || (!f[0] && state.update!=sim::MotionUpdate::airborne
                    && state.update!=sim::MotionUpdate::airborne_fall)) break;
            }
            const auto& p=state.presentation;
            std::cout<<state.position.x<<' '<<state.position.y<<' '<<state.horizontal_speed<<' '<<state.vertical_motion<<' '
                <<state.airborne_delay<<' '<<static_cast<unsigned>(state.update)<<' '<<unsigned(p.mode)<<' '
                <<p.words[0]<<' '<<p.words[1]<<' '<<p.words[2]<<' '<<unsigned(p.counter)<<' '<<unsigned(p.reload)<<' '
                <<scratch.x<<' '<<scratch.y<<' '<<state.flags<<' '<<result.horizontal_steps<<' '<<result.settle_calls<<' '
                <<result.landings<<' '<<completed<<' '<<result.immediate_continuation<<' '<<result.horizontal_contact<<'\n';
        }
        std::cout.flush();if (std::cin.bad() || !std::cout) throw assets::BankError("airborne I/O failed");
        return 0;
    } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 2;}
}
