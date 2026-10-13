import unittest
import pandas as pd
from advanced_features import build_current_team_features, METRICS
from enrich_v12_matchups import enrich

class AdvancedEnrichmentTests(unittest.TestCase):
    def test_scores_unchanged_and_matchup_gap(self):
        if "rushSuccessRate" not in METRICS: METRICS.append("rushSuccessRate")
        if "defRushSuccessRateAllowed" not in METRICS: METRICS.append("defRushSuccessRateAllowed")
        history=pd.DataFrame([
          dict(season=2026,week=1,gameId=1,team="A",opponent="B",rushSuccessRate=.6,defRushSuccessRateAllowed=.3),
          dict(season=2026,week=1,gameId=1,team="B",opponent="A",rushSuccessRate=.4,defRushSuccessRateAllowed=.5),
        ])
        upcoming=pd.DataFrame([
          dict(season=2026,week=2,gameId=2,team="A",opponent="B"),
          dict(season=2026,week=2,gameId=2,team="B",opponent="A"),
        ])
        snap=build_current_team_features(history,upcoming)
        predictions=pd.DataFrame([dict(season=2026,week=2,gameId=2,teamA="A",teamB="B",
              predictedTotal=47.,predictedMargin=6.)])
        outcome=enrich(predictions,snap,min_coverage=0)
        self.assertEqual(len(outcome),1)
        self.assertEqual(outcome.predictedTotal.iloc[0],47.)
        self.assertEqual(outcome.predictedMargin.iloc[0],6.)
        self.assertAlmostEqual(outcome.home_rush_success_offMinusOppDef_last3.iloc[0],.1)
        self.assertAlmostEqual(outcome.away_rush_success_offMinusOppDef_last3.iloc[0],.1)
        self.assertIn("ADVANCED EVIDENCE",outcome.advancedMatchupStatus.iloc[0])
    def test_reject_missing_team_snapshot(self):
        predictions=pd.DataFrame([dict(season=2026,week=2,gameId=2,teamA="A",teamB="B",
              predictedTotal=47.,predictedMargin=6.)])
        snapshots=pd.DataFrame(columns=["season","week","gameId","team","priorGames"])
        with self.assertRaises(ValueError):
            enrich(predictions,snapshots)

if __name__=="__main__":
    unittest.main()
