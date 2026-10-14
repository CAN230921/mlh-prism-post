from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional
import copy
import sys

@dataclass
class State:
    oxygen: int = 12
    power: int = 10
    time: int = 14
    flags: Set[str] = field(default_factory=set)
    node: str = "start"
    ending: Optional[str] = None

@dataclass
class Choice:
    key: str
    label: str
    target: str
    costs: Dict[str, int] = field(default_factory=dict)  # keys: 'oxygen','power','time'
    require_flags: Set[str] = field(default_factory=set)
    give_flags: Set[str] = field(default_factory=set)
    ending: Optional[str] = None

@dataclass
class Node:
    title: str
    text: str
    choices: List[Choice] = field(default_factory=list)

class Game:
    def __init__(self, nodes: Dict[str, Node], initial: Optional[State] = None):
        self.nodes = nodes
        self._initial_state = copy.deepcopy(initial) if initial is not None else State()
        self.state = copy.deepcopy(self._initial_state)

    def reset(self):
        self.state = copy.deepcopy(self._initial_state)

    def _get_node(self) -> Node:
        if self.state.node not in self.nodes:
            raise KeyError(f"当前节点 '{self.state.node}' 不存在。")
        return self.nodes[self.state.node]

    def available(self) -> List[Choice]:
        node = self._get_node()
        avail = []
        for c in node.choices:
            # 前置旗标
            if not c.require_flags.issubset(self.state.flags):
                continue
            # 成本是否可付
            cost_o = c.costs.get("oxygen", 0)
            cost_p = c.costs.get("power", 0)
            cost_t = c.costs.get("time", 0)
            if cost_o < 0 or cost_p < 0 or cost_t < 0:
                continue  # 不接受负成本定义
            if (self.state.oxygen - cost_o) < 0:
                continue
            if (self.state.power - cost_p) < 0:
                continue
            if (self.state.time - cost_t) < 0:
                continue
            avail.append(c)
        # 按 key 排序以稳定展示
        avail.sort(key=lambda x: x.key)
        return avail

    def choose(self, key: str) -> (bool, str):
        try:
            node = self._get_node()
        except KeyError as e:
            return False, str(e)
        choice = None
        for c in node.choices:
            if c.key == key:
                choice = c
                break
        if choice is None:
            return False, "无效选择：该选项不存在。"

        # 验证前置与资源
        if not choice.require_flags.issubset(self.state.flags):
            return False, "无效选择：前置条件不满足。"
        cost_o = choice.costs.get("oxygen", 0)
        cost_p = choice.costs.get("power", 0)
        cost_t = choice.costs.get("time", 0)
        if cost_o < 0 or cost_p < 0 or cost_t < 0:
            return False, "选项定义错误：成本不能为负数。"
        if self.state.oxygen < cost_o or self.state.power < cost_p or self.state.time < cost_t:
            return False, "资源不足，不能执行该选择。"

        # 防止无副作用的自循环导致死循环：如果目标是当前节点且不会改变资源、旗标或结局，则拒绝
        no_resource_change = (cost_o == 0 and cost_p == 0 and cost_t == 0)
        gives_new_flag = len(choice.give_flags - self.state.flags) > 0
        changes_node = (choice.target != self.state.node)
        sets_ending = (choice.ending is not None)
        if (not changes_node) and no_resource_change and (not gives_new_flag) and (not sets_ending):
            return False, "此选择不会改变状态，已被视为无效以防止无限循环。"

        # 扣除资源并应用效果，保证原子性（出错则回滚）
        prev = copy.deepcopy(self.state)
        try:
            self.state.oxygen -= cost_o
            self.state.power -= cost_p
            self.state.time -= cost_t
            # 再次确保不为负（防御）
            if self.state.oxygen < 0 or self.state.power < 0 or self.state.time < 0:
                self.state = prev
                return False, "执行失败：资源不足（事务回滚）。"
            # 设置旗标
            self.state.flags = set(self.state.flags) | set(choice.give_flags)
            # 跳转或结局
            if choice.ending:
                self.state.ending = choice.ending
            self.state.node = choice.target
            return True, f"已执行：{choice.label}"
        except Exception as e:
            self.state = prev
            return False, f"执行时发生错误：{e}"

def format_costs(costs: Dict[str, int]) -> str:
    parts = []
    for k in ("oxygen", "power", "time"):
        v = costs.get(k, 0)
        if v:
            name = {"oxygen":"氧气","power":"电力","time":"时间"}[k]
            parts.append(f"{name}-{v}")
    return ", ".join(parts) if parts else "无消耗"

def run_cli(nodes: Dict[str, Node], endings: Dict[str, str]):
    game = Game(nodes)
    print("欢迎来到《折光邮局》简易交互式冒险（中文 CLI）。输入 'help' 获取帮助。")
    while True:
        try:
            node = game._get_node()
        except KeyError:
            print("当前节点配置丢失，游戏结束。")
            break

        # 显示场景
        print("\n" + "="*40)
        print(f"{node.title}\n")
        print(node.text + "\n")
        # 显示资源状态
        s = game.state
        print(f"资源 — 氧气: {s.oxygen}  电力: {s.power}  时间: {s.time}")
        if s.flags:
            print("旗标:", ", ".join(sorted(s.flags)))
        # 显示可选项
        avail = game.available()
        if not avail and s.ending is None:
            print("没有可用选项，游戏无法继续。输入 'restart' 重玩或 'quit' 退出。")
        else:
            print("可选项：")
            for c in avail:
                print(f"  {c.key}) {c.label}  [{format_costs(c.costs)}]")
        # 读取输入
        try:
            raw = input("\n请输入选项键或命令 (help): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。再见。")
            return
        if not raw:
            continue
        cmd = raw.lower()
        if cmd in ("help", "h", "?"):
            print("命令：输入选项键  | help 显示此帮助 | status 显示状态 | restart 重玩 | quit 退出")
            continue
        if cmd in ("status",):
            print(f"当前节点: {game.state.node}  资源: 氧气={s.oxygen} 电力={s.power} 时间={s.time}")
            continue
        if cmd in ("restart", "r"):
            game.reset()
            print("游戏已重置。")
            continue
        if cmd in ("quit", "q", "exit"):
            print("已退出。再见。")
            return

        # 选择处理
        ok, msg = game.choose(raw)
        print(msg)
        if not ok:
            continue
        # 检查是否到达结局
        if game.state.ending:
            end_key = game.state.ending
            print("\n" + "-"*40)
            print("结局：" + (end_key if end_key else "（未知结局）"))
            print(endings.get(end_key, "（此结局暂无描述。）"))
            # 结局后选择重玩或退出
            while True:
                try:
                    ans = input("\n输入 'replay' 重新开始，或 'quit' 退出: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print("\n已退出。再见。")
                    return
                if ans in ("replay", "r"):
                    game.reset()
                    break
                if ans in ("quit", "q"):
                    print("已退出。再见。")
                    return
                print("请输入 'replay' 或 'quit'。")