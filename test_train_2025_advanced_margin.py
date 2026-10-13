import unittest
import pandas as pd
from research.train_2025_advanced_margin import evaluate
from train_advanced_totals_research import PAIR_METRICS
class MarginResearchTests(unittest.TestCase):
 def test_malformed_target_rejected(self):
  row={"week_base":7,"frozenV12Margin":2.,"actualMarginTeamA":7.,
       "actualTeamAPoints":10.,"actualTeamBPoints":9.}
  for m in PAIR_METRICS:
   for w in (3,5):
    row[f"home_pregame_{m}_L{w}"]=0.3
    row[f"home_opp_pregame_{m}_L{w}"]=0.2
  with self.assertRaisesRegex(ValueError,"Invalid margin"):
   evaluate(pd.DataFrame([row]))
if __name__=="__main__":unittest.main()
