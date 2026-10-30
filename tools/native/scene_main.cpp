#include "assets/scene.hpp"

#include <fstream>
#include <iostream>

namespace {
std::vector<std::uint8_t> read_input(const char* path, std::size_t limit) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    const auto extent = input.tellg();
    if (!input || extent < 2 || extent > static_cast<std::streamoff>(limit))
        throw wiz::assets::BankError("scene input unavailable or outside size limits");
    std::vector<std::uint8_t> data(static_cast<std::size_t>(extent));
    input.seekg(0);
    if (!input.read(reinterpret_cast<char*>(data.data()), static_cast<std::streamsize>(data.size()))
        || input.peek() != std::char_traits<char>::eof())
        throw wiz::assets::BankError("scene input changed or could not be read");
    return data;
}
}

int main(int argc, char** argv) {
    using namespace wiz::assets;
    if (argc != 5) {
        std::cerr << "{\"status\":\"error\",\"message\":\"usage: wiznliz-scene-preview scene-id scene.bin bank-id bank.bin\"}\n";
        return 2;
    }
    try {
        const auto scene = parse_scene(argv[1], argv[3], read_input(argv[2], max_scene_v1_bytes));
        const auto bank = parse_pattern_bank(argv[3], read_input(argv[4], max_bank_v1_bytes));
        const auto image = make_scene_image(scene, bank);
        const auto pam = encode_pam(image);
        std::cout.write(reinterpret_cast<const char*>(pam.data()), static_cast<std::streamsize>(pam.size()));
        std::cout.flush();
        if (!std::cout) throw BankError("failed writing scene preview");
        std::cerr << "{\"status\":\"ok\",\"schema_version\":1,\"renderer\":\"wiznliz-scene-preview\""
                  << ",\"logical_id\":\"" << scene.logical_id << "\",\"base_bank_id\":\"" << bank.logical_id
                  << "\",\"coordinates\":" << scene.coordinates.size()
                  << ",\"additional_patterns\":" << scene.additional_patterns.size()
                  << ",\"base_patterns\":" << bank.patterns.size() << ",\"map_cells\":" << scene.cells.size()
                  << ",\"width\":" << image.width << ",\"height\":" << image.height
                  << ",\"palette_policy\":\"normal-rgb3-rounded-v1\",\"single_plane\":true}\n";
        return 0;
    } catch (const BankError& error) {
        std::cerr << "{\"status\":\"error\",\"message\":\"" << error.what() << "\"}\n";
    } catch (const std::exception&) {
        std::cerr << "{\"status\":\"error\",\"message\":\"resource or I/O failure\"}\n";
    }
    return 2;
}
