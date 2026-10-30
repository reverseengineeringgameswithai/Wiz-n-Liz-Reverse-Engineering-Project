#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace wiz::assets {

class BankError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

using Rgba = std::array<std::uint8_t, 4>;
struct PaletteEntry {
    std::array<std::uint8_t, 2> source{};
    std::uint16_t cram_word{};
    Rgba rgba{};
};
struct Pattern {
    std::array<std::uint8_t, 64> indices{}; // Row-major 8x8, no flips applied.
    std::array<std::uint8_t, 8> opaque_record{}; // Preserved bytes; terrain column/contact use verified in sim/terrain.
};
struct PatternBank {
    std::string logical_id;
    std::array<PaletteEntry, 16> palette{};
    std::vector<Pattern> patterns;
};
struct BankLimits {
    std::size_t patterns = 65536; // Wire count + 1, not a native engine capacity.
};
inline constexpr std::size_t max_bank_v1_bytes = 34 + 65536 * 40;

void require_resource_id(std::string_view id);
Pattern decode_pattern(std::span<const std::uint8_t, 32> packed,
                       std::span<const std::uint8_t, 8> record);

// Original palette byte permutation at 0x13754; preserves non-color bits.
std::uint16_t palette_cram_word(std::uint8_t a, std::uint8_t b) noexcept;
// Diagnostic digital mapping: normal-mode 3-bit RGB, rounded full-range scale.
// Does not model analog voltage, shadow/highlight, fades or scene backdrop.
Rgba diagnostic_rgba(std::uint16_t cram_word, bool transparent) noexcept;
PatternBank parse_pattern_bank(std::string_view logical_id,
                               std::span<const std::uint8_t> bytes,
                               BankLimits limits = {});

struct Atlas {
    std::size_t width{}, height{};
    std::vector<Rgba> pixels;
};
// Explicit host safety bounds. Unused cells are transparent black.
Atlas make_atlas(const PatternBank& bank, std::size_t columns = 32,
                 std::size_t max_pixels = 4 * 1024 * 1024);
std::vector<std::uint8_t> encode_pam(const Atlas& atlas);

} // namespace wiz::assets
