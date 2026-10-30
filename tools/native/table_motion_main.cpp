#include "mixed_transport.hpp"
#include <string_view>

int main(int argc,char** argv) {
    using namespace wiz;
    try {
        if(argc!=2 || (std::string_view(argv[1])!="--handler" && std::string_view(argv[1])!="--scheduled"))
            throw assets::BankError("usage: wiznliz-table-motion --handler|--scheduled");
        const bool scheduled=std::string_view(argv[1])=="--scheduled";
        std::size_t count=0;
        while(std::cin.peek()!=std::char_traits<char>::eof()) {
            if(++count>1000000)throw assets::BankError("table case budget exhausted");
            const auto f=transport::pool_row(std::cin);
            if(f.size()!=18)throw assets::BankError("invalid table case");
            auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("table word outside range");return static_cast<std::uint16_t>(f[i]);};
            auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("table byte outside range");return static_cast<std::uint8_t>(f[i]);};
            sim::TableMotion object{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),w(10),{f[11]},f[12],w(13),w(14)};
            const auto loops=w(15);
            if(!f[16] || f[16]>256 || f[17]>65536 || (std::uint64_t(loops)+1)*f[16]>1048576)
                throw assets::BankError("table repetition budget exhausted");
            for(unsigned i=0;i<f[16];++i)sim::step_table_motion(object,loops,scheduled,f[17]);
            transport::print_object(object);std::cout<<'\n';
        }
        std::cout.flush();if(std::cin.bad() || !std::cout)throw assets::BankError("table I/O failure");
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
