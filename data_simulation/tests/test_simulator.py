import os
import unittest
from collections import defaultdict
from data_simulation.dataset import load_fd001_dataframe
from data_simulation.simulator import replay_engine, MultiEngineScheduler

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "train_FD001.txt")


class TestSimulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = load_fd001_dataframe(target_path=DATA_PATH)

    def test_cycles_strictly_increasing_per_engine(self):
        """Assert cycles come out strictly increasing per engine."""
        engine_id = 1
        gen = replay_engine(engine_id, df=self.df, delay=0.0)

        prev_cycle = 0
        cycle_count = 0
        for record in gen:
            curr_cycle = record["cycle"]
            self.assertEqual(
                curr_cycle,
                prev_cycle + 1,
                f"Cycle count out of order for engine {engine_id}: expected {prev_cycle + 1}, got {curr_cycle}"
            )
            self.assertEqual(record["asset_id"], f"ENG-{engine_id:03d}")
            prev_cycle = curr_cycle
            cycle_count += 1

        self.assertGreater(cycle_count, 0, "No records yielded")

    def test_multi_engine_concurrent_streaming_order(self):
        """Assert running multiple engines concurrently doesn't interleave one engine's cycles out of order."""
        engine_ids = [1, 2, 3, 4, 5]
        scheduler = MultiEngineScheduler(engine_ids=engine_ids, delay=0.0, df=self.df)

        engine_cycles = defaultdict(list)
        total_records = 0

        for record in scheduler.stream_all():
            asset_id = record["asset_id"]
            cycle = record["cycle"]

            # Verify that for this specific engine, cycle is strictly greater than the last recorded cycle
            if engine_cycles[asset_id]:
                last_cycle = engine_cycles[asset_id][-1]
                self.assertEqual(
                    cycle,
                    last_cycle + 1,
                    f"Interleaved or out-of-order cycle detected for {asset_id}: last cycle was {last_cycle}, current cycle is {cycle}"
                )

            engine_cycles[asset_id].append(cycle)
            total_records += 1

        # Assert all 5 engines yielded records
        self.assertEqual(len(engine_cycles), 5)
        for eng_id in engine_ids:
            asset_id = f"ENG-{eng_id:03d}"
            cycles = engine_cycles[asset_id]
            self.assertEqual(cycles[0], 1, f"{asset_id} did not start at cycle 1")
            self.assertEqual(cycles, list(range(1, len(cycles) + 1)), f"{asset_id} cycles were out of sequence")

        self.assertGreater(total_records, 500)


if __name__ == "__main__":
    unittest.main()
