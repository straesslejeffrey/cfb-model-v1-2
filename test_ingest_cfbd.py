import unittest
from ingest_cfbd import normalize_rows

class CFBDIngestionTests(unittest.TestCase):
    def test_normalize_reciprocal_games_and_keep_ppa_separate(self):
        base = lambda team, opponent: dict(
            season=2026,week=1,gameId=101,team=team,opponent=opponent,
            offense={"ppa":0.2,"successRate":0.43,"lineYards":3.1,
                "rushingPlays":{"ppa":0.1,"explosiveness":1.2},
                "passingPlays":{"ppa":0.3,"explosiveness":1.5}},
            defense={"ppa":-0.1,"successRate":0.39,"lineYards":2.7})
        havoc = lambda team, opponent: dict(
            season=2026,week=1,gameId=101,team=team,opponent=opponent,
            offense={"havoc":{"total":0.12}},
            defense={"havoc":{"total":0.19,"frontSeven":0.1,"db":0.09}})
        df = normalize_rows([base("A","B"),base("B","A")],
                            [havoc("A","B"),havoc("B","A")])
        self.assertEqual(len(df),2)
        self.assertEqual(df.loc[df.team=="A","offPPA"].iloc[0],0.2)
        self.assertEqual(df.loc[df.team=="A","defHavocCreated"].iloc[0],0.19)
        self.assertEqual(df.loc[df.team=="A","frontSevenHavoc"].iloc[0],0.1)
        self.assertNotIn("offEPA",df.columns)

    def test_reject_missing_opponent(self):
        record = dict(season=2026,week=1,gameId=22,team="A",opponent="B",
                      offense={"ppa":0.3},defense={})
        with self.assertRaises(ValueError):
            normalize_rows([record],[])

if __name__ == "__main__":
    unittest.main()
