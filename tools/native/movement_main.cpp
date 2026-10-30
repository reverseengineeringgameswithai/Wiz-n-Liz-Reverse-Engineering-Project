#include "sim/movement.hpp"

#include <fstream>
#include <iostream>
#include <sstream>

namespace {
std::vector<std::uint8_t> read_input(const char* path, std::size_t limit) {
    std::ifstream input(path,std::ios::binary|std::ios::ate);
    const auto extent=input.tellg();
    if (!input || extent<2 || extent>static_cast<std::streamoff>(limit))
        throw wiz::assets::BankError("movement resource unavailable or outside limits");
    std::vector<std::uint8_t> data(static_cast<std::size_t>(extent));input.seekg(0);
    if (!input.read(reinterpret_cast<char*>(data.data()),static_cast<std::streamsize>(data.size()))
        || input.peek()!=std::char_traits<char>::eof()) throw wiz::assets::BankError("movement resource changed");
    return data;
}
}
int main(int argc,char** argv) {
    using namespace wiz;
    if (argc!=5) { std::cerr<<"usage: wiznliz-movement scene-id scene.bin bank-id bank.bin\n";return 2; }
    try {
        const auto scene=assets::parse_scene(argv[1],argv[3],read_input(argv[2],assets::max_scene_v1_bytes));
        const auto bank=assets::parse_pattern_bank(argv[3],read_input(argv[4],assets::max_bank_v1_bytes));
        std::string line;std::size_t cases=0;
        while (std::getline(std::cin,line)) {
            std::istringstream input(line);std::array<unsigned,10> fields{};
            for (auto& field:fields) if (!(input>>field)) throw assets::BankError("incomplete movement case");
            std::string extra;
            if (line.size()>160 || input>>extra || ++cases>1000000 || fields[0]>7 || !fields[9] || fields[9]>16)
                throw assets::BankError("invalid movement case");
            for (std::size_t i=1;i<9;++i) if (fields[i]>65535) throw assets::BankError("movement word outside range");
            auto w=[&](std::size_t i){return static_cast<std::uint16_t>(fields[i]);};
            sim::MotionState state{{w(1),w(2)},w(3),0x1357,0x2468,{0xa5,{0xa5a5,0xa5a5,0xa5a5},0xa5,0xa5}};
            sim::MotionParameters parameters{w(4),w(5),w(6)};
            sim::TerrainScratch scratch{w(7),w(8)};sim::MotionResult result;
            for (unsigned i=0;i<fields[9];++i) {
                sim::MotionResult step;
                switch (fields[0]) {
                case 0: step=sim::step_horizontal(scene,bank,state,parameters,scratch,65536);break;
                case 1: step=sim::step_left(scene,bank,state,parameters,scratch);break;
                case 2: step=sim::step_right(scene,bank,state,parameters,scratch);break;
                case 3: sim::damp_horizontal(state,parameters);break;
                case 4: sim::damp_once(state);break;
                case 5: sim::clamp_positive(state,parameters);break;
                case 6: sim::clamp_negative(state,parameters);break;
                case 7: sim::enter_airborne(state);step.airborne_transitions=1;break;
                }
                result.horizontal_steps+=step.horizontal_steps;result.airborne_transitions+=step.airborne_transitions;
            }
            const auto& p=state.presentation;
            std::cout<<state.position.x<<' '<<state.position.y<<' '<<state.horizontal_speed<<' '<<state.vertical_motion<<' '
                <<state.airborne_delay<<' '<<(state.update==sim::MotionUpdate::airborne)<<' '<<unsigned(p.mode)<<' '
                <<p.words[0]<<' '<<p.words[1]<<' '<<p.words[2]<<' '<<unsigned(p.counter)<<' '<<unsigned(p.reload)<<' '
                <<scratch.x<<' '<<scratch.y<<' '<<result.horizontal_steps<<' '<<result.airborne_transitions<<'\n';
        }
        std::cout.flush();if (std::cin.bad() || !std::cout) throw assets::BankError("movement I/O failed");
        return 0;
    } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 2;}
}
