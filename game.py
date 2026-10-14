#!/usr/bin/env python3
"""《折光邮局：最后一封信》入口。只依赖 Python 标准库。"""

import argparse
from copilot_core import run_cli
from story import ENDINGS, FLAG_LABELS, NODES


def main():
    parser = argparse.ArgumentParser(description="中文科幻文字冒险《折光邮局：最后一封信》")
    parser.add_argument("--version", action="version", version="折光邮局 1.0")
    parser.parse_args()
    run_cli(NODES, ENDINGS, FLAG_LABELS)


if __name__ == "__main__":
    main()
