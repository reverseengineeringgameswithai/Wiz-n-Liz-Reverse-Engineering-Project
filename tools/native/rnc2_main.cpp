// Headless extraction transport. Binary stdout is published only on success;
// stderr contains machine-readable metadata or a fixed diagnostic.
#include "core/rnc2.hpp"

#include <fstream>
#include <iostream>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "{\"status\":\"error\",\"message\":\"usage: wiznliz-rnc2 exact-block.rnc\"}\n";
        return 2;
    }
    try {
        std::ifstream input(argv[1], std::ios::binary | std::ios::ate);
        const auto extent = input.tellg();
        if (!input || extent < 18 || extent > static_cast<std::streamoff>(wiz::rnc2::Limits{}.packed_bytes + 18)) {
            throw wiz::rnc2::DecodeError("input unavailable or outside size limits");
        }
        std::vector<std::uint8_t> block(static_cast<std::size_t>(extent));
        input.seekg(0);
        if (!input.read(reinterpret_cast<char*>(block.data()), static_cast<std::streamsize>(block.size()))
            || input.peek() != std::char_traits<char>::eof()) {
            throw wiz::rnc2::DecodeError("input changed or could not be read");
        }
        const auto result = wiz::rnc2::decode(block);
        std::cout.write(reinterpret_cast<const char*>(result.bytes.data()),
                        static_cast<std::streamsize>(result.bytes.size()));
        std::cout.flush();
        if (!std::cout) {
            throw wiz::rnc2::DecodeError("failed writing decoded output");
        }
        std::cerr << "{\"status\":\"ok\",\"decoder\":\"wiznliz-rnc2\",\"schema_version\":1"
                  << ",\"consumed_total_bytes\":" << block.size()
                  << ",\"consumed_payload_bytes\":" << result.consumed_payload_bytes
                  << ",\"produced_bytes\":" << result.bytes.size()
                  << ",\"packed_crc16\":" << result.packed_crc16
                  << ",\"unpacked_crc16\":" << result.unpacked_crc16 << "}\n";
        return 0;
    } catch (const wiz::rnc2::DecodeError& error) {
        // All messages are project literals without JSON metacharacters. Never
        // interpolate filenames or untrusted stream text into this document.
        std::cerr << "{\"status\":\"error\",\"message\":\"" << error.what() << "\"}\n";
    } catch (const std::exception&) {
        std::cerr << "{\"status\":\"error\",\"message\":\"resource or I/O failure\"}\n";
    }
    return 2;
}
