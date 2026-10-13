"""Conservative promotion gate for experimental V1.2 Advanced totals."""
import argparse
import json
from pathlib import Path

def decide(report, minimum_gain=.10):
    gain=float(report["gain"])
    lower,upper=map(float,report["bootstrap_95pct_interval_for_gain"])
    weekly=report["by_week"]
    cross=report.get("independent_cross_season_passed") is True
    passed=(gain>=minimum_gain and lower>0 and
            all(float(w["candidate_mae"])<=float(w["baseline_mae"]) for w in weekly)
            and cross)
    return {"promote":bool(passed),"status":"APPROVED" if passed else "RESEARCH_ONLY",
            "checks":{"minimum_gain_met":gain>=minimum_gain,
                      "bootstrap_lower_bound_positive":lower>0,
                      "no_worsening_heldout_week":all(float(w["candidate_mae"])<=float(w["baseline_mae"]) for w in weekly),
                      "independent_cross_season_passed":cross}}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--audit",required=True)
    p.add_argument("--output",default="advanced_promotion_decision.json")
    a=p.parse_args()
    decision=decide(json.loads(Path(a.audit).read_text()))
    Path(a.output).write_text(json.dumps(decision,indent=2))
    print(json.dumps(decision,indent=2))
    if not decision["promote"]: raise SystemExit(2)
