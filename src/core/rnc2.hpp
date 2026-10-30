#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <vector>

namespace wiz::rnc2 {

// Project safety policy, not an original machine capacity. Callers may lower
// either limit. Raising it requires an explicit API choice, never ROM metadata.
struct Limits {
    std::size_t packed_bytes = 4 * 1024 * 1024;
    std::size_t unpacked_bytes = 4 * 1024 * 1024;
};

class DecodeError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

struct Decoded {
    std::vector<std::uint8_t> bytes;
    std::size_t consumed_payload_bytes;
    std::uint16_t packed_crc16;
    std::uint16_t unpacked_crc16;
};

std::uint16_t crc16(std::span<const std::uint8_t> bytes) noexcept;

// Exactly one 18-byte header + payload, with no padding or trailing container.
// Throws DecodeError on unsupported/malformed input; allocation failure remains
// std::bad_alloc. No partial output escapes on failure. No CPU emulation.
Decoded decode(std::span<const std::uint8_t> block, Limits limits = {});

} // namespace wiz::rnc2
