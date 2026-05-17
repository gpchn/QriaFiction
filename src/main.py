#!/usr/bin/env python3
# coding=utf-8

import sys
import argparse
import webview
from pathlib import Path
from app.api import LauncherApi
from app.config import config_store


def main():
    parser = argparse.ArgumentParser(description="QriaFiction 互动小说引擎")
    parser.add_argument("--debug", action="store_true", default=False,
                        help="启用调试模式（开启开发者工具和热重载）")
    args = parser.parse_args()

    static_dir = Path(__file__).parent / "static"
    index_html = static_dir / "index.html"
    width = config_store.get("window_width", 1000)
    height = config_store.get("window_height", 700)

    webview.create_window(
        "QriaFiction",
        str(index_html),
        width=width,
        height=height,
        background_color="#0a0a0a",
        js_api=LauncherApi(),
    )
    webview.start(debug=args.debug)


if __name__ == "__main__":
    main()
