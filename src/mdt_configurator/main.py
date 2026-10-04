from __future__ import annotations

import sys


def main() -> None:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise SystemExit('PySide6 is required. Install with: pip install -e ".[gui]"') from exc

    from mdt_configurator.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("MDT Linux Configurator")
    window = MainWindow()
    window.resize(1180, 760)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
