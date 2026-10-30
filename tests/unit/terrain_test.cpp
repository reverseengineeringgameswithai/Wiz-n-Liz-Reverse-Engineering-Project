#include "sim/terrain.hpp"

#include <iostream>

namespace {
using namespace wiz;
void check(bool value) { if (!value) throw std::runtime_error("terrain check failed"); }
template<typename F> void rejects(F function) {
    try { function(); } catch (const assets::BankError&) { return; }
    throw std::runtime_error("invalid terrain query accepted");
}
}
int main() {
    try {
        assets::PatternBank bank;
        bank.logical_id = "base";
        bank.patterns.resize(1);
        bank.patterns[0].opaque_record.fill(8);
        assets::SceneResource scene;
        scene.base_bank_id = "base"; scene.columns = 128; scene.rows = 32;
        scene.cells.resize(4096); scene.additional_patterns.resize(1);
        scene.additional_patterns[0].opaque_record = {0,1,2,3,4,5,128,255};
        for (auto& cell : scene.cells) cell.source_word = 1;
        sim::TerrainScratch scratch{5,6};
        auto sample = sim::query_terrain(scene, bank, 128, 127, scratch);
        check(sample.above_map && sample.value == 8 && sample.map_word == 0 && sample.column == 5);
        check(scratch.x == 5 && scratch.y == 6);
        for (unsigned attributes = 0; attributes < 32; ++attributes) {
            scene.cells[0].source_word = static_cast<std::uint16_t>(1 | attributes << 11U);
            for (unsigned column = 0; column < 8; ++column) {
                sample = sim::query_terrain(scene, bank, static_cast<std::uint16_t>(128 + column), 128, scratch);
                const auto selected = (attributes & 1U) ? 7 - column : column;
                check(sample.value == scene.additional_patterns[0].opaque_record[selected]);
                check(sample.column == selected && !sample.above_map);
            }
        }
        scene.cells[0].source_word = 1;
        for (const auto y : {384,1152,0x807f}) {
            scratch = {11,12};
            rejects([&] { sim::query_terrain(scene, bank, 128, static_cast<std::uint16_t>(y), scratch); });
            check(scratch.x == 11 && scratch.y == 12);
        }
        sample = sim::query_terrain(scene, bank, 1153, 2176, scratch);
        check(sample.value == 1 && scratch.x == 1025 && scratch.y == 2048);
        // Match, borrow, signed overflow and unsigned byte values above 127.
        auto contact = sim::probe_contact(scene, bank, {117,105}, sim::ContactProbe::foot, scratch);
        check(contact.equal() && contact.nzvc == 4 && contact.within_tile == 1);
        contact = sim::probe_contact(scene, bank, {118,105}, sim::ContactProbe::foot, scratch);
        check(!contact.equal() && contact.nzvc == 9);
        contact = sim::probe_contact(scene, bank, {122,105}, sim::ContactProbe::foot, scratch);
        check(contact.nzvc == 11 && contact.sample.value == 128);
        contact = sim::probe_contact(scene, bank, {123,105}, sim::ContactProbe::foot, scratch);
        check(contact.nzvc == 1 && contact.sample.value == 255);
        sim::Position position{117,105};
        check(!sim::settle_down(scene, bank, position, scratch).moved && position.y == 105);
        position = {118,105};
        check(sim::settle_down(scene, bank, position, scratch).moved && position.y == 106);
        position = {116,65535}; scratch = {1,0};
        check(sim::settle_down(scene, bank, position, scratch).moved && position.y == 0);
        rejects([&] { sim::probe_contact(scene, bank, position, static_cast<sim::ContactProbe>(99), scratch); });
        scene.cells[0].source_word = 2; scratch = {11,12};
        rejects([&] { sim::query_terrain(scene, bank, 128,128,scratch); });
        check(scratch.x == 11 && scratch.y == 12);
        scene.base_bank_id = "wrong";
        rejects([&] { sim::query_terrain(scene, bank,128,128,scratch); });
        scene.base_bank_id = "base"; scene.rows = 0;
        rejects([&] { sim::query_terrain(scene, bank,128,128,scratch); });
        std::cout << "terrain queries, attributes, scratch, bounds, byte flags and settling passed\n";
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
