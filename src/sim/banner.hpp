#pragma once

#include "sim/terrain.hpp"
#include <optional>

namespace wiz::sim {
enum class Difficulty : std::uint8_t { apprentice, wizard, sorcerer, super_wizard };
struct LevelBannerConfig {
    Difficulty difficulty{};
    std::uint16_t stage{}, row{};
};
struct BannerNumberRequest {
    std::uint16_t value{}, destination{};
    bool operator==(const BannerNumberRequest&) const = default;
};
struct LevelBannerRequest {
    // Logical resource: difficulty * 2 + final-level flag. Text assets and the
    // centered-text / two-glyph number renderers remain outside this contract.
    std::uint8_t label{};
    std::uint16_t destination{}; // Normalized low word of the tilemap address.
    std::optional<BannerNumberRequest> number;
    bool operator==(const LevelBannerRequest&) const = default;
};
// 63E2..644C: centered label first, then optional numeric request. The shared
// scratch Y receives the original row even when the final-level tail is taken.
LevelBannerRequest request_level_banner(LevelBannerConfig config, TerrainScratch& scratch);
} // namespace wiz::sim
