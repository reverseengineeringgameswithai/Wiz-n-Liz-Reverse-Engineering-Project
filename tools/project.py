#!/usr/bin/env python3
"""Stable project entry point; unfinished interfaces fail explicitly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import unittest

from rom import DEFAULT_ROM, ROOT, RomError, inspect_file, verify_expected

IMPLEMENTED = ("game-session", "hub-compare", "hub-session", "completion-compare", "spell-compare", "world-session", "pair-initializer-capture", "pair-initializer-compare", "pickup-hit-compare", "delivery-compare", "ingredient-compare", "return-only-compare", "collision-compare", "table-motion-compare", "private-compare", "mixed-session-probe", "mixed-session", "trail-compare", "trail-capture", "effect-session-probe", "effect-session", "session-compare", "banner-compare", "input-compare", "session-capture", "doctor", "rom-identify", "split", "reset-probe", "rnc-loader-probe", "scene-probe", "scene-preview", "terrain-probe", "terrain-compare", "movement-probe", "movement-compare", "airborne-probe", "airborne-compare", "genesis-compare", "actor-probe", "actor-compare", "actor-capture", "presentation-probe", "presentation-compare", "movie-actor-capture", "reversal-probe", "reversal-compare", "reversal-capture", "actions-probe", "actions-compare", "actions-capture", "dispatch-probe", "dispatch-compare", "dispatch-capture", "transition-probe", "transition-compare", "transition-capture", "tally-probe", "tally-compare", "tally-capture", "palette-probe", "palette-compare", "palette-capture", "bonus-probe", "bonus-compare", "bonus-capture", "score-probe", "score-compare", "score-capture", "exit-tally-probe", "exit-tally-compare", "exit-tally-capture", "coasting-probe", "coasting-compare", "coasting-capture", "rnc-validate", "bank-atlas", "configure", "build", "reference-test", "test", "check-vault", "check-hygiene")
PLANNED = ("extract", "run")


def emit(report):
    print(json.dumps(report, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=IMPLEMENTED + PLANNED)
    args, remaining = parser.parse_known_args(argv)
    try:
        if args.command in PLANNED:
            print(f"{args.command}: not implemented; see vault/01_Project/NEXT_ACTIONS.md", file=sys.stderr)
            return 2
        if args.command == "game-session":
            import genesis_game_session
            return genesis_game_session.main(remaining)
        if args.command == "hub-compare":
            import hub_compare
            return hub_compare.main(remaining)
        if args.command == "hub-session":
            import genesis_hub_session
            return genesis_hub_session.main(remaining)
        if args.command == "completion-compare":
            import completion_compare
            return completion_compare.main(remaining)
        if args.command == "spell-compare":
            import spell_compare
            return spell_compare.main(remaining)
        if args.command == "world-session":
            from genesis_world_session import main as world_session_main
            return world_session_main(remaining)
        if args.command == "pair-initializer-capture":
            from genesis_pair_initializer import main as pair_capture_main
            return pair_capture_main(remaining)
        if args.command == "pair-initializer-compare":
            import pair_initializer_compare
            return pair_initializer_compare.main(remaining)
        if args.command == "pickup-hit-compare":
            import pickup_hit_compare
            return pickup_hit_compare.main(remaining)
        if args.command == "delivery-compare":
            import delivery_compare
            return delivery_compare.main(remaining)
        if args.command == "ingredient-compare":
            import ingredient_compare
            return ingredient_compare.main(remaining)
        if args.command == "return-only-compare":
            import return_only_compare
            return return_only_compare.main(remaining)
        if args.command == "collision-compare":
            import collision_compare
            return collision_compare.main(remaining)
        if args.command == "table-motion-compare":
            import table_motion_compare
            return table_motion_compare.main(remaining)
        if args.command == "private-compare":
            import private_compare
            return private_compare.main(remaining)
        if args.command == "mixed-session-probe":
            from mixed_session_probe import main as mixed_probe_main
            return mixed_probe_main(remaining)
        if args.command == "mixed-session":
            from genesis_mixed_session import main as mixed_main
            return mixed_main(remaining)
        if args.command == "trail-compare":
            from trail_compare import main as trail_compare_main
            return trail_compare_main(remaining)
        if args.command == "trail-capture":
            from genesis_trail_capture import main as trail_capture_main
            return trail_capture_main(remaining)
        if args.command == "effect-session-probe":
            from effect_session_probe import main as effect_probe_main
            return effect_probe_main(remaining)
        if args.command == "effect-session":
            from genesis_effect_session import main as effect_session_main
            return effect_session_main(remaining)
        if args.command == "banner-compare":
            from banner_compare import main as banner_main
            return banner_main(remaining)
        if args.command == "input-compare":
            from input_compare import main as input_main
            return input_main(remaining)
        if args.command == "session-compare":
            from genesis_session_compare import main as session_compare_main
            return session_compare_main(remaining)
        if args.command == "session-capture":
            from genesis_session_capture import main as session_main
            return session_main(remaining)
        if args.command == "doctor":
            from doctor import main as doctor_main
            return doctor_main(remaining)
        if args.command == "split":
            from sega2asm import main as split_main
            return split_main(remaining)
        if args.command == "reset-probe":
            from reset_probe import main as reset_main
            return reset_main(remaining)
        if args.command == "rnc-loader-probe":
            from rnc_loader_probe import main as loader_main
            return loader_main(remaining)
        if args.command == "rnc-validate":
            from rnc_validate import main as rnc_main
            return rnc_main(remaining)
        if args.command == "bank-atlas":
            from bank_atlas import main as atlas_main
            return atlas_main(remaining)
        if args.command == "scene-probe":
            from scene_probe import main as scene_probe_main
            return scene_probe_main(remaining)
        if args.command == "scene-preview":
            from scene_preview import main as preview_main
            return preview_main(remaining)
        if args.command == "terrain-probe":
            from terrain_probe import main as terrain_probe_main
            return terrain_probe_main(remaining)
        if args.command == "terrain-compare":
            from terrain_compare import main as terrain_compare_main
            return terrain_compare_main(remaining)
        if args.command == "movement-probe":
            from movement_probe import main as movement_probe_main
            return movement_probe_main(remaining)
        if args.command == "movement-compare":
            from movement_compare import main as movement_compare_main
            return movement_compare_main(remaining)
        if args.command == "actor-capture":
            from genesis_actor_capture import main as actor_capture_main
            return actor_capture_main(remaining)
        if args.command == "presentation-probe":
            from presentation_probe import main as presentation_probe_main
            return presentation_probe_main(remaining)
        if args.command == "presentation-compare":
            from presentation_compare import main as presentation_compare_main
            return presentation_compare_main(remaining)
        if args.command == "movie-actor-capture":
            from genesis_movie_actor_capture import main as movie_actor_capture_main
            return movie_actor_capture_main(remaining)
        if args.command == "score-probe":
            from score_probe import main as score_main
            return score_main(remaining)
        if args.command == "score-compare":
            from score_compare import main as score_main
            return score_main(remaining)
        if args.command == "score-capture":
            from genesis_score_capture import main as score_main
            return score_main(remaining)
        if args.command == "exit-tally-probe":
            from exit_tally_probe import main as exit_main
            return exit_main(remaining)
        if args.command == "exit-tally-compare":
            from exit_tally_compare import main as exit_main
            return exit_main(remaining)
        if args.command == "exit-tally-capture":
            from genesis_exit_tally_capture import main as exit_main
            return exit_main(remaining)
        if args.command == "bonus-probe":
            from bonus_probe import main as bonus_main
            return bonus_main(remaining)
        if args.command == "bonus-compare":
            from bonus_compare import main as bonus_main
            return bonus_main(remaining)
        if args.command == "bonus-capture":
            from genesis_bonus_capture import main as bonus_main
            return bonus_main(remaining)
        if args.command == "palette-probe":
            from palette_probe import main as palette_main
            return palette_main(remaining)
        if args.command == "palette-compare":
            from palette_compare import main as palette_main
            return palette_main(remaining)
        if args.command == "palette-capture":
            from genesis_palette_capture import main as palette_main
            return palette_main(remaining)
        if args.command == "tally-probe":
            from tally_probe import main as tally_main
            return tally_main(remaining)
        if args.command == "tally-compare":
            from tally_compare import main as tally_main
            return tally_main(remaining)
        if args.command == "tally-capture":
            from genesis_tally_capture import main as tally_main
            return tally_main(remaining)
        if args.command == "coasting-probe":
            from coasting_probe import main as coasting_main
            return coasting_main(remaining)
        if args.command == "coasting-compare":
            from coasting_compare import main as coasting_main
            return coasting_main(remaining)
        if args.command == "coasting-capture":
            from genesis_coasting_capture import main as coasting_main
            return coasting_main(remaining)
        if args.command == "transition-probe":
            from transition_probe import main as transition_main
            return transition_main(remaining)
        if args.command == "transition-compare":
            from transition_compare import main as transition_main
            return transition_main(remaining)
        if args.command == "transition-capture":
            from genesis_transition_capture import main as transition_main
            return transition_main(remaining)
        if args.command == "dispatch-probe":
            from dispatch_probe import main as dispatch_main
            return dispatch_main(remaining)
        if args.command == "dispatch-compare":
            from dispatch_compare import main as dispatch_main
            return dispatch_main(remaining)
        if args.command == "dispatch-capture":
            from genesis_dispatch_capture import main as dispatch_main
            return dispatch_main(remaining)
        if args.command == "actions-probe":
            from actions_probe import main as actions_probe_main
            return actions_probe_main(remaining)
        if args.command == "actions-compare":
            from actions_compare import main as actions_compare_main
            return actions_compare_main(remaining)
        if args.command == "actions-capture":
            from genesis_actions_capture import main as actions_capture_main
            return actions_capture_main(remaining)
        if args.command == "reversal-probe":
            from reversal_probe import main as reversal_probe_main
            return reversal_probe_main(remaining)
        if args.command == "reversal-compare":
            from reversal_compare import main as reversal_compare_main
            return reversal_compare_main(remaining)
        if args.command == "reversal-capture":
            from genesis_reversal_capture import main as reversal_capture_main
            return reversal_capture_main(remaining)
        if args.command == "actor-probe":
            from actor_probe import main as actor_probe_main
            return actor_probe_main(remaining)
        if args.command == "actor-compare":
            from actor_compare import main as actor_compare_main
            return actor_compare_main(remaining)
        if args.command == "airborne-probe":
            from airborne_probe import main as airborne_probe_main
            return airborne_probe_main(remaining)
        if args.command == "airborne-compare":
            from airborne_compare import main as airborne_compare_main
            return airborne_compare_main(remaining)
        if args.command == "genesis-compare":
            from genesis_reference import main as genesis_main
            return genesis_main(remaining)
        if args.command in ("configure", "build"):
            from native_build import main as native_main
            return native_main(args.command, remaining)
        if args.command == "reference-test":
            from rnc_compare import main as compare_main
            return compare_main(remaining)
        sub = argparse.ArgumentParser(prog=f"{parser.prog} {args.command}")
        if args.command == "rom-identify":
            sub.add_argument("--rom", type=Path, default=DEFAULT_ROM)
            sub.add_argument("--verify", action="store_true", help="Require the recorded local ROM identity")
            options = sub.parse_args(remaining)
            report = inspect_file(options.rom)
            if options.verify:
                verify_expected(report)
            emit(report)
            return 0
        if args.command == "test":
            sub.add_argument("--rom", action="store_true", help="Also verify the local proprietary input; missing is failure")
            sub.add_argument("--preset", choices=("debug", "release", "sanitize"), help="Also run required headless native CTest tests in this existing build")
            options = sub.parse_args(remaining)
            suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
            if not suite.countTestCases():
                raise ValueError("no tests discovered")
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            if not result.wasSuccessful():
                return 1
            if options.rom:
                before = inspect_file()
                verify_expected(before)
                after = inspect_file()
                verify_expected(after)
                print(f"Local ROM identity PASS: {after['sha256']}")
            else:
                print("Local ROM-dependent validation: not requested (synthetic tests only).")
            if options.preset:
                from native_build import run
                return run("test", options.preset)
            print("Native CTest tests: not requested (use --preset debug/release/sanitize).")
            return 0
        sub.parse_args(remaining)
        if args.command == "check-vault":
            from check_vault import check_vault
            report = check_vault()
        else:
            from hygiene import check_hygiene
            report = check_hygiene()
        emit(report)
        return int(not report["ok"])
    except (OSError, ValueError, ImportError, subprocess.SubprocessError) as exc:
        print(f"{args.command}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
