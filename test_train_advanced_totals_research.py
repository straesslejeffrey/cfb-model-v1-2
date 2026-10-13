import unittest
import pandas as pd
from train_advanced_totals_research import symmetric_features,PAIR_METRICS
class SymmetricTrainingFeaturesTests(unittest.TestCase):
    def test_schema_and_orientation_invariance(self):
        hist={"home_pregame_"+m+"_L"+str(w):.8 for m in PAIR_METRICS for w in (3,5)}
        hist.update({"home_opp_pregame_"+m+"_L"+str(w):.3 for m in PAIR_METRICS for w in (3,5)})
        live={"teamA_2026_"+m+"_last"+str(w):.8 for m in PAIR_METRICS for w in (3,5)}
        live.update({"teamB_2026_"+m+"_last"+str(w):.3 for m in PAIR_METRICS for w in (3,5)})
        a=symmetric_features(pd.DataFrame([hist]),True)
        b=symmetric_features(pd.DataFrame([live]),False)
        self.assertEqual(a.columns.tolist(),b.columns.tolist())
        self.assertTrue(a.equals(b))
        switched={**{"teamA_2026_"+m+"_last"+str(w):.3 for m in PAIR_METRICS for w in (3,5)},
          **{"teamB_2026_"+m+"_last"+str(w):.8 for m in PAIR_METRICS for w in (3,5)}}
        self.assertTrue(a.equals(symmetric_features(pd.DataFrame([switched]),False)))
if __name__=="__main__":unittest.main()
