#!/usr/bin/env python3
# coding=utf-8

import webview
from pathlib import Path
from app.api import LauncherApi
from app.config import config_store


def main():
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
    webview.start(debug=True)


if __name__ == "__main__":
    main()
