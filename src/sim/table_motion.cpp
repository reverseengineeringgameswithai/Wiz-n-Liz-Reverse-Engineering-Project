#include "sim/table_motion.hpp"
#include "sim/presentation.hpp"

namespace wiz::sim {
void step_table_motion(TableMotion& object, std::uint16_t loop_count, bool scheduled, std::size_t budget) {
    if (scheduled && !(object.presentation.mode & 0x80U)) return;
    auto next = object;
    if (scheduled && advance_presentation(next.presentation,next.target))
        throw assets::BankError("unsupported table motion callback79B6");
    const auto iterations = static_cast<std::size_t>(loop_count) + 1U;
    if (iterations > budget) throw assets::BankError("table motion loop budget exhausted");
    constexpr std::array<int,24> vertical{1,0,1,0,2,0,1,0,1,0,0,0,-1,0,-1,0,-2,0,-1,0,-1,0,0,0};
    for (std::size_t i=0; i<iterations; ++i) {
        next.toggle ^= 1U;
        if (!next.toggle) continue;
        if (next.cursor >= vertical.size()) throw assets::BankError("unsupported table motion cursor");
        next.position.y = static_cast<std::uint16_t>(next.position.y + vertical[next.cursor]);
        if (++next.cursor == vertical.size()) next.cursor = 0;
        next.position.x = static_cast<std::uint16_t>(next.position.x + next.delta_x);
        next.countdown = static_cast<std::uint16_t>(next.countdown - 1U);
        if (next.countdown & 0x8000U) {
            next.delta_x = static_cast<std::uint16_t>(0U - next.delta_x);
            next.countdown = 28;
        }
    }
    object = next;
}
} // namespace wiz::sim
