import unittest
from gate_advanced_totals_promotion import decide

class GateTests(unittest.TestCase):
 def test_real_observed_holdout_is_not_promoted(self):
  observed={"gain":0.2002502328453622,
   "bootstrap_95pct_interval_for_gain":[-0.35827071074000855,0.7389141980168229],
   "by_week":[{"baseline_mae":12.076,"candidate_mae":11.350},
              {"baseline_mae":14.357,"candidate_mae":14.166},
              {"baseline_mae":12.738,"candidate_mae":12.985}]}
  r=decide(observed)
  self.assertFalse(r["promote"])
  self.assertFalse(r["checks"]["bootstrap_lower_bound_positive"])
  self.assertFalse(r["checks"]["independent_cross_season_passed"])
 def test_all_conditions_required(self):
  good={"gain":0.3,"bootstrap_95pct_interval_for_gain":[0.1,0.5],
   "by_week":[{"baseline_mae":13,"candidate_mae":12.5}],
   "independent_cross_season_passed":True}
  self.assertTrue(decide(good)["promote"])
  good["independent_cross_season_passed"]=False
  self.assertFalse(decide(good)["promote"])
if __name__=="__main__":unittest.main()
