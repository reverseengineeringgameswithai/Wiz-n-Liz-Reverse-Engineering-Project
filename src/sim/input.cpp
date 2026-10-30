#include "sim/input.hpp"

namespace wiz::sim {
namespace {
std::uint8_t field(bool pressed) noexcept { return pressed ? 0xff : 0; }
}
PadControl convert_pad_byte(std::uint8_t raw) noexcept {
    const auto held = static_cast<std::uint8_t>(raw ^ 0xffU);
    PadControl c;
    c.raw = raw;
    c.up = field((held & 3U) == 1);
    c.down = field((held & 3U) == 2);
    c.left = field((held & 12U) == 4);
    c.right = field((held & 12U) == 8);
    c.a = field((held & 64U) != 0);
    c.b = field((held & 16U) != 0);
    c.c = field((held & 32U) != 0);
    c.start = field((held & 128U) != 0);
    c.drop = c.a;
    c.jump = static_cast<std::uint8_t>(c.b | c.c);
    c.any_action = static_cast<std::uint8_t>(c.a | c.jump);
    return c;
}
PadControl produce_pad_control(ThreeButtonPad p) noexcept {
    const unsigned held = (p.up ? 1U : 0U) | (p.down ? 2U : 0U) |
        (p.left ? 4U : 0U) | (p.right ? 8U : 0U) | (p.a ? 64U : 0U) |
        (p.b ? 16U : 0U) | (p.c ? 32U : 0U) | (p.start ? 128U : 0U);
    return convert_pad_byte(static_cast<std::uint8_t>(held ^ 0xffU));
}
ActorInput actor_input(PadControl c, std::uint16_t gate) noexcept {
    return {c.jump,c.drop,c.up,c.down,c.left,c.right,gate,c.raw,c.start};
}
} // namespace wiz::sim
