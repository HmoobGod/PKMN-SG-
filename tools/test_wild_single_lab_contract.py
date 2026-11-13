#!/usr/bin/env python3
"""Fail-closed SOURCE-FIRST laboratory contract regressions.

These static source tests supplement, but never replace, the GNU ARM build and
real modified-ROM CPU/legality witnesses. They do not authorize a ROM hook.
"""
from pathlib import Path
import unittest

PATCH = Path(__file__).resolve().parents[1] / "source-first" / "wild-single-lab.patch"


def inserted_source(patch: str) -> str:
    lines = patch.splitlines()
    if not lines[0].startswith("--- a/src/battle_controller_player.c"):
        raise ValueError("unexpected source path")
    if not lines[1].startswith("+++ b/src/battle_controller_player.c"):
        raise ValueError("unexpected destination path")
    return "\n".join(line[1:] for line in lines[2:] if line.startswith("+"))


def contract_ok(text: str) -> bool:
    checks = (
        "gBattleTypeFlags != BATTLE_TYPE_IS_MASTER",
        "gBattleOutcome != 0",
        "!gMain.inBattle",
        "gBattlersCount != 2 || battler != 0",
        "gBattlerBattleController[battler] != BATTLE_CONTROLLER_PLAYER",
        "!IsBattleControllerActiveOnLocal(battler)",
        "GetBattlerPosition(battler) != B_POSITION_PLAYER_LEFT",
        "GetBattlerPosition(foe) != B_POSITION_OPPONENT_LEFT",
        "IsBattlerAlly(battler, foe)",
        "gAbsentBattlerFlags",
        "!IsBattlerAlive(battler) || !IsBattlerAlive(foe)",
        "gBattleResources == NULL",
        "verifyReply ? CONTROLLER_CHOOSEMOVE : CONTROLLER_CHOOSEACTION",
        "GetBattlerMoveTargetType(battler, move) != TARGET_SELECTED",
        "!CanTargetBattler(battler, foe, move)",
        "moveInfo->moves[slot] != move",
        "moveInfo->currentPp[slot] != gBattleMons[battler].pp[slot]",
        "bool32 armed = sSourceFirstWildLease.armed",
        "if (!armed || battler != sSourceFirstWildLease.owner ||",
        "GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT) != sSourceFirstWildLease.foe",
        "sSourceFirstWildLease.moves[slot] != gBattleMons[battler].moves[slot]",
        "sSourceFirstWildLease.pp[slot] != gBattleMons[battler].pp[slot]",
        "SourceFirstArmWildLease(battler);",
        "SourceFirstConsumeWildLease(battler) &&",
        "B_ACTION_USE_MOVE, 0",
        "B_ACTION_EXEC_SCRIPT, autoReply",
        "BtlController_Complete(battler);",
    )
    return (all(part in text for part in checks)
            and text.count("sSourceFirstWildLease.armed = FALSE;") == 2
            and text.index("sSourceFirstWildLease.armed = FALSE;") <
                text.index("if (!armed || battler != sSourceFirstWildLease.owner ||")
            and text.index("SourceFirstConsumeWildLease(battler) &&") <
                text.index("SourceFirstWildSingleMove(battler, TRUE, &autoReply)")
            and text.count("CheckMoveLimitations(battler, 0, MOVE_LIMITATIONS_ALL)") == 1
            and "unusable = verifyReply ? CheckMoveLimitations(" in text
            and "*reply = slot | (foe << 8)" in text
            and not any(mark in text for mark in (
                "B_ACTION_USE_ITEM", "B_ACTION_SWITCH", "B_ACTION_RUN",
                "EmitChosenMon", "Master Ball", "gBattleMons[foe].moves",
                "gBattleMons[foe].pp", "Random("
            )))


class WildSingleLabContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = inserted_source(PATCH.read_text(encoding="utf-8"))

    def test_real_source_patch_meets_contract(self):
        self.assertTrue(contract_ok(self.text))

    def test_no_disallowed_controller_writes(self):
        self.assertNotIn("gBattlerBattleController[foe] =", self.text)
        self.assertNotIn("gBattlerControllerFuncs[foe] =", self.text)
        self.assertNotIn("W8(", self.text)

    def test_preflight_does_not_mutate_limitation_cache(self):
        self.assertEqual(self.text.count("CheckMoveLimitations("), 1)
        self.assertIn("unusable = verifyReply ?", self.text)

    def test_actor_ownership_tampering_fails(self):
        self.assertFalse(contract_ok(self.text.replace("battler != 0", "battler != 9")))

    def test_inactive_original_engine_request_is_denied(self):
        self.assertFalse(contract_ok(self.text.replace(
            "!IsBattleControllerActiveOnLocal(battler)",
            "IsBattleControllerActiveOnLocal(battler) == FALSE && 0")))

    def test_terminal_outcome_blocks_auto(self):
        self.assertFalse(contract_ok(self.text.replace(
            "gBattleOutcome != 0", "gBattleOutcome == 0")))

    def test_stale_field_battle_flags_do_not_authorize_auto(self):
        self.assertFalse(contract_ok(self.text.replace(
            "!gMain.inBattle", "gMain.inBattle == FALSE && 0")))

    def test_request_opcode_tampering_fails(self):
        self.assertFalse(contract_ok(self.text.replace("CONTROLLER_CHOOSEMOVE", "CONTROLLER_OPENBAG")))

    def test_target_legality_tampering_fails(self):
        self.assertFalse(contract_ok(self.text.replace("!CanTargetBattler(battler, foe, move)", "TRUE")))

    def test_request_pp_mismatch_tampering_fails(self):
        self.assertFalse(contract_ok(self.text.replace("moveInfo->currentPp[slot] != gBattleMons[battler].pp[slot]", "moveInfo->currentPp[slot] == 0")))

    def test_unconditional_limitation_check_fails(self):
        self.assertFalse(contract_ok(self.text.replace("unusable = verifyReply ? CheckMoveLimitations(", "unusable = CheckMoveLimitations(")))

    def test_missing_single_use_consumption_denied(self):
        self.assertFalse(contract_ok(self.text.replace(
            "sSourceFirstWildLease.armed = FALSE;", "sSourceFirstWildLease.armed = TRUE;", 1)))

    def test_wrong_source_lease_actor_denied(self):
        self.assertFalse(contract_ok(self.text.replace(
            "battler != sSourceFirstWildLease.owner",
            "battler != 255")))

    def test_changed_pp_between_action_and_move_denied(self):
        self.assertFalse(contract_ok(self.text.replace(
            "sSourceFirstWildLease.pp[slot] != gBattleMons[battler].pp[slot]",
            "sSourceFirstWildLease.pp[slot] == gBattleMons[battler].pp[slot]")))

    def test_changed_moves_between_action_and_move_denied(self):
        self.assertFalse(contract_ok(self.text.replace(
            "sSourceFirstWildLease.moves[slot] != gBattleMons[battler].moves[slot]",
            "sSourceFirstWildLease.moves[slot] == gBattleMons[battler].moves[slot]")))

    def test_unrelated_reply_without_fight_lease_denied(self):
        self.assertFalse(contract_ok(self.text.replace(
            "SourceFirstConsumeWildLease(battler) &&",
            "TRUE &&")))

    def test_enemy_auto_path_injection_fails(self):
        self.assertFalse(contract_ok(self.text + "\nB_ACTION_USE_ITEM"))

    def test_patch_does_not_embed_private_game_image(self):
        self.assertNotIn(".gba", self.text)
        self.assertNotIn(".sav", self.text)


if __name__ == "__main__":
    unittest.main()
