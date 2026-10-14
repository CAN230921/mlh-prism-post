import copy
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from copilot_core import Choice, Game, Node, State, run_cli
from story import ENDINGS, FLAG_LABELS, NODES

ROUTES = {
    "home": "1 1 1 2 1 1 1 1 1 1 1 1 1".split(),
    "voices": "1 1 1 2 1 1 1 1 1 1 1 2 2".split(),
    "lone": "1 1 1 2 1 1 1 1 1 1 1 1 3".split(),
    "reunion": "1 1 1 2 1 1 1 2 1 2 1 3 4".split(),
    "darkness": "1 1 1 2 1 1 1 1 1 1 1 1 5".split(),
}


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(NODES)

    def test_invalid_choice_keeps_state(self):
        before = copy.deepcopy(self.game.state)
        self.assertFalse(self.game.choose("not-a-choice")[0])
        self.assertEqual(self.game.state, before)

    def test_missing_flag_keeps_state(self):
        self.game.state.node = "transit"
        before = copy.deepcopy(self.game.state)
        self.assertNotIn("1", {c.key for c in self.game.available()})
        self.assertFalse(self.game.choose("1")[0])
        self.assertEqual(self.game.state, before)

    def test_insufficient_resources_keeps_state(self):
        self.game.state.node = "antenna"
        self.game.state.power = 0
        before = copy.deepcopy(self.game.state)
        self.assertFalse(self.game.choose("1")[0])
        self.assertEqual(self.game.state, before)

    def test_exact_cost_is_payable_and_not_negative(self):
        self.game.state.node = "antenna"
        self.game.state.power = 1
        self.game.state.time = 1
        self.assertTrue(self.game.choose("1")[0])
        self.assertEqual(self.game.state.power, 0)
        self.assertEqual(self.game.state.time, 0)
        self.assertIn("map", self.game.state.flags)

    def test_invalid_target_rejected_before_payment(self):
        g = Game({"start": Node("测试", "", [Choice("1", "坏链接", "missing", {"power": 1})])})
        before = copy.deepcopy(g.state)
        self.assertEqual(g.available(), [])
        self.assertFalse(g.choose("1")[0])
        self.assertEqual(g.state, before)

    def test_negative_cost_is_rejected(self):
        g = Game({"start": Node("测试", "", [Choice("1", "坏成本", "start", {"power": -1})])})
        before = copy.deepcopy(g.state)
        self.assertEqual(g.available(), [])
        self.assertFalse(g.choose("1")[0])
        self.assertEqual(g.state, before)

    def test_no_op_self_loop_not_presented(self):
        g = Game({"start": Node("测试", "", [Choice("1", "空循环", "start")])})
        self.assertEqual(g.available(), [])
        self.assertFalse(g.choose("1")[0])

    def test_restart_resets_resources_flags_and_progress(self):
        self.game.choose("1")
        self.game.choose("1")
        self.game.reset()
        self.assertEqual(self.game.state, State())
        self.assertTrue(self.game.choose("1")[0])

    def test_separate_games_do_not_share_flags(self):
        other = Game(NODES)
        self.game.state.flags.add("seed")
        self.assertEqual(other.state.flags, set())

    def test_end_state_cannot_be_changed(self):
        for key in ROUTES["darkness"]:
            self.assertTrue(self.game.choose(key)[0])
        before = copy.deepcopy(self.game.state)
        self.assertEqual(self.game.available(), [])
        self.assertFalse(self.game.choose("5")[0])
        self.assertEqual(self.game.state, before)


class StoryTests(unittest.TestCase):
    def test_all_five_ending_routes(self):
        for ending, route in ROUTES.items():
            with self.subTest(ending=ending):
                g = Game(NODES)
                for key in route:
                    self.assertTrue(g.choose(key)[0], (g.state.node, key))
                self.assertEqual(g.state.ending, ending)

    def test_story_links_costs_flags_and_keys_are_valid(self):
        for node in NODES.values():
            self.assertEqual(len(node.choices), len({c.key for c in node.choices}))
            self.assertTrue(node.title and node.text)
            for c in node.choices:
                self.assertTrue(c.target in NODES or c.ending in ENDINGS)
                self.assertTrue(c.ending is None or c.ending in ENDINGS)
                self.assertTrue(set(c.costs) <= {"oxygen", "power", "time"})
                self.assertTrue(all(isinstance(v, int) and v >= 0 for v in c.costs.values()))
                self.assertTrue(c.give_flags <= FLAG_LABELS.keys())
                self.assertTrue(c.require_flags <= FLAG_LABELS.keys())

    def test_every_reachable_state_can_finish_and_preserves_resources(self):
        # 穷举真实状态，合并完全相同的状态，验证每个可选动作和所有资源组合。
        seen = set()
        found_endings = set()
        visited_nodes = set()
        stack = [Game(NODES)]
        while stack:
            g = stack.pop()
            s = g.state
            signature = (s.node, s.oxygen, s.power, s.time, tuple(sorted(s.flags)), s.ending)
            if signature in seen:
                continue
            seen.add(signature)
            visited_nodes.add(s.node)
            self.assertGreaterEqual(min(s.oxygen, s.power, s.time), 0)
            if s.ending:
                found_endings.add(s.ending)
                continue
            self.assertTrue(g.available(), f"无路可走：{signature}")
            for c in g.available():
                child = copy.deepcopy(g)
                self.assertTrue(child.choose(c.key)[0])
                stack.append(child)
        self.assertEqual(found_endings, set(ENDINGS))
        self.assertEqual(visited_nodes, set(NODES))
        self.assertEqual(len(seen), 25605)


class CLITests(unittest.TestCase):
    def play(self, inputs):
        return subprocess.run([sys.executable, str(ROOT / "game.py")],
                              input="\n".join(inputs) + "\n", text=True,
                              capture_output=True, timeout=10, cwd=ROOT)

    def test_actual_cli_reaches_all_five_endings(self):
        for ending, route in ROUTES.items():
            with self.subTest(ending=ending):
                p = self.play(route + ["quit"])
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertIn(ENDINGS[ending].splitlines()[0], p.stdout)
                self.assertIn("已发现结局：1/5", p.stdout)
                self.assertNotIn("没有可用选项", p.stdout)

    def test_help_status_invalid_input_and_quit(self):
        p = self.play(["help", "status", "99", "", "quit"])
        self.assertEqual(p.returncode, 0)
        self.assertIn("时间是行动余量", p.stdout)
        self.assertIn("氧气=12 电力=10 时间=14", p.stdout)
        self.assertIn("无效选择", p.stdout)

    def test_restart_during_play(self):
        p = self.play(["1", "restart", "status", "quit"])
        self.assertIn("游戏已重置", p.stdout)
        self.assertIn("氧气=12 电力=10 时间=14", p.stdout)

    def test_replay_tracks_two_endings(self):
        p = self.play(ROUTES["home"] + ["replay"] + ROUTES["reunion"] + ["quit"])
        self.assertEqual(p.returncode, 0)
        self.assertIn("【归航的人】", p.stdout)
        self.assertIn("【下一座邮局】", p.stdout)
        self.assertIn("已发现结局：2/5", p.stdout)

    def test_end_menu_invalid_input_then_quit(self):
        p = self.play(ROUTES["darkness"] + ["bad", "quit"])
        self.assertIn("请输入 'replay' 或 'quit'", p.stdout)

    def test_eof_exits_without_traceback(self):
        p = subprocess.run([sys.executable, str(ROOT / "game.py")], input="",
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(p.returncode, 0)
        self.assertIn("已退出", p.stdout)
        self.assertEqual(p.stderr, "")

    def test_ctrl_c_exits_cleanly(self):
        out = io.StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt), patch("sys.stdout", out):
            run_cli(NODES, ENDINGS, FLAG_LABELS)
        self.assertIn("已退出", out.getvalue())


if __name__ == "__main__":
    unittest.main()
