#!/usr/bin/env python3
"""Fast regression checks for cached RK3506 navigation frames."""
import pathlib
import sys
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

    def test_nodes_page_exposes_separate_add_and_edit_actions(self):
        import dashboard
        view = dashboard._sample_view()
        view["configured_nodes"] = [{
            "id": "local-ttyS1-9", "name": "水泵 9", "deviceType": "pump_vfd",
            "serialPort": "/dev/ttyS1", "slaveId": 9,
        }]
        _, buttons = dashboard.render(view, page="nodes")
        actions = {button.get("action") for button in buttons}
        self.assertIn("open_device_add", actions)
        self.assertIn("open_device_config", actions)


if __name__ == "__main__":
    unittest.main()
