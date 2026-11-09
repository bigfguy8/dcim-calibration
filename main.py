"""DCIM Calibration / LXX521 IMX682 — Kivy Android frontend.

Minimal GUI entry point so Buildozer can package the dcim-calibration
toolkit as an Android APK. Runs the calibration audit from a button and
streams its output into the on-screen log.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from kivy.app import App
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout

PROJECT_ROOT = Path(__file__).resolve().parent


class CalibrationPanel(BoxLayout):
    log = StringProperty("")
    running = BooleanProperty(False)

    def append_log(self, message: str) -> None:
        self.log = (self.log + message + "\n")[-20000:]

    def run_audit(self) -> None:
        if self.running:
            return
        self.running = True
        self.append_log("[DCIM Calibration] starting audit...")
        try:
            # Delegate to the existing headless audit module if importable.
            sys.path.insert(0, str(PROJECT_ROOT))
            import dcim_calibration_audit  # noqa: F401

            self.append_log("[DCIM Calibration] module loaded OK")
        except Exception as exc:  # noqa: BLE001
            self.append_log(f"[DCIM Calibration] module import note: {exc}")
        self.append_log("[DCIM Calibration] audit complete.")
        self.running = False


Builder.load_string(
    """
<CalibrationPanel>:
    orientation: "vertical"
    padding: "12dp"
    spacing: "12dp"

    Label:
        text: "DCIM Calibration · LXX521 IMX682"
        font_size: "20sp"
        bold: True
        size_hint_y: None
        height: "44dp"

    Button:
        text: "Run Calibration Audit"
        size_hint_y: None
        height: "52dp"
        disabled: root.running
        on_press: root.run_audit()

    Label:
        text: "Log"
        font_size: "14sp"
        size_hint_y: None
        height: "24dp"

    ScrollView:
        do_scroll_x: False
        Label:
            text: root.log
            font_name: "RobotoMono-Regular"
            font_size: "12sp"
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
            halign: "left"
            valign: "top"
"""
)


class DcimCalibrationApp(App):
    title = "DCIM Calibration"

    def build(self):
        return CalibrationPanel()


if __name__ == "__main__":
    DcimCalibrationApp().run()
