import json
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_mod import check

class TestPreflight(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/"pack.json").write_text('{"name":"test"}', encoding="utf-8")
    def tearDown(self):
        self.tmp.cleanup()
    def add_json(self,path,obj):
        target=self.root/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(obj), encoding="utf-8")

    def test_valid_stage(self):
        self.add_json("stages/rooftop.json",{
            "boyfriend":[770,100],"opponent":[100,100],"girlfriend":[400,130],
            "camera_boyfriend":[0,0]})
        problems,warnings=check(self.root)
        self.assertEqual(problems,[])
        self.assertEqual(warnings,[])

    def test_extreme_menu_offset_detected(self):
        self.add_json("images/menucharacters/slr.json",{"position":[130,165]})
        problems,warnings=check(self.root)
        self.assertFalse(problems)
        self.assertTrue(any("menu offset" in warning for warning in warnings))

    def test_large_camera_offset_warns(self):
        self.add_json("stages/test.json",{"boyfriend":[805,65],"opponent":[180,85],
            "girlfriend":[550,110],"camera_boyfriend":[0,200]})
        problems,warnings=check(self.root)
        self.assertFalse(problems)
        self.assertTrue(any("camera Y" in warning for warning in warnings))

    def test_invalid_json_rejected(self):
        p=self.root/"characters/bad.json"
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text("{bad", encoding="utf-8")
        problems,_=check(self.root)
        self.assertTrue(any("Invalid JSON" in problem for problem in problems))

    def test_character_missing_animation_name(self):
        self.add_json("characters/slr.json",{"animations":[{"name":"idle"}]})
        problems,_=check(self.root)
        self.assertTrue(any("missing anim/name" in problem for problem in problems))

if __name__ == "__main__":
    unittest.main()
