#!/usr/bin/env python3
"""Fast regression checks for cached RK3506 navigation frames."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import drm_hmi_v4


class HmiFrameTests(unittest.TestCase):
    def test_prepare_rgb_converts_to_drm_bgrx(self):
        pixel_count = drm_hmi_v4.W * drm_hmi_v4.H
        rgb = bytes((0x11, 0x22, 0x33)) * pixel_count
        frame = drm_hmi_v4.Screen.prepare_rgb(rgb)
        self.assertEqual(len(frame), pixel_count * 4)
        self.assertEqual(frame[:8], bytes((0x33, 0x22, 0x11, 0x00)) * 2)

    def test_frame_cache_keeps_frame_and_matching_buttons(self):
        cache = drm_hmi_v4.FrameCache()
        buttons = [{"rect": (0, 442, 100, 38), "nav": "overview"}]
        cache.put("overview", b"prepared", buttons)
        buttons.clear()
        frame, cached_buttons = cache.get("overview")
        self.assertEqual(frame, b"prepared")
        self.assertEqual(cached_buttons[0]["nav"], "overview")
        self.assertIsNone(cache.get("monitor"))
        cache.invalidate("overview")
        self.assertIsNone(cache.get("overview"))

    def test_nodes_page_is_readonly_after_devcfg_retirement(self):
        """设备页只读:配置入口已退役(设备接入走 Web /config 页),只剩导航按钮。"""
        import dashboard
        _, buttons = dashboard.render(dashboard._sample_view(), page="nodes")
        self.assertEqual([b.get("action") for b in buttons if "action" in b], [])
        self.assertEqual(len([b for b in buttons if "nav" in b]), 5)

    def test_settings_page_exposes_brightness_and_theme_actions(self):
        import dashboard
        view = dashboard._sample_view()
        view["local_settings"] = {"brightness": 70, "theme": "dark"}
        dashboard.apply_theme("dark")
        try:
            _, buttons = dashboard.render(view, page="settings")
        finally:
            dashboard.apply_theme("light")
        actions = [button.get("action") for button in buttons]
        self.assertEqual(actions.count("brightness_change"), 2)
        self.assertEqual(actions.count("theme_set"), 2)

    def test_settings_round_trip_and_clamp(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(pathlib.Path(directory) / "hmi-settings.json")
            saved = drm_hmi_v4.save_settings(
                {"brightness": 0, "theme": "dark"}, path)
            self.assertEqual(saved, {"brightness": 10, "theme": "dark"})
            self.assertEqual(drm_hmi_v4.load_settings(path), saved)

    def test_brightness_percent_maps_to_driver_range(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "max_brightness").write_text("255", encoding="ascii")
            (root / "brightness").write_text("200", encoding="ascii")
            raw = drm_hmi_v4.apply_brightness(50, directory)
            self.assertEqual(raw, 128)
            self.assertEqual((root / "brightness").read_text(encoding="ascii"), "128")


if __name__ == "__main__":
    unittest.main()
