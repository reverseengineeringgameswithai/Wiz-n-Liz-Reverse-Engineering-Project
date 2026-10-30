// Native resource loading and rasterization. Python may package the emitted
// RGBA raster as PNG, but never supplies pixels or executes original CPU code.
#include "assets/pattern_bank.hpp"

#include <charconv>
#include <fstream>
#include <iostream>
#include <string_view>

int main(int argc, char** argv) {
    using namespace wiz::assets;
    if (argc != 4) {
        std::cerr << "{\"status\":\"error\",\"message\":\"usage: wiznliz-bank-atlas logical-id bank.bin columns\"}\n";
        return 2;
    }
    try {
        const std::string_view column_text(argv[3]);
        std::size_t columns{};
        const auto number = std::from_chars(column_text.data(), column_text.data() + column_text.size(), columns);
        if (number.ec != std::errc{} || number.ptr != column_text.data() + column_text.size())
            throw BankError("invalid atlas columns");
        std::ifstream input(argv[2], std::ios::binary | std::ios::ate);
        const auto extent = input.tellg();
        if (!input || extent < 34 || extent > static_cast<std::streamoff>(max_bank_v1_bytes))
            throw BankError("input unavailable or outside bank size limits");
        std::vector<std::uint8_t> bytes(static_cast<std::size_t>(extent));
        input.seekg(0);
        if (!input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()))
            || input.peek() != std::char_traits<char>::eof())
            throw BankError("input changed or could not be read");
        const auto bank = parse_pattern_bank(argv[1], bytes);
        const auto atlas = make_atlas(bank, columns);
        const auto pam = encode_pam(atlas);
        std::cout.write(reinterpret_cast<const char*>(pam.data()), static_cast<std::streamsize>(pam.size()));
        std::cout.flush();
        if (!std::cout) throw BankError("failed writing atlas");
        // ID has been validated to a restricted ASCII alphabet by the parser.
        std::cerr << "{\"status\":\"ok\",\"schema_version\":1,\"renderer\":\"wiznliz-bank-atlas\""
                  << ",\"logical_id\":\"" << bank.logical_id << "\",\"patterns\":" << bank.patterns.size()
                  << ",\"width\":" << atlas.width << ",\"height\":" << atlas.height
                  << ",\"columns\":" << columns << ",\"input_bytes\":" << bytes.size()
                  << ",\"palette_policy\":\"normal-rgb3-rounded-v1\",\"transparent_index\":0}\n";
        return 0;
    } catch (const BankError& error) {
        std::cerr << "{\"status\":\"error\",\"message\":\"" << error.what() << "\"}\n";
    } catch (const std::exception&) {
        std::cerr << "{\"status\":\"error\",\"message\":\"resource or I/O failure\"}\n";
    }
    return 2;
}
