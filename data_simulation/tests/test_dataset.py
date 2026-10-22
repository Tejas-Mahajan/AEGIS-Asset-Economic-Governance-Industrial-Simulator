import os
import unittest
from data_simulation.dataset import load_fd001_dataframe, COLUMN_NAMES

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "train_FD001.txt")


class TestDatasetFD001(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = load_fd001_dataframe(target_path=DATA_PATH)

    def test_dataframe_column_count(self):
        """Assert the dataframe has the expected column count (26 columns)."""
        self.assertEqual(
            len(self.df.columns),
            26,
            f"Expected 26 columns, got {len(self.df.columns)}"
        )
        self.assertEqual(list(self.df.columns), COLUMN_NAMES)

    def test_cycle_counts_vary_across_engines(self):
        """Assert cycle counts vary across at least two different engine IDs."""
        max_cycles = self.df.groupby("engine_id")["cycle"].max()
        
        # Check there are multiple engines
        self.assertGreaterEqual(
            len(max_cycles),
            2,
            "Expected at least 2 distinct engine IDs"
        )
        
        # Check that cycle counts vary across engines
        unique_cycle_counts = max_cycles.nunique()
        self.assertGreater(
            unique_cycle_counts,
            1,
            f"Expected varying max cycle counts across engines, found all equal: {max_cycles.unique()}"
        )
        
        # Check engine 1 and engine 2 cycle count difference
        e1_max = max_cycles.loc[1]
        e2_max = max_cycles.loc[2]
        self.assertNotEqual(
            e1_max,
            e2_max,
            f"Engine 1 max cycle ({e1_max}) should differ from Engine 2 max cycle ({e2_max})"
        )


if __name__ == "__main__":
    unittest.main()
