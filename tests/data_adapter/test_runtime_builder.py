from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from packages.data_adapter.runtime_builder import (
    DISTRICT_DIAGNOSTICS_FILE,
    DISTRICT_ROWS_FILE,
    FILTERED_DIAGNOSTICS_FILE,
    FILTERED_ROWS_FILE,
    MANIFEST_FILE,
    build_runtime_dataset,
    load_runtime_dataset,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "runtime_builder"


class RuntimeBuilderTests(unittest.TestCase):
    def test_manifest_row_counts_and_source_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "runtime"
            manifest = build_runtime_dataset(
                filtered_results_dir=FIXTURES / "filtered_results",
                district_csvs_dir=FIXTURES / "district_csvs",
                output_dir=out_dir,
            )

            self.assertEqual(manifest["row_counts"]["filtered_rows"], 3)
            self.assertEqual(manifest["row_counts"]["district_rows"], 2)
            self.assertEqual(sorted(manifest["source_files"]["filtered_results"]), [
                "De_Anza_College_filtered.csv",
                "Lassen_Community_College_filtered.csv",
            ])
            self.assertEqual(sorted(manifest["source_files"]["district_csvs"]), [
                "Foothill-De_Anza_Community_College_District.csv",
                "Lassen_Community_College_District.csv",
            ])

            for artifact in (
                FILTERED_ROWS_FILE,
                DISTRICT_ROWS_FILE,
                FILTERED_DIAGNOSTICS_FILE,
                DISTRICT_DIAGNOSTICS_FILE,
                MANIFEST_FILE,
            ):
                self.assertTrue((out_dir / artifact).exists(), f"missing artifact {artifact}")

    def test_checksums_stable_across_repeated_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_one = Path(tmp) / "runtime1"
            out_two = Path(tmp) / "runtime2"

            manifest_one = build_runtime_dataset(
                filtered_results_dir=FIXTURES / "filtered_results",
                district_csvs_dir=FIXTURES / "district_csvs",
                output_dir=out_one,
            )
            manifest_two = build_runtime_dataset(
                filtered_results_dir=FIXTURES / "filtered_results",
                district_csvs_dir=FIXTURES / "district_csvs",
                output_dir=out_two,
            )

            self.assertEqual(manifest_one["checksums"], manifest_two["checksums"])
            self.assertEqual(manifest_one["version"], manifest_two["version"])

            # Byte-level stability for deterministic file writes.
            for artifact in (
                FILTERED_ROWS_FILE,
                DISTRICT_ROWS_FILE,
                FILTERED_DIAGNOSTICS_FILE,
                DISTRICT_DIAGNOSTICS_FILE,
                MANIFEST_FILE,
            ):
                self.assertEqual(
                    (out_one / artifact).read_bytes(),
                    (out_two / artifact).read_bytes(),
                    f"artifact differs across runs: {artifact}",
                )

    def test_runtime_loader_uses_normalized_artifacts_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            out_dir = workspace / "runtime"
            filtered_dir = workspace / "filtered_results"
            district_dir = workspace / "district_csvs"
            filtered_dir.mkdir()
            district_dir.mkdir()

            # Copy fixtures into temp source dirs.
            for src in (FIXTURES / "filtered_results").glob("*.csv"):
                (filtered_dir / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            for src in (FIXTURES / "district_csvs").glob("*.csv"):
                (district_dir / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

            build_runtime_dataset(
                filtered_results_dir=filtered_dir,
                district_csvs_dir=district_dir,
                output_dir=out_dir,
            )

            # Remove raw sources; loader should still work from runtime artifacts alone.
            for src in filtered_dir.glob("*.csv"):
                src.unlink()
            for src in district_dir.glob("*.csv"):
                src.unlink()

            loaded = load_runtime_dataset(out_dir)
            self.assertIn("manifest", loaded)
            self.assertEqual(len(loaded["filtered_rows"]), 3)
            self.assertEqual(len(loaded["district_rows"]), 2)

            # quick shape sanity
            manifest_on_disk = json.loads((out_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
            self.assertEqual(loaded["manifest"]["version"], manifest_on_disk["version"])


if __name__ == "__main__":
    unittest.main()

