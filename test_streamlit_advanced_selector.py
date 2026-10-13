import ast
import unittest
from pathlib import Path

class StreamlitAdvancedSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=Path("app.py").read_text()
        ast.parse(cls.code)
    def test_production_is_default(self):
        self.assertIn('selected_model = st.sidebar.selectbox("Model", MODEL_OPTIONS, index=0)',self.code)
        self.assertIn('"V1.2 (production)"',self.code)
    def test_candidate_is_clearly_experimental(self):
        self.assertIn('"V1.2 Advanced (research preview)"',self.code)
        self.assertIn('expanded=selected_model == MODEL_OPTIONS[1]',self.code)
        self.assertIn("experimental_total(research_frame)",self.code)
        self.assertIn("not a default score",self.code)
if __name__=="__main__": unittest.main()
