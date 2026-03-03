# This Python file uses the following encoding: utf-8
import asyncio
import sys

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtWidgets import QApplication

from qt.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    with AsyncioPySide6.use_asyncio():
        app.setApplicationDisplayName('AdGuard VPN')
        window = MainWindow()
        asyncio.run(window.init_app())

        app.exec()


if __name__ == "__main__":
    main()
