import unittest
import pandas as pd
from validate_2026_training_inputs import validate, METRICS

class CurrentSeasonValidationTest(unittest.TestCase):
    def setUp(self):
        row={"season":2026,"week":7,"gameId":1,"teamA":"A","teamB":"B",
             "predictedTotal":49.0,"predictedMargin":2.0}
        for side in ("teamA","teamB"):
            row[side+"_priorGameCount"]=5
            row[side+"_lastHistoricalWeek"]=6
            for metric in METRICS:
                for window in (3,5):
                    row[f"{side}_2026_{metric}_last{window}"]=0.25
        self.df=pd.DataFrame([row])
    def test_valid_input(self):
        result=validate(self.df)
        self.assertEqual(result["advanced_feature_count"],56)
        self.assertEqual(result["rows_at_least_80pct_coverage"],1)
    def test_same_week_leakage(self):
        bad=self.df.copy()
        bad.loc[0,"teamB_lastHistoricalWeek"]=7
        with self.assertRaisesRegex(ValueError,"historical week"):
            validate(bad)
    def test_duplicate_identity(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            validate(pd.concat([self.df,self.df]))
    def test_missing_metric(self):
        bad=self.df.drop(columns=["teamB_2026_offPPAperPlay_last5"])
        with self.assertRaisesRegex(ValueError,"Missing"):
            validate(bad)
if __name__=="__main__":unittest.main()
