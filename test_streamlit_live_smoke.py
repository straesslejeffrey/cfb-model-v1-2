"""Streamlit AppTest smoke test: execute entire app with real checked-in research data."""
import unittest
from streamlit.testing.v1 import AppTest

class StreamlitPreviewSmokeTest(unittest.TestCase):
 def test_default_and_research_selection(self):
  app=AppTest.from_file("app.py",default_timeout=30).run()
  errors=[str(e.message) for e in app.exception]
  self.assertFalse(errors,errors)
  labels=[s.label for s in app.sidebar.selectbox]
  self.assertIn("Model",labels)
  select=next(s for s in app.sidebar.selectbox if s.label=="Model")
  self.assertEqual(select.value,"V1.2 (production)")
  select.set_value("V1.2 Advanced (research preview)").run()
  errors=[str(e.message) for e in app.exception]
  self.assertFalse(errors,errors)

if __name__=="__main__":unittest.main()
