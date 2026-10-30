#include "hub_transport.hpp"
#include <string_view>
int main(int argc,char** argv) {
    using namespace wiz;
    try {
        if(argc!=2)throw assets::BankError("usage: wiznliz-collision --overlap|--service|--scheduled|--pickup-service|--pickup-scheduled|--pickup-hit|--probe-hit|--delivered|--ingredient|--second-ingredient|--anchor|--completion|--sparkle|--door|--spell-mix|--quad|--quad-pool|--world-pool|--hub-doors|--hub-door|--hub-exit|--scene-change|--second-level|--hint-screen");
        const std::string_view mode=argv[1];
        const bool pickup=mode=="--pickup-service" || mode=="--pickup-scheduled";
        if(mode!="--overlap" && mode!="--service" && mode!="--scheduled" && !pickup && mode!="--pickup-hit" && mode!="--probe-hit" && mode!="--delivered" && mode!="--ingredient" && mode!="--second-ingredient" && mode!="--anchor" && mode!="--completion" && mode!="--sparkle" && mode!="--door" && mode!="--spell-mix" && mode!="--hub-doors" && mode!="--hub-door" && mode!="--hub-exit" && mode!="--scene-change" && mode!="--second-level" && mode!="--hint-screen" && mode!="--quad" && mode!="--quad-pool" && mode!="--world-pool")throw assets::BankError("unsupported collision mode");
        // 783A seeded pool: the fourth header field is the logical caller
        // control; each phase row names the 78EE collision inputs explicitly.
        if(mode=="--quad-pool")
            transport::pair_pool(std::cin,[](sim::MixedSessionState& w,const auto& h){return w.pool.initialize_collision_quad({h[3]});},transport::Anchors::none,transport::PhaseInputs::collision,1);
        // The retained level world from the [6886,68D4) setup (world_pool).
        if(mode=="--world-pool") transport::world_pool(std::cin);
        std::size_t count=0;
        while(mode!="--quad-pool" && mode!="--world-pool" && std::cin.peek()!=std::char_traits<char>::eof()) {
            if(++count>1000000)throw assets::BankError("collision case budget exhausted");
            const auto f=transport::pool_row(std::cin);
            if(mode=="--quad") {transport::authored_quad(f);std::cout<<'\n';continue;}
            if(mode=="--pickup-hit") {transport::authored_pickup_hit(f);std::cout<<'\n';continue;}
            if(mode=="--probe-hit") {transport::authored_probe_hit(f);std::cout<<'\n';continue;}
            if(mode=="--delivered") {transport::authored_delivered(f);std::cout<<'\n';continue;}
            if(mode=="--ingredient") {transport::authored_ingredient(f);std::cout<<'\n';continue;}
            if(mode=="--second-ingredient") {transport::authored_second_ingredient(f);std::cout<<'\n';continue;}
            if(mode=="--anchor") {transport::authored_anchor(f);std::cout<<'\n';continue;}
            if(mode=="--completion") {transport::authored_completion(f);std::cout<<'\n';continue;}
            if(mode=="--sparkle") {transport::authored_sparkle(f);std::cout<<'\n';continue;}
            if(mode=="--door") {transport::authored_door(f);std::cout<<'\n';continue;}
            if(mode=="--spell-mix") {transport::authored_spell_mix(f);std::cout<<'\n';continue;}
            if(mode=="--hub-doors") {transport::authored_hub_doors(f);std::cout<<'\n';continue;}
            if(mode=="--hub-door") {transport::authored_hub_door(f);std::cout<<'\n';continue;}
            if(mode=="--hub-exit") {transport::authored_hub_exit(f);std::cout<<'\n';continue;}
            if(mode=="--scene-change") {transport::authored_scene_change(f);std::cout<<'\n';continue;}
            if(mode=="--second-level") {transport::authored_second_level(f);std::cout<<'\n';continue;}
            if(mode=="--hint-screen") {transport::authored_hint_screen(f);std::cout<<'\n';continue;}
            if(f.size()!=(mode=="--overlap" ? 7U : 22U))throw assets::BankError("invalid collision case extent");
            auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("collision word outside range");return static_cast<std::uint16_t>(f[i]);};
            auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("collision byte outside range");return static_cast<std::uint8_t>(f[i]);};
            if(mode=="--overlap") {std::cout<<sim::overlaps_control({w(0),w(1)},{w(2),w(3)},{w(4),w(5)},w(6))<<'\n';continue;}
            sim::CollisionProbe object{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),w(10),{f[11]},w(12),w(13)};
            sim::CollisionInputs inputs{{w(14),w(15)},{w(16),w(17),{}}};
            if(f[18]>1 || !f[21] || f[21]>256)throw assets::BankError("invalid collision presence/repetition");
            const sim::Position secondary{w(19),w(20)};
            if(f[18])inputs.config.secondary=secondary;
            else if(secondary.x || secondary.y)throw assets::BankError("unconsumed secondary coordinates");
            if(pickup) {
                // The same 22 fields as a 6AF0 pickup on record 0 (6BD6 service).
                sim::Pickup p{object.position,object.flags,object.presentation,object.target,object.countdown,object.control,object.x_extent,object.y_extent,0};
                for(unsigned i=0;i<f[21];++i)sim::step_pickup(p,inputs,mode=="--pickup-scheduled");
                transport::print_object(p);std::cout<<'\n';continue;
            }
            for(unsigned i=0;i<f[21];++i)sim::step_collision_probe(object,inputs,mode=="--scheduled");
            transport::print_object(object);std::cout<<'\n';
        }
        std::cout.flush();if(std::cin.bad() || !std::cout)throw assets::BankError("collision I/O failure");
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
