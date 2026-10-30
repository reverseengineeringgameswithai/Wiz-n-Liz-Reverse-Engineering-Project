#pragma once

#include "assets/scene.hpp"

namespace wiz::sim {

// The original query retains these two words when translated y is negative.
// Explicit state preserves that behavior without global RAM or host pointers.
struct TerrainScratch { std::uint16_t x{}, y{}; };
struct TerrainSample {
    std::uint16_t map_word{}; // Logical index, original attributes, palette-2 OR.
    std::uint8_t column{}, value{};
    bool above_map{};
};
struct Position { std::uint16_t x{}, y{}; };
struct Contact {
    TerrainSample sample;
    std::uint8_t within_tile{}; // One-based y position compared with record byte.
    std::uint8_t nzvc{};        // CMP.B N/Z/V/C, for verified branching callers.
    bool equal() const noexcept { return (nzvc & 4U) != 0; }
};
enum class ContactProbe { upper, foot, lower }; // Original y offsets 22/23/24.
struct SettleResult { Contact contact; bool moved{}; };

// No vertical mirroring is applied to the record: the original ignores bit 12.
// Nonnegative y uses original low-word signed row addressing. An address outside
// this resource fails explicitly instead of reading unrelated original RAM.
TerrainSample query_terrain(const assets::SceneResource& scene, const assets::PatternBank& bank,
                            std::uint16_t x, std::uint16_t y, TerrainScratch& scratch);
Contact probe_contact(const assets::SceneResource& scene, const assets::PatternBank& bank,
                      Position position, ContactProbe probe, TerrainScratch& scratch);
// Verified one-pixel downward step at 0x9A80. This is not a complete controller.
SettleResult settle_down(const assets::SceneResource& scene, const assets::PatternBank& bank,
                         Position& position, TerrainScratch& scratch);
} // namespace wiz::sim
