#include "sim/banner.hpp"
#include <array>

namespace wiz::sim {
LevelBannerRequest request_level_banner(LevelBannerConfig config, TerrainScratch& scratch) {
    const auto index = static_cast<unsigned>(config.difficulty);
    if (index >= 4) throw assets::BankError("unsupported level banner difficulty");
    constexpr std::array<std::uint16_t,4> final_stages{7,15,31,55};
    constexpr std::array<std::uint16_t,4> number_offsets{56,52,54,58};
    const bool final = config.stage == final_stages[index];
    // Original LSL.W then signed word address addition. The renderer uses only
    // the low address word, so normalization preserves both wrap boundaries.
    const auto destination = static_cast<std::uint16_t>(0xe000u + (unsigned(config.row) << 7));
    LevelBannerRequest request{static_cast<std::uint8_t>(2*index + unsigned(final)),destination,{}};
    if (!final) request.number = BannerNumberRequest{static_cast<std::uint16_t>(config.stage+1u),
        static_cast<std::uint16_t>(destination+number_offsets[index])};
    scratch.y = config.row;
    return request;
}
} // namespace wiz::sim
