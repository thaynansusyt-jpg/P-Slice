import json
import unittest
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1] / "presets/reboot-teste-stage-camera-v4.json"

class TestCameraPreset(unittest.TestCase):
    def test_height_alignment(self):
        stage = json.loads(STAGE.read_text(encoding="utf-8"))
        # Medicoes reais do Android em 10/10/2026:
        # BF: y=339 h=418 (o JSON do BF acrescenta +350)
        # Laranja: y=79 h=678 (character position Y=-6)
        bf_y = stage["boyfriend"][1] + 350
        opponent_y = stage["opponent"][1] - 6
        self.assertEqual(bf_y + 418, opponent_y + 678)
        self.assertEqual(bf_y + 418, 757)

    def test_camera_targets_equal_at_measured_pose(self):
        stage = json.loads(STAGE.read_text(encoding="utf-8"))
        bf_y = stage["boyfriend"][1] + 350
        dad_y = stage["opponent"][1] - 6
        # P-Slice PlayState.moveCamera() usa o midpoint -100 + offsets.
        bf_cam_y = bf_y + 418 / 2 - 100 + stage["camera_boyfriend"][1]
        dad_cam_y = dad_y + 678 / 2 - 100 - 25 + stage["camera_opponent"][1]
        self.assertAlmostEqual(bf_cam_y, 323)
        self.assertAlmostEqual(dad_cam_y, 323)

if __name__ == "__main__":
    unittest.main()
