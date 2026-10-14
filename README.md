# 折光邮局：最后一封信

一座绕着冰巨星运行的邮局遭遇碎冰潮。你是最后的值班员，需要在有限的氧气、电力和行动时间内，决定带走乘员、寄出记忆，或者独自回家。

中文命令行文字冒险，13 个阶段、5 个结局。首次细读与思考的目标时长约 5–10 分钟；这是设计估计，实际时长随阅读速度变化。没有现实倒计时，也没有强制等待。

## 开始游戏

下载或克隆仓库后，进入仓库根目录，在终端运行：

```sh
python3 game.py
```

使用 Python 3.10 或更新版本的标准库，不需要 `pip install`，运行游戏不联网、不读其他项目、不写存档。实际验证环境：macOS、Python 3.14.7。

输入画面显示的编号进行选择。`help` / `h` / `?` 查看帮助，`status` 查看状态，`restart` 重开，`quit` 退出。结局后输入 `replay` 重玩。本次启动中发现的结局数会保留到退出；下次启动重新计数。

氧气初始 12、电力初始 10、行动时间初始 14。每个选项标明花费。阅读、帮助、状态查询和无效输入不扣资源；缺少前置物品或付不起的选项不会显示。没有随机判定，剧情可以复现。

## 验证

```sh
python3 -m unittest discover -s tests -v
```

已通过 20 项测试，穷举 25,605 个不同的可达状态，确认没有负资源、无路可走的状态或不可达的结局。五条路线还各自启动了真实的 `game.py` 命令行程序，走到结局并正常退出。

要重新生成测试与通关记录：

```sh
python3 verify.py
```

验证会更新本项目 `evidence/` 中的测试、通关输出与源文件校验摘要。`evidence/tests.txt`、`verification.json` 和五份 `play_*.txt` 是本次实际运行记录。

## 文件与来源

- `game.py`：启动入口。
- `copilot_core.py`：实际由 GitHub Copilot 生成后，经 Codex 修订的状态引擎和命令行交互。
- `story.py`：本次新创作的设定、资源决策、剧情和结局。
- `MLH_SOURCE.py`：提交说明中嵌入的独立可运行版本，五种结局另行验证通过。
- `tests/test_game.py`：自动化验证。
- `RULES.md`：游戏与官方挑战规则。
- `TOOL_USAGE.md`：Copilot 实际使用记录、贡献范围与修改说明。
- `WALKTHROUGH.md`：带剧透的五条通关路线。
- `evidence/copilot_core_original.py`：从网页 Copilot 回复直接复制并保存的原始代码。

这是在本次独立目录制作的新作品。没有复制用户其他游戏项目。Copilot 原始回复和 Codex 后续工作分开记录；没有把全部工作声称为 Copilot 完成。

## MLH 挑战

本项目用于 [Use GitHub Copilot to Build a Simple Application](https://www.mlh.com/challenges/01a11b46-2f5c-3ba2-3dac-73e6f58fd53e)。实际使用 GitHub Copilot 的范围与原始回复见 TOOL_USAGE.md 和 evidence/。当前仓库仅包含本次新项目，测试与通关输出均来自实际运行。
