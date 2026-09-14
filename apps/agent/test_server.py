import tempfile
import unittest
from pathlib import Path

from server import discover_names


class DiscoveryTest(unittest.TestCase):
    def test_discovers_only_directories_with_marker(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            Path(root, "valid").mkdir()
            Path(root, "valid", "domain.yaml").touch()
            Path(root, "ignored").mkdir()
            self.assertEqual(discover_names(root, "domain.yaml"), ["valid"])


if __name__ == "__main__":
    unittest.main()
