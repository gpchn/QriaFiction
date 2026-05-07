#!/usr/bin/env python3
# coding=utf-8

import webview
from pathlib import Path
from jsapi import Api


def main():
    INDEX_HTML = Path(__file__).parent / "static" / "index.html"
    webview.create_window(
        "QriaFiction",
        str(INDEX_HTML),
        width=800,
        height=600,
        js_api=Api()
    )
    webview.start()



if __name__ == "__main__":
    main()