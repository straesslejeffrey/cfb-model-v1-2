import unittest
import pandas as pd
from gate_historical_v12_baseline import historical_baseline_gate

class BaselineGateTest(unittest.TestCase):
    def test_missing_2024_blocks(self):
        h=pd.DataFrame([{"season":2024,"gameId":1},{"season":2025,"gameId":2}])
        b=pd.DataFrame([{"season":2025,"gameId":2,"actualTotal":52,"frozenV12Total":49}])
        r=historical_baseline_gate(h,b)
        self.assertFalse(r["cross_season_v12_comparison_ready"])
        self.assertEqual(r["years"]["2024"]["missing"],1)
    def test_complete_passes(self):
        h=pd.DataFrame([{"season":2024,"gameId":1},{"season":2025,"gameId":2}])
        b=pd.DataFrame([{"season":2024,"gameId":1,"actualTotal":42,"frozenV12Total":41},
                        {"season":2025,"gameId":2,"actualTotal":52,"frozenV12Total":49}])
        self.assertTrue(historical_baseline_gate(h,b)["cross_season_v12_comparison_ready"])
if __name__=="__main__": unittest.main()
