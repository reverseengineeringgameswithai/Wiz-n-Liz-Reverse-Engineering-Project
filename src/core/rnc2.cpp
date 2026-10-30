#include "core/rnc2.hpp"

#include <array>
#include <string_view>
#include <utility>

namespace wiz::rnc2 {
namespace {

using Bytes = std::span<const std::uint8_t>;

std::uint32_t big_endian(Bytes bytes) {
    std::uint32_t value = 0;
    for (const auto byte : bytes) {
        value = (value << 8U) | byte;
    }
    return value;
}

// Control bits and raw bytes share a cursor; unused bits in the current control
// byte survive raw reads. A new control byte is fetched only when exhausted.
class Stream {
public:
    explicit Stream(Bytes payload) : payload_(payload) {}

    std::uint8_t raw() {
        if (cursor_ == payload_.size()) {
            throw DecodeError("truncated RNC2 payload or missing terminator");
        }
        return payload_[cursor_++];
    }

    unsigned bit() {
        if (remaining_ == 0) {
            control_ = raw();
            remaining_ = 8;
        }
        --remaining_;
        return (control_ >> remaining_) & 1U;
    }

    unsigned four_bits() {
        unsigned value = 0;
        for (unsigned i = 0; i < 4; ++i) {
            value = (value << 1U) | bit();
        }
        return value;
    }

    std::size_t consumed() const noexcept { return cursor_; }

private:
    Bytes payload_;
    std::size_t cursor_ = 0;
    unsigned control_ = 0;
    unsigned remaining_ = 0;
};

enum class Kind { literal, match, literal_run, extended };
struct Token {
    std::string_view prefix;
    Kind kind;
    unsigned length;
};

// Declarative wire grammar, documented with independent cases in the vault.
// This is project code, not the reference decoder or the game's CPU routine.
constexpr std::array tokens{
    Token{"0", Kind::literal, 1}, Token{"110", Kind::match, 2},
    Token{"1110", Kind::match, 3}, Token{"1000", Kind::match, 4},
    Token{"1010", Kind::match, 5}, Token{"10010", Kind::match, 6},
    Token{"10011", Kind::match, 7}, Token{"10110", Kind::match, 8},
    Token{"10111", Kind::literal_run, 0}, Token{"1111", Kind::extended, 0},
};
constexpr std::array<std::string_view, 16> distance_codes{
    "0", "110", "1000", "1001", "10101", "10111", "11101", "11111",
    "101000", "101001", "101100", "101101", "111000", "111001", "111100", "111101",
};

template <std::size_t N>
std::size_t prefix_index(Stream& stream, const std::array<std::string_view, N>& codes) {
    std::array<char, 6> prefix{};
    for (std::size_t count = 1; count <= prefix.size(); ++count) {
        prefix[count - 1] = stream.bit() ? '1' : '0';
        const std::string_view observed(prefix.data(), count);
        for (std::size_t i = 0; i < N; ++i) {
            if (observed == codes[i]) {
                return i;
            }
        }
    }
    throw DecodeError("invalid RNC2 prefix");
}

constexpr auto token_codes = [] {
    std::array<std::string_view, tokens.size()> codes{};
    for (std::size_t i = 0; i < tokens.size(); ++i) {
        codes[i] = tokens[i].prefix;
    }
    return codes;
}();

void require_room(std::size_t produced, std::size_t amount, std::size_t limit) {
    // Invariant produced <= limit avoids both subtraction and addition overflow.
    if (amount > limit - produced) {
        throw DecodeError("RNC2 token exceeds declared output length");
    }
}

} // namespace

std::uint16_t crc16(Bytes bytes) noexcept {
    unsigned value = 0;
    for (const auto byte : bytes) {
        value ^= byte;
        for (unsigned bit = 0; bit < 8; ++bit) {
            value = (value >> 1U) ^ ((value & 1U) ? 0xA001U : 0U);
        }
    }
    return static_cast<std::uint16_t>(value);
}

Decoded decode(Bytes block, Limits limits) {
    constexpr std::size_t header_size = 18;
    if (block.size() < header_size) {
        throw DecodeError("truncated RNC header");
    }
    if (big_endian(block.first(4)) != 0x524E4302U) {
        throw DecodeError("unsupported signature; expected RNC method 2");
    }
    const std::size_t unpacked = big_endian(block.subspan(4, 4));
    const std::size_t packed = big_endian(block.subspan(8, 4));
    if (unpacked == 0 || unpacked > limits.unpacked_bytes || packed < 2 || packed > limits.packed_bytes) {
        throw DecodeError("RNC2 lengths outside configured limits");
    }
    if (packed != block.size() - header_size) {
        throw DecodeError("RNC2 packed length must match exact input extent");
    }
    const auto payload = block.subspan(header_size);
    const auto packed_crc = crc16(payload);
    if (packed_crc != big_endian(block.subspan(14, 2))) {
        throw DecodeError("RNC2 packed CRC mismatch");
    }
    Stream stream(payload);
    // All four initial bit combinations are ignored by the pinned reference.
    // Their game meaning is unknown. Header bytes 16/17 are likewise opaque.
    stream.bit();
    stream.bit();
    std::vector<std::uint8_t> output;
    output.reserve(unpacked);
    for (;;) {
        const auto token = tokens[prefix_index(stream, token_codes)];
        std::size_t count = token.length;
        if (token.kind == Kind::literal_run) {
            count = (stream.four_bits() + 3U) * 4U;
        }
        if (token.kind == Kind::literal || token.kind == Kind::literal_run) {
            require_room(output.size(), count, unpacked);
            for (std::size_t i = 0; i < count; ++i) {
                output.push_back(stream.raw());
            }
            continue;
        }
        if (token.kind == Kind::extended) {
            count = stream.raw();
            if (count == 0) {
                if (stream.bit() != 0) {
                    continue; // Continuation consumes input even with no output.
                }
                break;
            }
            count += 8;
        }
        const std::size_t high = count == 2 ? 0 : prefix_index(stream, distance_codes);
        const std::size_t distance = (high * 256 + stream.raw()) + 1;
        if (distance > output.size()) {
            throw DecodeError("RNC2 backreference precedes output");
        }
        require_room(output.size(), count, unpacked);
        for (std::size_t i = 0; i < count; ++i) {
            // Read anew each iteration: overlapping matches extend the source.
            const auto value = output[output.size() - distance];
            output.push_back(value);
        }
    }
    if (output.size() != unpacked || stream.consumed() != packed) {
        throw DecodeError("RNC2 termination disagrees with declared extents");
    }
    const auto unpacked_crc = crc16(output);
    if (unpacked_crc != big_endian(block.subspan(12, 2))) {
        throw DecodeError("RNC2 unpacked CRC mismatch");
    }
    return {std::move(output), stream.consumed(), packed_crc, unpacked_crc};
}

} // namespace wiz::rnc2
