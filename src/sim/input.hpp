#pragma once

#include "sim/actor.hpp"

namespace wiz::sim {
// Logical held buttons, independent of device I/O or the original pad bit order.
struct ThreeButtonPad {
    bool up{}, down{}, left{}, right{}, a{}, b{}, c{}, start{};
};
struct PadControl {
    std::uint8_t raw = 0xff, any_action{}, jump{}, drop{};
    std::uint8_t up{}, down{}, left{}, right{}, a{}, b{}, c{}, start{};
    bool operator==(const PadControl&) const = default;
};
// 14E4E..14F24: stateless conversion of the combined active-low byte. Opposing
// directions cancel; pressed fields are FF. No edge detection or I/O emulation.
PadControl convert_pad_byte(std::uint8_t raw) noexcept;
PadControl produce_pad_control(ThreeButtonPad held) noexcept;
ActorInput actor_input(PadControl control, std::uint16_t acceleration_gate) noexcept;
} // namespace wiz::sim
