#include "assets/pattern_bank.hpp"

#include <algorithm>
#include <limits>

namespace wiz::assets {
namespace {
bool valid_id(std::string_view id) {
    if (id.empty() || id.size() > 96) return false;
    bool previous_separator = true;
    for (const char c : id) {
        const bool alnum = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9');
        const bool separator = c == '.' || c == '_' || c == '-';
        if (!alnum && (!separator || previous_separator)) return false;
        previous_separator = !alnum;
    }
    return !previous_separator;
}

std::size_t product(std::size_t a, std::size_t b) {
    if (b != 0 && a > std::numeric_limits<std::size_t>::max() / b)
        throw BankError("image dimensions overflow");
    return a * b;
}
} // namespace

void require_resource_id(std::string_view id) {
    if (!valid_id(id)) throw BankError("invalid logical resource ID");
}

Pattern decode_pattern(std::span<const std::uint8_t, 32> packed,
                       std::span<const std::uint8_t, 8> record) {
    Pattern pattern;
    for (std::size_t p = 0; p < packed.size(); ++p) {
        pattern.indices[p * 2] = static_cast<std::uint8_t>(packed[p] >> 4U);
        pattern.indices[p * 2 + 1] = static_cast<std::uint8_t>(packed[p] & 15U);
    }
    std::copy(record.begin(), record.end(), pattern.opaque_record.begin());
    return pattern;
}

std::uint16_t palette_cram_word(std::uint8_t a, std::uint8_t b) noexcept {
    return static_cast<std::uint16_t>(((b & 15U) << 8U) | (b & 240U) | (a & 15U));
}

Rgba diagnostic_rgba(std::uint16_t word, bool transparent) noexcept {
    const auto channel = [word](unsigned shift) {
        return static_cast<std::uint8_t>((((word >> shift) & 7U) * 255U + 3U) / 7U);
    };
    return {channel(1), channel(5), channel(9), static_cast<std::uint8_t>(transparent ? 0 : 255)};
}

PatternBank parse_pattern_bank(std::string_view id, std::span<const std::uint8_t> bytes,
                               BankLimits limits) {
    require_resource_id(id);
    if (bytes.size() < 34) throw BankError("truncated pattern bank header");
    const std::size_t count = (static_cast<std::size_t>(bytes[32]) << 8U) + bytes[33] + 1;
    if (count > limits.patterns) throw BankError("pattern count exceeds configured limit");
    // Count comes from a 16-bit field, so this product cannot overflow size_t.
    if (bytes.size() != 34 + count * 40) throw BankError("pattern bank extent mismatch");
    PatternBank bank;
    bank.logical_id = id;
    for (std::size_t i = 0; i < bank.palette.size(); ++i) {
        auto& color = bank.palette[i];
        color.source = {bytes[i * 2], bytes[i * 2 + 1]};
        color.cram_word = palette_cram_word(color.source[0], color.source[1]);
        color.rgba = diagnostic_rgba(color.cram_word, i == 0);
    }
    bank.patterns.resize(count);
    for (std::size_t i = 0; i < count; ++i) {
        bank.patterns[i] = decode_pattern(
            std::span<const std::uint8_t, 32>(bytes.subspan(34 + i * 32, 32)),
            std::span<const std::uint8_t, 8>(bytes.subspan(34 + count * 32 + i * 8, 8)));
    }
    return bank;
}

Atlas make_atlas(const PatternBank& bank, std::size_t columns, std::size_t max_pixels) {
    if (columns == 0 || columns > 256 || bank.patterns.empty())
        throw BankError("atlas requires patterns and 1 to 256 columns");
    const auto rows = (bank.patterns.size() - 1) / columns + 1;
    Atlas atlas;
    atlas.width = product(columns, 8);
    atlas.height = product(rows, 8);
    const auto pixels = product(atlas.width, atlas.height);
    if (pixels > max_pixels) throw BankError("atlas exceeds configured pixel limit");
    atlas.pixels.resize(pixels, Rgba{});
    for (std::size_t i = 0; i < bank.patterns.size(); ++i) {
        const auto x = (i % columns) * 8;
        const auto y = (i / columns) * 8;
        for (std::size_t p = 0; p < 64; ++p) {
            const auto index = bank.patterns[i].indices[p];
            if (index >= bank.palette.size()) throw BankError("pixel palette index out of range");
            atlas.pixels[(y + p / 8) * atlas.width + x + p % 8] = bank.palette[index].rgba;
        }
    }
    return atlas;
}

std::vector<std::uint8_t> encode_pam(const Atlas& atlas) {
    if (atlas.width == 0 || atlas.height == 0
        || product(atlas.width, atlas.height) != atlas.pixels.size())
        throw BankError("inconsistent atlas dimensions");
    const auto header = "P7\nWIDTH " + std::to_string(atlas.width)
        + "\nHEIGHT " + std::to_string(atlas.height)
        + "\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n";
    const auto payload = product(atlas.pixels.size(), 4);
    if (payload > std::numeric_limits<std::size_t>::max() - header.size())
        throw BankError("image extent overflow");
    std::vector<std::uint8_t> result(header.begin(), header.end());
    result.reserve(header.size() + payload);
    for (const auto& pixel : atlas.pixels) result.insert(result.end(), pixel.begin(), pixel.end());
    return result;
}
} // namespace wiz::assets
