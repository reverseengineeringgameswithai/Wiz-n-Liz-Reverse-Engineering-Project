// SPDX-License-Identifier: GPL-3.0-or-later
// Research-only harness linked with pinned ScummVM code; never a game runtime.
// The decoder is unmodified. Mandatory sanitizers trap its unchecked accesses.
#include <algorithm>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <string_view>
#include <sys/resource.h>
#include <unistd.h>

#include "common/endian.h"
#include "common/compression/rnc_deco.h"

#ifndef __has_feature
#define __has_feature(x) 0
#endif
#if !defined(__SANITIZE_ADDRESS__) && !__has_feature(address_sanitizer)
#error This research harness must be built with AddressSanitizer.
#endif

namespace {
constexpr std::size_t kHeaderSize = 18;
constexpr std::size_t kLimit = 4 * 1024 * 1024;

int fail(std::string_view message) {
    // Only fixed literals are passed here, so no JSON escaping is required.
    std::cerr << "{\"status\":\"error\",\"message\":\"" << message << "\"}\n";
    return 2;
}

class ObservedDecoder : public Common::RncDecoder {
public:
    std::ptrdiff_t consumed(const uint8 *begin) const {
        return _srcPtr ? _srcPtr - begin : 0;
    }
    std::ptrdiff_t produced(const uint8 *begin) const {
        return _dstPtr ? _dstPtr - begin : 0;
    }
    uint16 crc(const uint8 *begin, std::size_t size) {
        return crcBlock(begin, static_cast<uint32>(size));
    }
};

int run(int argc, char **argv) {
    if (argc != 2) return fail("usage: rnc-reference INPUT.rnc; stdout is decoded bytes");
    // ASan requires a large virtual reservation: use CPU/alarm, not RLIMIT_AS.
    const rlimit cpu_limit{5, 5};
    if (setrlimit(RLIMIT_CPU, &cpu_limit) != 0) return fail("cannot set CPU limit");
    alarm(10);

    std::ifstream input(argv[1], std::ios::binary | std::ios::ate);
    if (!input) return fail("cannot open input");
    const auto size = input.tellg();
    if (size < static_cast<std::streamoff>(kHeaderSize) ||
        size > static_cast<std::streamoff>(kLimit + kHeaderSize)) {
        return fail("input size outside [18,4194322]");
    }
    const auto input_size = static_cast<std::size_t>(size);
    // Exact new[] sizes permit ASan to detect even a one-byte overrun.
    auto packed = std::make_unique<uint8[]>(input_size);
    input.seekg(0);
    input.read(reinterpret_cast<char *>(packed.get()), size);
    if (!input || input.peek() != std::char_traits<char>::eof()) {
        return fail("input changed or could not be read exactly");
    }
    if (READ_BE_UINT32(packed.get()) != Common::RncDecoder::kRnc2Signature) {
        return fail("only RNC method 2 is supported by this harness");
    }
    const auto output_size = READ_BE_UINT32(packed.get() + 4);
    const auto payload_size = READ_BE_UINT32(packed.get() + 8);
    if (output_size == 0 || output_size > kLimit || payload_size == 0 ||
        payload_size > kLimit || input_size != kHeaderSize + payload_size) {
        return fail("invalid or excessive declared length, or nonexact packed extent");
    }
    auto unpacked = std::make_unique<uint8[]>(output_size);
    std::fill_n(unpacked.get(), output_size, uint8{0xcd});
    ObservedDecoder decoder;
    const auto packed_crc = decoder.crc(packed.get() + kHeaderSize, payload_size);
    if (packed_crc != READ_BE_UINT16(packed.get() + 14)) {
        return fail("packed CRC mismatch");
    }
    const auto result = decoder.unpackM2(packed.get(), unpacked.get());
    const auto consumed_total = decoder.consumed(packed.get());
    const auto produced = decoder.produced(unpacked.get());
    if (result < 0 || result != static_cast<int32>(output_size) ||
        produced != output_size || consumed_total != static_cast<std::ptrdiff_t>(input_size)) {
        std::cerr << "{\"status\":\"decoder_failure\",\"decoder_return\":" << result
                  << ",\"consumed_total_bytes\":" << consumed_total
                  << ",\"produced_bytes\":" << produced << "}\n";
        return 2;
    }
    const auto unpacked_crc = decoder.crc(unpacked.get(), output_size);
    std::cout.write(reinterpret_cast<const char *>(unpacked.get()), output_size);
    std::cout.flush();
    if (!std::cout) return fail("could not write decoded stdout");
    std::cerr << "{\"status\":\"ok\",\"decoder_return\":" << result
              << ",\"consumed_total_bytes\":" << consumed_total
              << ",\"consumed_payload_bytes\":" << consumed_total - kHeaderSize
              << ",\"produced_bytes\":" << produced
              << ",\"packed_crc16\":" << packed_crc
              << ",\"unpacked_crc16\":" << unpacked_crc
              << ",\"address_sanitizer\":true,\"undefined_behavior_sanitizer\":true}\n";
    return 0;
}
} // namespace

int main(int argc, char **argv) {
    try {
        return run(argc, argv);
    } catch (...) {
        return fail("reference harness exception");
    }
}
