#!/usr/bin/env python3
"""重新运行测试与五条真实 CLI 路线，保存不含凭据的验证记录。"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
from test_game import ROUTES
from story import ENDINGS


def main():
    destination = ROOT / "evidence"
    destination.mkdir(exist_ok=True)
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                           text=True, capture_output=True, cwd=ROOT, timeout=60)
    (destination / "tests.txt").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    result = {"verified_at_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "tests_exit_code": tests.returncode,
              "endings": {}, "source_sha256": {}}
    for ending, route in ROUTES.items():
        inputs = route + ["quit"]
        p = subprocess.run([sys.executable, "game.py"], input="\n".join(inputs) + "\n",
                           text=True, capture_output=True, cwd=ROOT, timeout=10)
        (destination / f"play_{ending}.txt").write_text(
            "实际启动命令：python3 game.py\n输入（每行一条）：\n" + "\n".join(inputs)
            + "\n\n标准输出：\n" + p.stdout + "\n标准错误：\n" + p.stderr, encoding="utf-8")
        passed = p.returncode == 0 and ENDINGS[ending].splitlines()[0] in p.stdout and not p.stderr
        result["endings"][ending] = {"route": route, "exit_code": p.returncode, "passed": passed}
    for name in ("game.py", "copilot_core.py", "story.py", "tests/test_game.py",
                 "evidence/copilot_core_original.py"):
        result["source_sha256"][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    (destination / "verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if tests.returncode == 0 and all(v["passed"] for v in result["endings"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
