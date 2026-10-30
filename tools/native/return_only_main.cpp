#include "pair_transport.hpp"
#include <string_view>
int main(int argc,char** argv) {
    using namespace wiz;
    try {
        const std::string_view mode=argc==2 ? argv[1] : "";
        const bool pair=mode=="--pair",prefix=mode=="--prefix",tail=mode=="--tail",message=mode=="--message",pairs=mode=="--pairs";
        const bool pool=mode=="--pair-pool" || mode=="--dormant-pool" || mode=="--prefix-pool" || mode=="--tail-pool" || mode=="--pairs-pool";
        if(argc!=1 && !pair && !prefix && !tail && !message && !pairs && !pool)throw assets::BankError("usage: wiznliz-return-only [--pair|--pair-pool|--dormant-pool|--prefix|--prefix-pool|--tail|--tail-pool|--message|--pairs|--pairs-pool]");
        if(mode=="--tail-pool") transport::tail_pool(std::cin);
        if(mode=="--pair-pool") transport::pair_pool(std::cin,[](sim::MixedSessionState& w,const auto&){return sim::initialize_return_only_pair(w);},transport::Anchors::return_only,transport::PhaseInputs::none);
        // 6EC8/6EDC: the fourth header field selects FF31B4 (0) or FF31B8 (1).
        if(mode=="--dormant-pool") transport::pair_pool(std::cin,[](sim::MixedSessionState& w,const auto& h){
            if(h[3]>1)throw assets::BankError("unknown dormant identity");
            return sim::initialize_dormant(w,static_cast<sim::DormantAnchor>(h[3]));},transport::Anchors::all,transport::PhaseInputs::none,1);
        // [6886,68A4): the fourth header field is the logical identity of FF0690.
        if(mode=="--prefix-pool") transport::pair_pool(std::cin,[](sim::MixedSessionState& w,const auto& h){
            return sim::initialize_level_setup_prefix(w,{h[3]});},transport::Anchors::all,transport::PhaseInputs::none,1);
        // [68C4,68D4): header extras are the caller's A5 identity, the logical
        // FF0690 identity, the four gate words and the P2 control's +3C/+3E.
        if(mode=="--pairs-pool") transport::pair_pool(std::cin,[](sim::MixedSessionState& w,const auto& h){
            sim::GatedPairInputs inputs{{},sim::Position{},{h[3]},{h[4]}};
            for(std::size_t i=5;i<11;++i) if(h[i]>65535) throw assets::BankError("setup pairs word outside range");
            for(std::size_t i=0;i<4;++i) inputs.gates[i]=static_cast<std::uint16_t>(h[5+i]);
            inputs.p2_origin=sim::Position{static_cast<std::uint16_t>(h[9]),static_cast<std::uint16_t>(h[10])};
            return sim::initialize_gated_pairs(w,inputs);},transport::Anchors::none,transport::PhaseInputs::none,8);
        std::size_t count=0;
        while(!pool && std::cin.peek()!=std::char_traits<char>::eof()) {
            if(++count>1000000)throw assets::BankError("return-only case budget exhausted");
            const auto f=transport::pool_row(std::cin);
            if(prefix){transport::authored_prefix(f);std::cout<<'\n';continue;}
            if(tail){transport::authored_tail(f);std::cout<<'\n';continue;}
            if(message){transport::authored_message(f);std::cout<<'\n';continue;}
            if(pairs){transport::authored_pairs(f);std::cout<<'\n';continue;}
            if(pair){
                transport::authored_pair<sim::ReturnOnlyObject>(f,[](sim::MixedPool& p){return p.initialize_return_only_pair();},
                    "return-only pair allocation exhausted","return-only pair inherits unknown slot state",true);
                std::cout<<'\n';continue;
            }
            if(f.size()!=13 || !f[12] || f[12]>256)throw assets::BankError("invalid return-only case/repetitions");
            auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("return-only word outside range");return static_cast<std::uint16_t>(f[i]);};
            auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("return-only byte outside range");return static_cast<std::uint8_t>(f[i]);};
            sim::ReturnOnlyObject object{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),w(10),{f[11]}};
            for(unsigned i=0;i<f[12];++i)sim::step_return_only_object(object);
            transport::print_object(object);std::cout<<'\n';
        }
        std::cout.flush();if(std::cin.bad() || !std::cout)throw assets::BankError("return-only I/O failure");
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
