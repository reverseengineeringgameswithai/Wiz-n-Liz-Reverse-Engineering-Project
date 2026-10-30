#include "pair_transport.hpp"
#include <string_view>

int main(int argc,char** argv) {
    using namespace wiz;
    try {
        const std::string_view mode=argc==2 ? argv[1] : "";
        const bool pool=mode=="--pair-pool" || mode=="--rising-pair-pool";
        if(mode!="--handler" && mode!="--scheduled" && mode!="--pair" && mode!="--rising-pair" && !pool)
            throw assets::BankError("usage: wiznliz-private --handler|--scheduled|--pair|--pair-pool|--rising-pair|--rising-pair-pool");
        const bool scheduled=mode=="--scheduled";
        // 7C26 gated-visibility pair: authored cases, or a seeded pool followed
        // by phases that each name the three shared gate inputs explicitly.
        if(mode=="--pair-pool")
            transport::pair_pool(std::cin,[](sim::MixedSessionState& w,const auto&){return w.pool.initialize_visibility_pair();},transport::Anchors::none,transport::PhaseInputs::gates);
        // 7772 rising pair: the fourth header field is the logical control identity.
        if(mode=="--rising-pair-pool")
            transport::pair_pool(std::cin,[](sim::MixedSessionState& w,const auto& h){return w.pool.initialize_rising_pair({h[3]});},transport::Anchors::none,transport::PhaseInputs::gates,1);
        std::size_t count=0;
        while(!pool && std::cin.peek()!=std::char_traits<char>::eof()) {
            if(++count>1000000)throw assets::BankError("private case budget exhausted");
            const auto f=transport::pool_row(std::cin);
            if(mode=="--pair") {
                transport::authored_pair<sim::PrivateObject>(f,[](sim::MixedPool& p){return p.initialize_visibility_pair();},
                    "visibility pair allocation exhausted","visibility pair inherits unknown slot state",false);
                std::cout<<'\n';continue;
            }
            if(mode=="--rising-pair") {
                transport::authored_pair<sim::PrivateObject>(f,[&](sim::MixedPool& p){return p.initialize_rising_pair({f.size()>3 ? f[3] : 0});},
                    "rising pair allocation exhausted","rising pair inherits unknown slot state",false);
                std::cout<<'\n';continue;
            }
            if(f.size()!=17 || f[0]>1)throw assets::BankError("invalid private case");
            auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("private word outside range");return static_cast<std::uint16_t>(f[i]);};
            auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("private byte outside range");return static_cast<std::uint8_t>(f[i]);};
            sim::PrivateObject object{static_cast<sim::PrivateUpdate>(f[0]),{w(1),w(2)},w(3),{b(4),{w(5),w(6),w(7)},b(8),b(9)},w(10),w(11),{f[12]}};
            const sim::PrivateGlobals globals{f[13],w(14),w(15)};
            if(!f[16] || f[16]>256)throw assets::BankError("private repetition budget exhausted");
            for(unsigned i=0;i<f[16];++i)sim::step_private_object(object,globals,scheduled);
            // Shared object encoding starts with pool type 5.
            transport::print_object(object);std::cout<<'\n';
        }
        std::cout.flush();if(std::cin.bad() || !std::cout)throw assets::BankError("private I/O failure");
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
