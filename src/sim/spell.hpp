#pragma once
#include "sim/collision_probe.hpp"
#include "sim/trail.hpp"
#include <array>
#include <optional>

namespace wiz::sim {
// 7E18's recipe table at 83DA: unordered fruit-index pairs, FF-terminated, each
// naming its effect routine. Only 8652 (fruits 6 and 5) is reconstructed; the
// other effects are named for rejection.
struct Recipe { std::uint8_t first, second; std::uint32_t effect; };
extern const std::array<Recipe,105> recipes;
// The first entry naming {a, b} in either order (the word compares at 7E90 and
// 7EC8); none means 7ED2's branch to 9288.
std::optional<std::uint32_t> recipe_effect(std::uint16_t a, std::uint16_t b) noexcept;
// 7E28: an ingredient's fruit index from its +08 frame, (+08 - 0260) / 6 with
// DIVU.W on the zero-extended word (the quotient word is kept).
std::uint16_t ingredient_fruit(std::uint16_t frame) noexcept;

// Objects F9E2 allocates leave +08..+0E as the previous occupant left them; a
// mode-80 object never animates, so those bytes are never read and are held as
// zero here.

// 7F08/7F6A: the spell's sparkle source. F9E2 defaults, mode 80, frame 021D,
// (x, y + 4), extents 0010/0010 and +10 = 0040; 7F08 also requests sound 90.
struct SpellSparkle {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{}, x_extent{}, y_extent{};
};
SpellSparkle make_spell_sparkle(Position position) noexcept;
struct SparkleStep { bool released{}; std::optional<TrailParticle> particle; };
// One walk: active gate, presentation (a callback rejects), then handler 7F6A:
// +10 - 1; a negative result releases (JMP FAA4: mode 0). Otherwise E918; when
// its low byte is at most 73, two more E918 calls give Y then X offsets
// ((r & 1F) - 10), 5A9A allocates a particle there and a fourth E918 with bit 0
// set gives the particle flags 4000. Exhausted allocation rejects with no change.
SparkleStep step_spell_sparkle(SpellSparkle& sparkle, TrailRandom& random, bool allocation_available);

// 6F02's lower object, later the sign above the door: F9E2 defaults at (0,0)
// with RTS handlers until 4C08 gives it (x, y - 24), frame 00D2 (7052 replaces
// 4C08's +3A frame) and handler 4C34, which adds the 4C52 table word at the
// cursor to Y each walk (fourteen words, wrapping).
struct DoorSign {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{};
    std::size_t cursor{};
    bool bobbing{};
};
DoorSign make_door_sign() noexcept;
void raise_door_sign(DoorSign& sign, Position door) noexcept;
// Active gate, presentation (a callback rejects), then 4C34 once raised.
void step_door_sign(DoorSign& sign);

// 6F02's higher object, the exit door: mode 80 at (x - 8, y + 24), frame 021D,
// +10 = 001E, the control at +4A and the sign at +36. 6FB6 counts +10 down; a
// negative result runs 5964 (mode 87, frames 0227..021E, target 021E,
// cadence 3, flags & 9FFF) with callback 6FCA. 6FCA, when that presentation
// reaches its target, requests sound 95, moves it (+8, -8), sets frames
// 00B0/00A8/00B7, cadence 3, extents 0010/0020, mode 81 and service 705C.
enum class DoorPhase : std::uint8_t { waiting, appearing, open };
struct ExitDoor {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{}, x_extent{}, y_extent{};
    ActorId control;
    EffectId sign;
    DoorPhase phase = DoorPhase::waiting;
};
ExitDoor make_exit_door(Position position, ActorId control, EffectId sign) noexcept;
// One walk: active gate, presentation (6FCA when appearing; any other callback
// rejects), handler (6FB6 while waiting), then 705C once open: AC5E against the
// primary control's tracking; the two-player test rejects with no change.
// `dressed`: 6FCA ran (the caller runs 4C08 on the sign at the door's new
// position). `entered`: the primary control touched the open door (possibly
// just dressed); the door is left as walked and the caller runs 7082.
struct DoorStep { bool dressed{}, entered{}; };
DoorStep step_exit_door(ExitDoor& door, const CollisionInputs* inputs, bool two_player);
// 7082's 4CA2 on the door after its +3A sign is released: 59BC's vanish (mode
// 85, frames 021E/021E/0227, target 0227, cadence 3, flags & 9FFF, RTS
// handlers, FAA4 callback), then X - 8 and Y + 8. The result has 5A9A's shape.
TrailParticle vanish_exit_door(const ExitDoor& door) noexcept;
} // namespace wiz::sim
