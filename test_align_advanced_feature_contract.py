import unittest
import pandas as pd
from align_advanced_feature_contract import current_features, historical_features, feature_contract

class FeatureContractTests(unittest.TestCase):
 def setUp(self):
  self.data={"teamA":"Visitor","teamB":"Host","homeTeam":"Host","awayTeam":"Visitor","season":2026,"week":7}
  for metric in set(m for _,m,_ in feature_contract()):
   for window in (3,5):
    self.data[f"teamA_2026_{metric}_last{window}"]=1.
    self.data[f"teamB_2026_{metric}_last{window}"]=2.
 def test_reverse_orientation(self):
  result=current_features(pd.DataFrame([self.data]))
  self.assertEqual(result["home_offSuccessRate_last3"].iloc[0],2.)
  self.assertEqual(result["away_offSuccessRate_last3"].iloc[0],1.)
  self.assertEqual(len(result.columns),56)
 def test_explicit_identity_mandatory(self):
  df=pd.DataFrame([self.data]).drop(columns=["homeTeam","awayTeam"])
  with self.assertRaisesRegex(ValueError,"explicit"):current_features(df)
 def test_bad_team_mapping(self):
  df=pd.DataFrame([dict(self.data,homeTeam="Other")])
  with self.assertRaisesRegex(ValueError,"disagree"):current_features(df)
 def test_historical_columns(self):
  history={"homeTeam":"Host","awayTeam":"Visitor","season":2025,"week":7}
  for side,metric,window in feature_contract():
   history[f"{side}_pregame_{metric}_L{window}"]=3.
  result=historical_features(pd.DataFrame([history]))
  self.assertEqual(len(result.columns),56)
if __name__=="__main__":unittest.main()
