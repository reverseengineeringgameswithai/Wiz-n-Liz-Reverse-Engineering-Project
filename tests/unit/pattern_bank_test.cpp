#include "assets/pattern_bank.hpp"

#include <iostream>
#include <limits>

namespace {
using namespace wiz::assets;
void require(bool yes) {
    if (!yes) throw std::runtime_error("pattern bank check failed");
}
template<typename F> void rejects(F f) {
    try { f(); } catch (const BankError&) { return; }
    throw std::runtime_error("invalid bank or atlas accepted");
}
std::vector<std::uint8_t> fixture(std::size_t count) {
    std::vector<std::uint8_t> bytes(34 + count * 40);
    bytes[32] = static_cast<std::uint8_t>((count - 1) >> 8U);
    bytes[33] = static_cast<std::uint8_t>(count - 1);
    return bytes;
}
} // namespace

int main() {
    try {
        // Independent byte-permutation examples from FUNC-0007; full ignored
        // bits checked too, rather than using only the game's even channels.
        require(palette_cram_word(0xF2, 0xA6) == 0x06A2);
        require(palette_cram_word(0xDE, 0x01) == 0x010E);
        require(diagnostic_rgba(0x000E, false) == Rgba{255, 0, 0, 255});
        require(diagnostic_rgba(0x00E0, false) == Rgba{0, 255, 0, 255});
        require(diagnostic_rgba(0x0E00, true) == Rgba{0, 0, 255, 0});
        require(diagnostic_rgba(0xF111, false) == Rgba{0, 0, 0, 255});
        constexpr std::array<std::uint8_t, 8> levels{0,36,73,109,146,182,219,255};
        for (std::uint16_t value = 0; value < 8; ++value)
            require(diagnostic_rgba(static_cast<std::uint16_t>(value * 2), false)[0] == levels[value]);

        auto bytes = fixture(2);
        bytes[0] = 0xF2; bytes[1] = 0xA6;
        // Asymmetric authored rows detect nibble, byte, word, row and tile flips.
        const std::array<std::uint8_t, 8> row_bytes{0x01,0x23,0x45,0x67,0x89,0xAB,0xCD,0xEF};
        for (std::size_t p = 0; p < row_bytes.size(); ++p) bytes[34 + p] = row_bytes[p];
        bytes[66] = 0xF1;
        for (std::size_t p = 0; p < 16; ++p) bytes[98 + p] = static_cast<std::uint8_t>(240 + p);
        const auto bank = parse_pattern_bank("authored.test", bytes);
        require(bank.logical_id == "authored.test" && bank.patterns.size() == 2);
        require(bank.palette[0].source == std::array<std::uint8_t,2>{0xF2,0xA6});
        require(bank.palette[0].cram_word == 0x06A2 && bank.palette[0].rgba[3] == 0);
        for (std::size_t p = 0; p < 16; ++p) require(bank.patterns[0].indices[p] == p);
        require(bank.patterns[1].indices[0] == 15 && bank.patterns[1].indices[1] == 1);
        for (std::size_t tile = 0; tile < 2; ++tile)
            for (std::size_t p = 0; p < 8; ++p)
                require(bank.patterns[tile].opaque_record[p] == 240 + tile * 8 + p);
        const auto atlas = make_atlas(bank, 3);
        require(atlas.width == 24 && atlas.height == 8);
        require(atlas.pixels[8] == bank.palette[15].rgba);
        require(atlas.pixels[24] == bank.palette[8].rgba);
        require(atlas.pixels[16] == Rgba{}); // Unoccupied third tile.
        const auto vertical = make_atlas(bank, 1);
        require(vertical.width == 8 && vertical.height == 16);
        require(vertical.pixels[64] == bank.palette[15].rgba);

        for (std::size_t length = 0; length < bytes.size(); ++length)
            rejects([&] { parse_pattern_bank("test", std::span(bytes).first(length)); });
        bytes.push_back(0);
        rejects([&] { parse_pattern_bank("test", bytes); });
        bytes.pop_back();
        rejects([&] { parse_pattern_bank("test", bytes, {1}); });
        for (const auto id : {"", "../evil", "a/b", "a..b", "a\\b", "A", "a-", "a\"b"})
            rejects([&] { parse_pattern_bank(id, bytes); });
        rejects([&] { parse_pattern_bank(std::string(97, 'a'), bytes); });
        rejects([&] { make_atlas(bank, 0); });
        rejects([&] { make_atlas(bank, 257); });
        rejects([&] { make_atlas(bank, 2, 127); });
        rejects([&] { make_atlas(PatternBank{}, 1); });
        auto invalid = bank;
        invalid.patterns[0].indices[0] = 16;
        rejects([&] { make_atlas(invalid); });
        rejects([] { encode_pam(Atlas{1,1,{}}); });
        rejects([] { encode_pam(Atlas{std::numeric_limits<std::size_t>::max(),2,{}}); });

        require(parse_pattern_bank("one", fixture(1)).patterns.size() == 1);
        const auto largest = fixture(65536);
        require(parse_pattern_bank("wire.maximum", largest).patterns.size() == 65536);
        rejects([&] { parse_pattern_bank("bounded", largest, {65535}); });
        // Larger than the observed bank, without adopting 442 as a fixed pool.
        const auto larger = parse_pattern_bank("authored.large", fixture(1000));
        require(make_atlas(larger).height == 256);
        std::cout << "palette, layout, records, extents, IDs, atlas and count boundaries passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
