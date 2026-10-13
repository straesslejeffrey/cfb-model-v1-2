import unittest
import pandas as pd
from advanced_features import (
    build_pregame_team_features, build_current_team_features,
    build_matchup_features, coverage_report,
)

class AdvancedFeaturesTests(unittest.TestCase):
    def setUp(self):
        self.games = pd.DataFrame([
            dict(season=2026, week=1, gameId=1, team="A", opponent="B", offEPA=0.4, defHavocCreated=0.2),
            dict(season=2026, week=1, gameId=1, team="B", opponent="A", offEPA=-0.1, defHavocCreated=0.1),
            dict(season=2026, week=2, gameId=2, team="A", opponent="B", offEPA=0.1, defHavocCreated=0.3),
            dict(season=2026, week=2, gameId=2, team="B", opponent="A", offEPA=0.2, defHavocCreated=0.15),
        ])

    def test_no_current_game_leakage(self):
        p = build_pregame_team_features(self.games)
        a1 = p[(p.team == "A") & (p.week == 1)].iloc[0]
        a2 = p[(p.team == "A") & (p.week == 2)].iloc[0]
        self.assertEqual(a1.priorGames, 0)
        self.assertTrue(pd.isna(a1.adv_offEPA_last3))
        self.assertEqual(a2.priorGames, 1)
        self.assertAlmostEqual(a2.adv_offEPA_last3, 0.4)
        self.assertEqual(a2.adv_offEPA_n_last3, 1)

    def test_future_only_prior_weeks(self):
        upcoming = pd.DataFrame([
            dict(season=2026,week=3,gameId=3,team="A",opponent="B"),
            dict(season=2026,week=3,gameId=3,team="B",opponent="A"),
        ])
        future = build_current_team_features(self.games, upcoming)
        a = future.loc[future.team=="A"].iloc[0]
        self.assertEqual(a.priorGames,2)
        self.assertAlmostEqual(a.adv_offEPA_last3,0.25)
        schedule = pd.DataFrame([dict(season=2026,week=3,gameId=3,homeTeam="A",awayTeam="B")])
        matched = build_matchup_features(schedule, future)
        self.assertAlmostEqual(matched.iloc[0].diff_adv_offEPA_last3, 0.2)

    def test_reject_duplicate_team_game(self):
        with self.assertRaises(ValueError):
            build_pregame_team_features(pd.concat([self.games,self.games.iloc[[0]]]))

    def test_reject_nonreciprocal_game(self):
        bad = self.games.copy()
        bad.loc[bad.team=="B","opponent"] = "C"
        with self.assertRaises(ValueError):
            build_pregame_team_features(bad)

    def test_coverage_report(self):
        p=build_pregame_team_features(self.games)
        report=coverage_report(p)
        self.assertIn("adv_offEPA_last3",set(report.feature))

if __name__ == "__main__":
    unittest.main()
