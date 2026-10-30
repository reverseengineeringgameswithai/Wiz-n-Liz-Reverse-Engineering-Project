#include "sim/trail.hpp"
#include <iostream>
#include <sstream>
#include <string_view>
#include <vector>
namespace {
using namespace wiz;
std::vector<std::uint32_t> row(const std::string& line,std::size_t n) {
    if(line.size()>1024) throw assets::BankError("trail row exceeds limit");
    std::istringstream input(line);std::uint64_t value;std::vector<std::uint32_t> f;
    while(input>>value) {if(value>0xffffffffU) throw assets::BankError("trail field outside range");f.push_back(static_cast<std::uint32_t>(value));}
    if(!input.eof() || f.size()!=n) throw assets::BankError("invalid trail row");
    return f;
}
void print_particle(const sim::TrailParticle& p) {
    const auto& a=p.presentation;
    for(auto v:std::array<unsigned,10>{p.position.x,p.position.y,p.flags,a.mode,a.words[0],a.words[1],a.words[2],a.counter,a.reload,p.target}) std::cout<<' '<<v;
}
}
int main(int argc,char** argv) {
    using namespace wiz;
    try {
        if(argc!=2) throw assets::BankError("usage: wiznliz-trail --emitter|--scheduled|--sequence|--particle|--particle-sequence|--rng|--spawn");
        const std::string_view mode=argv[1];const bool particle_sequence=mode=="--particle-sequence";const bool particle=mode=="--particle" || particle_sequence,rng_mode=mode=="--rng",spawn=mode=="--spawn";
        const bool scheduled=mode=="--scheduled" || mode=="--sequence",sequence=mode=="--sequence";
        if(!particle && !rng_mode && !spawn && !scheduled && mode!="--emitter") throw assets::BankError("unknown trail mode");
        std::string line;std::size_t count=0;sim::TrailEmitter retained;sim::TrailRandom retained_random;sim::TrailParticle retained_particle;
        while(std::getline(std::cin,line)) {
            if(++count>1000000) throw assets::BankError("trail case budget exhausted");
            const auto f=row(line,particle ? 11 : rng_mode || spawn ? 3 : 29);
            auto w=[&](std::size_t i){if(f[i]>65535) throw assets::BankError("trail word outside range");return static_cast<std::uint16_t>(f[i]);};
            auto b=[&](std::size_t i){if(f[i]>255) throw assets::BankError("trail byte outside range");return static_cast<std::uint8_t>(f[i]);};
            const auto repeats=spawn ? 1U : f.back();
            if(!repeats || repeats>32) throw assets::BankError("trail repetition budget exhausted");
            if(spawn) {if(f[2]>1) throw assets::BankError("invalid spawn capacity");print_particle(sim::make_trail_particle({w(0),w(1)},f[2]!=0));}
            else if(rng_mode) {
                sim::TrailRandom rng{f[0],f[1]};std::uint32_t value=0;
                for(unsigned i=0;i<repeats;++i)value=sim::next_trail_random(rng);
                std::cout<<rng.state<<' '<<rng.mirror<<' '<<value;
            } else if(particle) {
                sim::TrailParticle p{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9)};if(particle_sequence && count>1)p=retained_particle;unsigned releases=0;
                for(unsigned i=0;i<repeats;++i) releases+=sim::step_trail_particle(p);
                retained_particle=p;print_particle(p);std::cout<<' '<<releases;
            } else {
                sim::TrailEmitter e;e.position={w(0),w(1)};e.countdown=w(2);
                for(std::size_t i=0;i<5;++i)e.history[i]={w(3+2*i),w(4+2*i)};
                e.presentation={b(13),{w(14),w(15),w(16)},b(17),b(18)};e.target=w(19);e.flags=w(20);e.owner={f[21]};
                if(sequence && count>1)e=retained;
                sim::TrailRandom rng{f[26],f[27]};if(sequence && count>1)rng=retained_random;unsigned available=f[25];
                if(available>16)throw assets::BankError("trail allocation budget outside range");
                const sim::Position owner_position{w(23),w(24)};std::vector<sim::TrailParticle> particles;
                for(unsigned i=0;i<repeats;++i) {
                    auto p=sim::step_trail_emitter(e,rng,{f[22]},owner_position,available!=0,scheduled);
                    if(p){particles.push_back(*p);--available;}
                }
                retained=e;retained_random=rng;const auto& a=e.presentation;
                std::cout<<e.position.x<<' '<<e.position.y<<' '<<e.countdown;
                for(auto h:e.history)std::cout<<' '<<h.x<<' '<<h.y;
                for(auto v:std::array<unsigned,8>{a.mode,a.words[0],a.words[1],a.words[2],a.counter,a.reload,e.target,e.flags})std::cout<<' '<<v;
                std::cout<<' '<<e.owner.value<<' '<<rng.state<<' '<<rng.mirror<<' '<<available<<' '<<particles.size();
                for(const auto& p:particles)print_particle(p);
            }
            std::cout<<'\n';
        }
        std::cout.flush();if(std::cin.bad() || !std::cout)throw assets::BankError("trail I/O failure");
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
