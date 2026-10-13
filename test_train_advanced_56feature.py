import unittest
import pandas as pd
from align_advanced_feature_contract import feature_contract
from train_advanced_56feature import train

class TrainingContractTests(unittest.TestCase):
    def test_reject_insufficient_or_misaligned(self):
        h={"season":2025,"week":5,"homeTeam":"A","awayTeam":"B","actualTotal":42.,
           "frozenV12Total":40.}
        for side,metric,window in feature_contract():
            h[f"{side}_pregame_{metric}_L{window}"]=.4
        c={"season":2026,"week":7,"teamA":"A","teamB":"B","homeTeam":"A","awayTeam":"B"}
        for metric in {m for _,m,_ in feature_contract()}:
            for w in (3,5):
                c[f"teamA_2026_{metric}_last{w}"]=.4
                c[f"teamB_2026_{metric}_last{w}"]=.3
        with self.assertRaisesRegex(ValueError,"Insufficient split"):
            train(pd.DataFrame([h]),pd.DataFrame([c]),"/tmp/advanced_contract_test")
    def test_reject_nonchronological_split(self):
        with self.assertRaisesRegex(ValueError,"Chronological"):
            train(pd.DataFrame(),pd.DataFrame(),"/tmp/advanced_contract_test",
                  train_end=2025,validation_year=2024,test_year=2023)

if __name__=="__main__":unittest.main()
