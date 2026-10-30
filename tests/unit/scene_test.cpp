#include "assets/scene.hpp"

#include <iostream>
#include <limits>

namespace {
using namespace wiz::assets;
void require(bool value) {
    if (!value) throw std::runtime_error("scene check failed");
}
template<typename F> void rejects(F function) {
    try { function(); } catch (const BankError&) { return; }
    throw std::runtime_error("invalid scene accepted");
}
void set_word(std::vector<std::uint8_t>& data, std::size_t offset, unsigned word) {
    data[offset] = static_cast<std::uint8_t>(word >> 8U);
    data[offset + 1] = static_cast<std::uint8_t>(word);
}
std::vector<std::uint8_t> fixture() {
    std::vector<std::uint8_t> data(8252); // One coordinate and one additional pattern.
    set_word(data, 2, 0xffff); set_word(data, 4, 0xffb0);
    set_word(data, 6, 0xff80); set_word(data, 8, 0xfff0);
    set_word(data, 10, 10); set_word(data, 12, 20);
    // Pattern starts at 16: count2 + coordinate4 + starts8 + count2.
    data[16] = 0x10; data[19] = 0x02; data[44] = 0x30; data[47] = 0x04;
    set_word(data, 48, 128); set_word(data, 50, 32);
    set_word(data, 52, 0x0001); set_word(data, 54, 0x0801);
    set_word(data, 56, 0x1001); set_word(data, 58, 0x9801);
    for (std::size_t i = 0; i < 8; ++i) data[8244 + i] = static_cast<std::uint8_t>(160 + i);
    return data;
}
} // namespace

int main() {
    try {
        // Original ADD.W wraps before OR.W; carries may affect attribute bits.
        require(relocate_map_word(0xffff,1) == 0x4000);
        require(relocate_map_word(0x07ff,1) == 0x4800);
        require(relocate_map_word(0x1234,0xfffe) == 0x5232);
        auto data = fixture();
        const auto scene = parse_scene("authored.scene", "authored.bank", data);
        require(scene.coordinates.size() == 1 && scene.additional_patterns.size() == 1);
        require(scene.columns == 128 && scene.rows == 32 && scene.cells.size() == 4096);
        require(scene.coordinates[0].source_x == 0xffff && scene.coordinates[0].loaded_x == 127);
        require(scene.coordinates[0].loaded_y == 32);
        require(scene.state_starts[0].loaded_x == 0 && scene.state_starts[0].loaded_y == 104);
        require(scene.state_starts[1].loaded_x == 138 && scene.state_starts[1].loaded_y == 140);
        require(scene.cells[3].source_word == 0x9801 && scene.cells[3].pattern_index == 1);
        require(scene.cells[3].flip_x && scene.cells[3].flip_y && scene.cells[3].priority);
        require(scene.cells[3].palette_selector == 2);
        for (std::size_t i = 0; i < 8; ++i) require(scene.additional_patterns[0].opaque_record[i] == 160 + i);
        PatternBank bank;
        bank.logical_id = "authored.bank";
        bank.patterns.resize(1);
        bank.palette[1].rgba = {255,0,0,255}; bank.palette[2].rgba = {0,255,0,255};
        bank.palette[3].rgba = {0,0,255,255}; bank.palette[4].rgba = {255,255,0,255};
        const auto image = make_scene_image(scene, bank);
        require(image.width == 1024 && image.height == 256);
        for (std::size_t i = 0; i < 4; ++i) require(image.pixels[i * 8] == bank.palette[i + 1].rgba);
        require(image.pixels[7] == bank.palette[2].rgba);
        require(image.pixels[7 * image.width] == bank.palette[3].rgba);
        require(image.pixels[8 * image.width] == Rgba{});
        for (std::size_t length = 0; length < data.size(); ++length)
            rejects([&] { parse_scene("test", "base", std::span(data).first(length)); });
        rejects([&] { parse_scene("test", "base", data, {0,65536}); });
        rejects([&] { parse_scene("test", "base", data, {4096,0}); });
        rejects([&] { parse_scene("../test", "base", data); });
        rejects([&] { parse_scene("test", "bad/id", data); });
        data.push_back(0); rejects([&] { parse_scene("test", "base", data); }); data.pop_back();
        set_word(data,48,64); rejects([&] { parse_scene("test", "base", data); });
        rejects([&] { make_scene_image(scene, bank, 262143); });
        auto broken = scene;
        broken.cells[0].pattern_index = 2;
        rejects([&] { make_scene_image(broken, bank); });
        broken = scene; broken.cells[0].palette_selector = 3;
        rejects([&] { make_scene_image(broken, bank); });
        broken = scene; broken.base_bank_id = "different";
        rejects([&] { make_scene_image(broken, bank); });
        broken = scene; broken.columns = std::numeric_limits<std::size_t>::max();
        rejects([&] { make_scene_image(broken, bank); });
        broken = scene; broken.additional_patterns[0].indices[0] = 16;
        rejects([&] { make_scene_image(broken, bank); });
        std::cout << "scene coordinates, wrap, layout, records, flips, links and bounds passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
