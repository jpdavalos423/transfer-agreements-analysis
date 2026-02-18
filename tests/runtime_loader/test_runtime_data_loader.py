from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from apps.api.runtime_data_loader import (
    DISTRICT_ROWS_FILE,
    MANIFEST_FILE,
    RuntimeDataError,
    load_runtime_data,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = REPO_ROOT / "data" / "runtime"


class RuntimeDataLoaderTests(unittest.TestCase):
    def test_load_runtime_data_success(self):
        loaded = load_runtime_data(RUNTIME_DIR)
        self.assertGreater(len(loaded.model.filtered_rows), 0)
        self.assertGreater(len(loaded.model.district_rows), 0)
        self.assertIsInstance(loaded.model.manifest, dict)
        self.assertIn("version", loaded.model.manifest)

    def test_missing_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with self.assertRaises(RuntimeDataError):
                load_runtime_data(tmp_path)

    def test_invalid_manifest_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name in [
                "manifest.json",
                "filtered_rows.json",
                "district_rows.json",
                "filtered_diagnostics.json",
                "district_diagnostics.json",
            ]:
                shutil.copyfile(RUNTIME_DIR / name, tmp_path / name)

            manifest_path = tmp_path / MANIFEST_FILE
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["checksums"][DISTRICT_ROWS_FILE] = "badbadbad"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            with self.assertRaises(RuntimeDataError):
                load_runtime_data(tmp_path)


if __name__ == "__main__":
    unittest.main()
