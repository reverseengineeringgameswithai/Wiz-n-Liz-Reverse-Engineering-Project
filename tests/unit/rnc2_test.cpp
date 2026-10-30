#include "core/rnc2.hpp"

#include <array>
#include <iostream>
#include <stdexcept>

namespace {
void require(bool condition) {
    if (!condition) {
        throw std::runtime_error("unit check failed");
    }
}
template <typename F> void rejects(F operation) {
    try {
        operation();
    } catch (const wiz::rnc2::DecodeError&) {
        return;
    }
    throw std::runtime_error("malformed input was accepted");
}
} // namespace

int main() {
    try {
        const std::array<std::uint8_t, 21> literal{
            0x52,0x4e,0x43,0x02,0,0,0,1,0,0,0,3,0x30,0xc0,0x56,0x50,0,1,0x1e,0x41,0
        };
        const std::array<std::uint8_t, 9> crc_vector{'1','2','3','4','5','6','7','8','9'};
        require(wiz::rnc2::crc16(crc_vector) == 0xBB3D);
        require(wiz::rnc2::crc16({}) == 0);
        const auto result = wiz::rnc2::decode(literal, {3, 1});
        require(result.bytes == std::vector<std::uint8_t>{'A'});
        require(result.consumed_payload_bytes == 3);
        require(result.packed_crc16 == 0x5650 && result.unpacked_crc16 == 0x30C0);
        rejects([&] { wiz::rnc2::decode(literal, {2, 1}); });
        rejects([&] { wiz::rnc2::decode(literal, {3, 0}); });
        rejects([] { wiz::rnc2::decode({}); });

        // Deterministic malformed-stream stress: valid container and packed CRC
        // force random bit/raw sequences through stream/output guards. This is a
        // safety check, not independent semantic or coverage proof.
        std::uint32_t rng = 0x524E4302U;
        auto random = [&] {
            rng ^= rng << 13U;
            rng ^= rng >> 17U;
            rng ^= rng << 5U;
            return rng;
        };
        std::size_t rejected = 0;
        for (unsigned iteration = 0; iteration < 10000; ++iteration) {
            const std::size_t payload_size = 2 + random() % 254;
            std::vector<std::uint8_t> input(literal.begin(), literal.begin() + 18);
            input.resize(18 + payload_size);
            input[7] = static_cast<std::uint8_t>(1 + random() % 255);
            input[11] = static_cast<std::uint8_t>(payload_size);
            for (std::size_t i = 18; i < input.size(); ++i) {
                input[i] = static_cast<std::uint8_t>(random());
            }
            const auto crc = wiz::rnc2::crc16(std::span(input).subspan(18));
            input[14] = static_cast<std::uint8_t>(crc >> 8U);
            input[15] = static_cast<std::uint8_t>(crc);
            try {
                const auto decoded = wiz::rnc2::decode(input, {256, 256});
                require(decoded.bytes.size() == input[7]);
                require(decoded.consumed_payload_bytes == payload_size);
            } catch (const wiz::rnc2::DecodeError&) {
                ++rejected;
            }
        }
        require(rejected > 0);
        std::cout << "API/CRC/limits passed; 10000 seeded malformed streams completed, "
                  << rejected << " rejected\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
