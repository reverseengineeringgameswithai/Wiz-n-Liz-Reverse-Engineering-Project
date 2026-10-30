#pragma once

#include "assets/pattern_bank.hpp"

namespace wiz::assets {

struct Coordinate {
    std::uint16_t source_x{}, source_y{};
    std::uint16_t loaded_x{}, loaded_y{}; // Original 16-bit addition, not host world limits.
};
struct MapCell {
    std::uint16_t source_word{};
    std::size_t pattern_index{}; // Relative to concatenated base/additional patterns.
    bool flip_x{}, flip_y{}, priority{};
    std::uint8_t palette_selector{};
};
struct SceneResource {
    std::string logical_id, base_bank_id;
    std::vector<Coordinate> coordinates; // Purpose unknown; do not invent entities.
    std::array<Coordinate, 2> state_starts{};
    std::vector<Pattern> additional_patterns;
    std::size_t columns{}, rows{};
    std::vector<MapCell> cells;
};
struct SceneLimits {
    std::size_t coordinates = 4096;
    std::size_t patterns = 65536;
};
inline constexpr std::size_t max_scene_v1_bytes = 2 + 65536 * 4 + 10 + 65536 * 40 + 4 + 8192;

// Exact word operation at 0x3F48..0x3F54, separate from native logical indexing.
std::uint16_t relocate_map_word(std::uint16_t source, std::uint16_t base) noexcept;
// Only the corroborated 128x32 import shape is currently supported. Host types
// are extensible; other wire shapes must gain evidence instead of silent guesses.
SceneResource parse_scene(std::string_view id, std::string_view base_bank_id,
                          std::span<const std::uint8_t> bytes, SceneLimits limits = {});
// One decoded map plane, diagnostic palette. No camera, backdrop, entities,
// inter-plane priority, fades or sprite emulation is supplied here.
Atlas make_scene_image(const SceneResource& scene, const PatternBank& base,
                       std::size_t max_pixels = 4 * 1024 * 1024);

} // namespace wiz::assets
