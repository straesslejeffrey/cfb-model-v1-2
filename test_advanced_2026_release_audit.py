"""End-to-end research preview release checks on all 58 frozen Week 7 inputs."""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from research_2025_fitted_totals import experimental_total, symmetric_features

PATH=Path(__file__).parent/"v1_2/data/advanced_2026_week7_research_inputs.csv"

class AdvancedReleaseAudit(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.df=pd.read_csv(PATH,low_memory=False)
 def test_complete_58_game_identity(self):
  df=self.df
  self.assertEqual(len(df),58)
  self.assertEqual(df[["season","gameId"]].drop_duplicates().shape[0],58)
  self.assertTrue((df.teamA_priorGameCount>=3).all())
  self.assertTrue((df.teamB_priorGameCount>=3).all())
  self.assertTrue((df.teamA_lastHistoricalWeek<df.week).all())
  self.assertTrue((df.teamB_lastHistoricalWeek<df.week).all())
 def test_all_research_totals_finite_and_in_reasonable_range(self):
  totals=np.asarray(experimental_total(self.df),dtype=float)
  self.assertEqual(len(totals),58)
  self.assertTrue(np.isfinite(totals).all())
  self.assertTrue(((totals>0)&(totals<150)).all())
 def test_team_swap_cannot_change_total(self):
  swapped=self.df.copy()
  pairs=[(c,"teamB"+c[len("teamA"):]) for c in self.df if c.startswith("teamA_2026_")]
  for a,b in pairs:
   swapped[a]=self.df[b].to_numpy()
   swapped[b]=self.df[a].to_numpy()
  np.testing.assert_allclose(experimental_total(self.df),experimental_total(swapped),atol=1e-9)
 def test_original_score_fields_remain_unchanged(self):
  protected=["predictedTotal","predictedMargin","projectedTeamAScore","projectedTeamBScore","projectedWinner"]
  before=self.df[protected].copy(deep=True)
  _=experimental_total(self.df)
  pd.testing.assert_frame_equal(before,self.df[protected])
 def test_symmetric_feature_contract(self):
  x=symmetric_features(self.df)
  self.assertEqual(x.shape,(58,56))
  self.assertFalse(x.isna().any().any())
if __name__=="__main__":unittest.main()
