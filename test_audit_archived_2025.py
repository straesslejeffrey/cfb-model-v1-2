import unittest
import pandas as pd
from audit_archived_2025 import evaluate

class ArchivedAuditTests(unittest.TestCase):
    def test_original_backtest_week_base_schema(self):
        df=pd.DataFrame({
            "gameId":[1,2],"season":[2025,2025],"week_base":[1,2],
            "actualTotal":[30,40],"frozenV12Total":[34,46],
            "advancedChallengerTotal":[33,44]})
        r=evaluate(df)
        self.assertEqual(r["overall"]["games"],2)
        self.assertEqual(len(r["by_week"]),2)
        self.assertAlmostEqual(r["overall"]["improvement"],1.5)

    def test_reject_duplicate_matchups(self):
        df=pd.DataFrame({
            "gameId":[1,1],"season":[2025,2025],"week_base":[1,1],
            "actualTotal":[30,30],"frozenV12Total":[35,35],
            "advancedChallengerTotal":[33,33]})
        with self.assertRaises(ValueError):
            evaluate(df)

if __name__=="__main__":
    unittest.main()
