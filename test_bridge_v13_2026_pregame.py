import unittest
import pandas as pd
from bridge_v13_2026_pregame import add_advanced_context

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.pred=pd.DataFrame([dict(season=2026,week=7,gameId=100,teamA="A",teamB="B",
                            predictedTotal=50.,predictedMargin=4.)])
        self.matrix=pd.DataFrame([dict(season=2026,week=7,gameId=100,homeTeam="A",awayTeam="B",
                              home_pregame_offSuccessRate_L5=.41,
                              away_pregame_defSuccessRateAllowed_L5=.39,
                              home_offPointsPerDrive=999.)])
    def test_keep_original_and_exclude_postgame_stats(self):
        out=add_advanced_context(self.pred,self.matrix)
        self.assertEqual(out.predictedTotal.iloc[0],50.)
        self.assertTrue(out.advanced2026Ready.iloc[0])
        self.assertNotIn("advanced_home_offPointsPerDrive",out.columns)
        self.assertAlmostEqual(out.advanced_home_pregame_offSuccessRate_L5.iloc[0],.41)
    def test_mismatched_team_names_rejected_for_evidence(self):
        m=self.matrix.copy()
        m.loc[0,"homeTeam"]="C"
        out=add_advanced_context(self.pred,m)
        self.assertFalse(out.advanced2026Ready.iloc[0])
        self.assertTrue(pd.isna(out.advanced_home_pregame_offSuccessRate_L5.iloc[0]))
    def test_week_mismatch_rejected(self):
        m=self.matrix.copy();m.loc[0,"week"]=6
        out=add_advanced_context(self.pred,m)
        self.assertFalse(out.advanced2026IdentityMatch.iloc[0])
    def test_duplicate_matrix_raises(self):
        with self.assertRaises(ValueError):
            add_advanced_context(self.pred,pd.concat([self.matrix,self.matrix]))

if __name__=="__main__":unittest.main()
