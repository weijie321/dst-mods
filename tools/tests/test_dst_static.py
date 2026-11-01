from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).parents[1]))
from dst_static import check_resources


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mod = self.root / "mod"
        self.mod.mkdir()
        self.dst = self.root / "game"
        archive = self.dst / "data/databundles/scripts.zip"
        archive.parent.mkdir(parents=True)
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("scripts/mods.lua", "MOD_API_VERSION = 10")
        (self.mod / "modmain.lua").write_text("-- blank valid mod")
        (self.mod / "modinfo.lua").write_text('name="name"; description="desc"; author="author"; version="1"; api_version=10; dst_compatible=true')

    def test_missing_asset_and_prefab_fail(self):
        (self.mod / "modmain.lua").write_text('PrefabFiles={"missing"}; Assets={Asset("IMAGE","images/missing.tex")}')
        result = check_resources(self.mod, self.dst)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["errors"]), 2)

    def test_comments_do_not_create_fake_asset(self):
        (self.mod / "modmain.lua").write_text('-- Asset("IMAGE", "missing.tex")\nlocal x="--not a comment"')
        self.assertEqual(check_resources(self.mod, self.dst)["status"], "passed")

    def test_dynamic_resource_requires_review(self):
        (self.mod / "modmain.lua").write_text('Assets={Asset("IMAGE", image_path)}')
        self.assertEqual(check_resources(self.mod, self.dst)["status"], "review_required")

    def test_explicit_nonstring_metadata_fails(self):
        (self.mod / "modinfo.lua").write_text('name=nil; description=false; author=1; version={}; api_version=10; dst_compatible=true')
        self.assertEqual(len(check_resources(self.mod, self.dst)["errors"]), 4)


if __name__ == "__main__":
    unittest.main()
