import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch

from patch_candidate import Rejected
import proton_launcher as linux
import proton_support as wine
from test_native_trial import synthetic_image


@unittest.skipUnless(sys.platform.startswith("linux"), "Native Linux launcher tests")
class ProtonLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, _, cls.spec = synthetic_image()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.library = self.root / "Steam library with spaces; $literal"
        self.executable = self.library / "steamapps/common/Resident Evil 6/BH6.exe"
        self.executable.parent.mkdir(parents=True)
        self.executable.write_bytes(self.original)
        (self.library / "steamapps/appmanifest_221040.acf").write_text(
            '"AppState" { "appid" "221040" "installdir" "Resident Evil 6" }')
        self.prefix = self.library / "steamapps/compatdata/221040/pfx"
        self.prefix.mkdir(parents=True)
        (self.prefix / "system.reg").touch()
        self.bundle = self.root / "Patch bundle"
        self.bundle.mkdir()
        self.helper = self.bundle / "RE6MercenariesPatch.exe"
        self.helper.write_bytes(b"MZ synthetic helper fixture")
        (self.bundle / "proton-bundle.json").write_text(json.dumps({
            "helper_sha256": hashlib.sha256(self.helper.read_bytes()).hexdigest()}))

    def command(self, environ=None, game_dir=None):
        with patch.object(linux, "pinned_manifest", return_value=self.spec):
            return linux.build_command([self.library], self.bundle, environ or {}, "/usr/bin/protontricks-launch",
                                       game_dir=game_dir)

    def test_same_app_prefix_and_library_are_passed_without_shell_interpretation(self):
        command = self.command()
        self.assertEqual(command[:4], ["/usr/bin/protontricks-launch", "--appid", "221040", str(self.helper)])
        self.assertEqual(command[4:], ["--proton-library", "Z:" + str(self.library).replace("/", "\\")])
        self.assertIn("$literal", command[-1])
        self.assertEqual(self.executable.read_bytes(), self.original)

    def test_wrong_executable_or_tampered_helper_is_refused(self):
        self.executable.write_bytes(b"unsupported build")
        with self.assertRaisesRegex(Rejected, "Unsupported executable"):
            self.command()
        self.executable.write_bytes(self.original)
        self.helper.write_bytes(b"changed helper")
        with self.assertRaisesRegex(Rejected, "checksum"):
            self.command()

    def test_missing_prefix_is_not_initialized_implicitly(self):
        (self.prefix / "system.reg").unlink()
        with self.assertRaisesRegex(Rejected, "prefix is missing"):
            self.command()
        self.assertFalse((self.prefix / "system.reg").exists())

    def test_custom_compat_data_path_is_honored(self):
        custom = self.root / "Custom prefix"
        (custom / "pfx").mkdir(parents=True)
        (custom / "pfx/system.reg").touch()
        (self.prefix / "system.reg").unlink()
        self.assertEqual(self.command({"STEAM_COMPAT_DATA_PATH": str(custom)})[2], "221040")

    def test_native_root_discovery_handles_xdg_and_symlink_duplicates(self):
        home = self.root / "User home"
        xdg = home / "Data"
        (xdg / "Steam").mkdir(parents=True)
        roots = linux.native_steam_roots(home, {"XDG_DATA_HOME": str(xdg), "STEAM_DIR": str(xdg / "Steam")})
        self.assertEqual(roots, [(xdg / "Steam").resolve()])

    def test_custom_xdg_does_not_hide_standard_steam_location(self):
        home = self.root / "User home"
        standard = home / ".local/share/Steam"
        standard.mkdir(parents=True)
        (home / ".steam").mkdir()
        (home / ".steam/steam").symlink_to(standard, target_is_directory=True)
        (home / ".steam/root").symlink_to(standard, target_is_directory=True)
        roots = linux.native_steam_roots(home, {"XDG_DATA_HOME": str(home / "Custom data")})
        self.assertEqual(roots, [standard.resolve()])

    def test_no_install_and_multiple_installs_have_distinct_useful_errors(self):
        with patch.object(linux, "discover_installs", return_value=[]):
            with self.assertRaisesRegex(Rejected, "No registered RE6.*Searched:"):
                self.command()
        with patch.object(linux, "discover_installs", return_value=[self.executable, Path("/other/BH6.exe")]):
            with self.assertRaisesRegex(Rejected, "Found 2 registered RE6 copies") as raised:
                self.command()
            self.assertIn(str(self.executable), str(raised.exception))
            self.assertIn("/other/BH6.exe", str(raised.exception))

    def test_explicit_game_folder_selects_linux_copy_among_dual_boot_libraries(self):
        other = self.root / "Windows library/steamapps/common/Resident Evil 6/BH6.exe"
        other.parent.mkdir(parents=True)
        other.write_bytes(self.original)
        with patch.object(linux, "discover_installs", return_value=[other, self.executable]):
            command = self.command(game_dir=self.executable.parent)
        self.assertEqual(command[-1], linux.wine_path(self.library))
        self.assertEqual(self.executable.read_bytes(), self.original)
        self.assertEqual(other.read_bytes(), self.original)

    def test_game_folder_selection_does_not_bypass_registration_or_hash(self):
        with patch.object(linux, "discover_installs", return_value=[]):
            with self.assertRaisesRegex(Rejected, "not a registered"):
                self.command(game_dir=self.executable.parent)
        self.executable.write_bytes(b"unsupported executable")
        with self.assertRaisesRegex(Rejected, "Unsupported executable"):
            self.command(game_dir=self.executable.parent)

    def test_explicit_library_is_wine_only_and_still_requires_steam_manifest(self):
        with patch.object(wine, "wine_version", side_effect=Rejected("Wine required")):
            with self.assertRaisesRegex(Rejected, "Wine required"):
                wine.checked_library(self.library)
        with patch.object(wine, "wine_version", return_value="test Wine"):
            self.assertEqual(wine.checked_library(self.library), (self.library.resolve(), "test Wine"))
            (self.library / "steamapps/appmanifest_221040.acf").unlink()
            with self.assertRaisesRegex(Rejected, "app manifest"):
                wine.checked_library(self.library)


if __name__ == "__main__":
    unittest.main()
