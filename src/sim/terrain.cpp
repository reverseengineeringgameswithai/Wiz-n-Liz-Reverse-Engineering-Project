#include "sim/terrain.hpp"

namespace wiz::sim {
namespace {
std::uint16_t word(unsigned value) noexcept { return static_cast<std::uint16_t>(value); }
int signed_word(unsigned value) noexcept {
    value &= 65535U;
    return value < 32768U ? static_cast<int>(value) : static_cast<int>(value) - 65536;
}
std::uint8_t compare_byte(std::uint8_t lhs, std::uint8_t rhs) noexcept {
    const auto difference = static_cast<std::uint8_t>(static_cast<unsigned>(lhs) - rhs);
    return static_cast<std::uint8_t>((difference & 0x80U ? 8U : 0U) | (difference == 0 ? 4U : 0U)
        | (((lhs ^ rhs) & (lhs ^ difference) & 0x80U) ? 2U : 0U) | (lhs < rhs ? 1U : 0U));
}
} // namespace

TerrainSample query_terrain(const assets::SceneResource& scene, const assets::PatternBank& bank,
                            std::uint16_t x, std::uint16_t y, TerrainScratch& scratch) {
    if (scene.base_bank_id != bank.logical_id) throw assets::BankError("terrain base bank ID mismatch");
    if (scene.columns != 128 || scene.rows != 32 || scene.cells.size() != 4096)
        throw assets::BankError("terrain query requires verified 128 by 32 map");
    const auto local_x = word(static_cast<unsigned>(x) - 128U);
    const auto local_y = word(static_cast<unsigned>(y) - 128U);
    TerrainSample sample;
    sample.above_map = (local_y & 0x8000U) != 0;
    if (!sample.above_map) {
        // ADDA.W sign-extends the low word of MULU.W. Large positive y may
        // alias earlier rows, or point outside the map: do not silently clamp.
        const int byte_offset = static_cast<int>(((local_x & 1023U) >> 3U) * 2U)
            + signed_word((static_cast<unsigned>(local_y) >> 3U) * 256U);
        if (byte_offset < 0 || byte_offset >= 8192) throw assets::BankError("terrain address outside map resource");
        sample.map_word = assets::relocate_map_word(scene.cells[static_cast<std::size_t>(byte_offset) / 2].source_word, 0);
    }
    const auto index = static_cast<std::size_t>(sample.map_word & 0x07ffU);
    const assets::Pattern* pattern;
    if (index < bank.patterns.size()) pattern = &bank.patterns[index];
    else {
        const auto extra = index - bank.patterns.size();
        if (extra >= scene.additional_patterns.size()) throw assets::BankError("terrain record reference out of range");
        pattern = &scene.additional_patterns[extra];
    }
    // Publish scratch only after validation succeeds; failed host queries have
    // no partial state changes. Above-map behavior uses the incoming scratch.
    if (!sample.above_map) scratch = {local_x, local_y};
    sample.column = static_cast<std::uint8_t>((scratch.x & 7U) ^ ((sample.map_word & 0x0800U) ? 7U : 0U));
    sample.value = pattern->opaque_record[sample.column];
    return sample;
}

Contact probe_contact(const assets::SceneResource& scene, const assets::PatternBank& bank,
                      Position position, ContactProbe probe, TerrainScratch& scratch) {
    unsigned y_add;
    switch (probe) {
    case ContactProbe::upper: y_add = 22; break;
    case ContactProbe::foot: y_add = 23; break;
    case ContactProbe::lower: y_add = 24; break;
    default: throw assets::BankError("unknown contact probe");
    }
    const auto sample = query_terrain(scene, bank, word(position.x + 12U), word(position.y + y_add), scratch);
    const auto within = static_cast<std::uint8_t>((scratch.y & 7U) + 1U);
    return {sample, within, compare_byte(within, sample.value)};
}

SettleResult settle_down(const assets::SceneResource& scene, const assets::PatternBank& bank,
                         Position& position, TerrainScratch& scratch) {
    const auto contact = probe_contact(scene, bank, position, ContactProbe::foot, scratch);
    const bool moved = !contact.equal();
    if (moved) position.y = word(position.y + 1U);
    return {contact, moved};
}
} // namespace wiz::sim
