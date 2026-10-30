#include "assets/scene.hpp"

#include <limits>

namespace wiz::assets {
namespace {
std::uint16_t word(std::span<const std::uint8_t> bytes, std::size_t offset) {
    if (offset > bytes.size() || bytes.size() - offset < 2) throw BankError("truncated scene word");
    return static_cast<std::uint16_t>((static_cast<unsigned>(bytes[offset]) << 8U) | bytes[offset + 1]);
}
Coordinate coordinate(std::span<const std::uint8_t> bytes, std::size_t offset, unsigned y_add) {
    const auto x = word(bytes, offset), y = word(bytes, offset + 2);
    return {x, y, static_cast<std::uint16_t>(x + 128U), static_cast<std::uint16_t>(y + y_add)};
}
std::size_t product(std::size_t a, std::size_t b) {
    if (b && a > std::numeric_limits<std::size_t>::max() / b) throw BankError("scene dimensions overflow");
    return a * b;
}
} // namespace

std::uint16_t relocate_map_word(std::uint16_t source, std::uint16_t base) noexcept {
    return static_cast<std::uint16_t>((static_cast<unsigned>(source) + base) | 0x4000U);
}

SceneResource parse_scene(std::string_view id, std::string_view base_id,
                          std::span<const std::uint8_t> bytes, SceneLimits limits) {
    require_resource_id(id);
    require_resource_id(base_id);
    const std::size_t count = static_cast<std::size_t>(word(bytes, 0)) + 1;
    if (count > limits.coordinates) throw BankError("scene coordinate count exceeds limit");
    const auto starts = 2 + count * 4;
    const std::size_t patterns = static_cast<std::size_t>(word(bytes, starts + 8)) + 1;
    if (patterns > limits.patterns) throw BankError("scene pattern count exceeds limit");
    // Both counts are at most 65536, so these wire extents cannot overflow size_t.
    const auto pattern_start = starts + 10;
    const auto map_header = pattern_start + patterns * 32;
    const auto map_start = map_header + 4;
    const auto records = map_start + 8192;
    if (bytes.size() != records + patterns * 8) throw BankError("scene extent mismatch");
    if (word(bytes, map_header) != 128 || word(bytes, map_header + 2) != 32)
        throw BankError("unsupported scene shape - verified import requires 128 by 32");
    SceneResource scene;
    scene.logical_id = id;
    scene.base_bank_id = base_id;
    scene.columns = 128;
    scene.rows = 32;
    scene.coordinates.reserve(count);
    for (std::size_t i = 0; i < count; ++i) scene.coordinates.push_back(coordinate(bytes, 2 + i * 4, 112));
    for (std::size_t i = 0; i < 2; ++i) scene.state_starts[i] = coordinate(bytes, starts + i * 4, 120);
    scene.additional_patterns.reserve(patterns);
    for (std::size_t i = 0; i < patterns; ++i)
        scene.additional_patterns.push_back(decode_pattern(
            std::span<const std::uint8_t,32>(bytes.subspan(pattern_start + i * 32,32)),
            std::span<const std::uint8_t,8>(bytes.subspan(records + i * 8,8))));
    scene.cells.reserve(4096);
    for (std::size_t i = 0; i < 4096; ++i) {
        const auto raw = word(bytes, map_start + i * 2);
        const auto relative = relocate_map_word(raw, 0);
        scene.cells.push_back({raw, static_cast<std::size_t>(raw & 0x07ffU),
            (raw & 0x0800U) != 0, (raw & 0x1000U) != 0, (raw & 0x8000U) != 0,
            static_cast<std::uint8_t>((relative >> 13U) & 3U)});
    }
    return scene;
}

Atlas make_scene_image(const SceneResource& scene, const PatternBank& base, std::size_t max_pixels) {
    if (base.logical_id != scene.base_bank_id) throw BankError("scene base bank ID mismatch");
    if (!scene.columns || !scene.rows || product(scene.columns, scene.rows) != scene.cells.size())
        throw BankError("inconsistent scene map dimensions");
    Atlas image;
    image.width = product(scene.columns, 8);
    image.height = product(scene.rows, 8);
    const auto count = product(image.width, image.height);
    if (count > max_pixels) throw BankError("scene image exceeds pixel limit");
    image.pixels.resize(count);
    for (std::size_t cell = 0; cell < scene.cells.size(); ++cell) {
        const auto& entry = scene.cells[cell];
        if (entry.palette_selector != 2) throw BankError("scene references an unavailable palette");
        const Pattern* pattern = nullptr;
        if (entry.pattern_index < base.patterns.size()) pattern = &base.patterns[entry.pattern_index];
        else {
            const auto extra = entry.pattern_index - base.patterns.size();
            if (extra >= scene.additional_patterns.size()) throw BankError("scene pattern reference out of range");
            pattern = &scene.additional_patterns[extra];
        }
        const auto x = cell % scene.columns * 8, y = cell / scene.columns * 8;
        for (std::size_t dy = 0; dy < 8; ++dy) {
            for (std::size_t dx = 0; dx < 8; ++dx) {
                const auto sx = entry.flip_x ? 7 - dx : dx;
                const auto sy = entry.flip_y ? 7 - dy : dy;
                const auto index = pattern->indices[sy * 8 + sx];
                if (index >= base.palette.size()) throw BankError("scene pixel index out of range");
                image.pixels[(y + dy) * image.width + x + dx] = base.palette[index].rgba;
            }
        }
    }
    return image;
}
} // namespace wiz::assets
