#include "sim/terrain.hpp"

#include <fstream>
#include <iostream>
#include <sstream>

namespace {
std::vector<std::uint8_t> read_input(const char* path, std::size_t limit) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    const auto extent = input.tellg();
    if (!input || extent < 2 || extent > static_cast<std::streamoff>(limit))
        throw wiz::assets::BankError("terrain input unavailable or outside size limits");
    std::vector<std::uint8_t> data(static_cast<std::size_t>(extent));
    input.seekg(0);
    if (!input.read(reinterpret_cast<char*>(data.data()), static_cast<std::streamsize>(data.size()))
        || input.peek() != std::char_traits<char>::eof()) throw wiz::assets::BankError("terrain input changed");
    return data;
}
}
int main(int argc, char** argv) {
    using namespace wiz;
    if (argc != 5) { std::cerr << "usage: wiznliz-terrain scene-id scene.bin bank-id bank.bin\n"; return 2; }
    try {
        const auto scene = assets::parse_scene(argv[1], argv[3], read_input(argv[2], assets::max_scene_v1_bytes));
        const auto bank = assets::parse_pattern_bank(argv[3], read_input(argv[4], assets::max_bank_v1_bytes));
        std::string line;
        std::size_t cases = 0;
        while (std::getline(std::cin, line)) {
            std::istringstream fields(line);
            unsigned mode, x, y, sx, sy;
            std::string extra;
            if (line.size() > 100 || !(fields >> mode >> x >> y >> sx >> sy) || (fields >> extra)
                || mode > 4 || x > 65535 || y > 65535 || sx > 65535 || sy > 65535 || ++cases > 1000000)
                throw assets::BankError("invalid terrain case");
            sim::Position position{static_cast<std::uint16_t>(x), static_cast<std::uint16_t>(y)};
            sim::TerrainScratch scratch{static_cast<std::uint16_t>(sx), static_cast<std::uint16_t>(sy)};
            sim::TerrainSample sample;
            unsigned test_value = 0, flags;
            if (mode == 0) {
                sample = sim::query_terrain(scene, bank, position.x, position.y, scratch);
                flags = sample.value == 0 ? 4U : (sample.value & 0x80U ? 8U : 0U);
            } else if (mode < 4) {
                const auto contact = sim::probe_contact(scene, bank, position,
                    static_cast<sim::ContactProbe>(mode - 1), scratch);
                sample = contact.sample; test_value = contact.within_tile; flags = contact.nzvc;
            } else {
                const auto result = sim::settle_down(scene, bank, position, scratch);
                sample = result.contact.sample;
                test_value = result.moved ? 1U : result.contact.within_tile;
                flags = result.moved ? 0U : result.contact.nzvc; // MOVEQ #1 sets NZVC.
            }
            std::cout << position.x << ' ' << position.y << ' ' << scratch.x << ' ' << scratch.y
                << ' ' << unsigned(sample.value) << ' ' << test_value << ' ' << flags << ' ' << sample.map_word << '\n';
        }
        std::cout.flush();
        if (std::cin.bad() || !std::cout) throw assets::BankError("terrain I/O failed");
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 2; }
}
