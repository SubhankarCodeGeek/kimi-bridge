import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.build_binary import compute_sha256, generate_checksums, get_target_info


class BuildBinaryTests(unittest.TestCase):
    def test_get_target_info_format(self) -> None:
        target_stem, target_name = get_target_info()
        self.assertTrue(target_stem.startswith("kimibridge-"))
        self.assertTrue(target_name.startswith("kimibridge-"))
        self.assertIn("-", target_stem)

    def test_compute_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_bytes(b"hello world\n")

            digest = compute_sha256(test_file)
            expected = hashlib.sha256(b"hello world\n").hexdigest()
            self.assertEqual(digest, expected)

    def test_generate_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "kimibridge-linux-x86_64").write_bytes(b"dummy binary data")

            checksum_file = generate_checksums(tmp_path)
            self.assertTrue(checksum_file.exists())
            content = checksum_file.read_text(encoding="utf-8")
            self.assertIn("kimibridge-linux-x86_64", content)


if __name__ == "__main__":
    unittest.main()
