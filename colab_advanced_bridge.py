"""Run the 2026 V1.2 Advanced data bridge in Colab.

Upload/download the saved 2026 matchup matrix and V1.2 prediction CSV;
install pyarrow; then run:
python colab_advanced_bridge.py --predictions /content/predictions.csv --matrix /content/matrix.parquet --output-dir /content/advanced_out
"""
import argparse
import json
from pathlib import Path
import pandas as pd
from bridge_v13_2026_pregame import add_advanced_context

def run(predictions_file, matrix_file, output_dir):
    predictions=pd.read_csv(predictions_file)
    matrix=pd.read_parquet(matrix_file)
    joined=add_advanced_context(predictions,matrix)
    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    result=output_dir/"v12_advanced_2026_pregame_context.csv"
    joined.to_csv(result,index=False)
    status=output_dir/"v12_advanced_2026_coverage.json"
    report={
        "games":int(len(joined)),
        "identity_matched":int(joined.advanced2026IdentityMatch.sum()),
        "advanced_ready":int(joined.advanced2026Ready.sum()),
        "missing_games":joined.loc[~joined.advanced2026Ready,["season","week","gameId","teamA","teamB"]].to_dict("records"),
        "model_status":"research_only_original_V1_2_scores_unchanged",
    }
    status.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    print("Wrote",result)
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",required=True)
    p.add_argument("--matrix",required=True)
    p.add_argument("--output-dir",default="advanced_output")
    a=p.parse_args()
    run(a.predictions,a.matrix,a.output_dir)
