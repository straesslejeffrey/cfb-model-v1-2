"""Fitted 2025-only research residual model. Never promote without independent validation."""
import base64,zlib,json
import numpy as np
import pandas as pd
METRICS=("offPointsPerDrive","defPointsPerDriveAllowed","offPPAperPlay",
 "defPPAperPlayAllowed","offSuccessRate","defSuccessRateAllowed",
 "offScoringOpportunityRate","defScoringOpportunityRateAllowed",
 "offExplosiveDriveRate","defExplosiveDriveRateAllowed",
 "offTurnoverDriveRate","defTurnoverDriveRateForced",
 "offPointsPerScoringOpportunity","defPointsPerScoringOpportunityAllowed")
def symmetric_features(frame):
    result={}
    for metric in METRICS:
        for n in (3,5):
            a=pd.to_numeric(frame[f"teamA_2026_{metric}_last{n}"],errors="coerce")
            b=pd.to_numeric(frame[f"teamB_2026_{metric}_last{n}"],errors="coerce")
            result[f"{metric}_{n}_sum"]=a+b
            result[f"{metric}_{n}_absdiff"]=(a-b).abs()
    return pd.DataFrame(result,index=frame.index)
COMPRESSED="eNo1VlmSXEkIu1C5gi1ZzuKY-19jhCi3PzqbByQIofTfv_GNfo5_H_mWv46Xn_i-qdGutan3WMMmNWXisGWV-KyfIDhtY1Max8BJSrrenkzzSe5X6RcdipN2vpfz-QMj7nq9fvJeZ56tc96G6Bu33jTVKoqy8DU7nRbrV2cRMUsWHzNVZzOW7uiLxclL8c6PoriGo21-HXPptU2EBu8U0UraUHozVu2luq9NwlydfoMuZtseg3XzyRQcaPI0aXYtBYe1Ral5nZsfErC9xxP8-pDQUZRC20MO52XAwZzIOsbCSfHC56F9UTOWzB4hAWD6uzmaP7N_IVAIWPGnP_Vtefo443mOgRZsqM2dtzZaNP_vA4JgwP5Y3sCYbhh84ZqIRaBfS5ouGczsqdGW28nHv1PtM5wZOIHhE4IMy421tAqWoJoYOG0eJYhdMjwgw84NyMezM66NnkjkyaY6rG7S7eAGp98Tj3RF4-lMUzZiQaC2evZUhp4P8mzcMzvpRsLZCPVyxBxL3IeECBVSdKYxV7I6HjrYy2DSm6AaOM11AaHlKPeUpYEo2kckROkx5I2SNao-jzTLEJfwYw1GdbOOBZzl6r-bQEIsJzkhQxJipdqGXi_rwJYl4TEHyZANvACSYiR3G7a3GViEDRTHHwNWpLeY7PqoJXZG14YFAXJEYbe8QRX92nhh9D-oZRQxhoZ-ujE-_RZgaEu9HxSJca9JBT0eFIbZbIsOvN6cRDTkYiMcG2p2ULwIKgQ2OuMARWJX2nAtVQgpUD9PwAtAEZUC9zjNXRl-lfRS_613zU9wgMCcH_hJ2smLXRNeNrlysV_rxwmtijzqCJhyjJkerD8rgABROLQDxp9b3xVP06hN0tg00-Mf5shS8Pv4rDHLbdoABeFGr1hXlgeF6znet9f5oWJE_xQUskybQ9fmMpdQQyEpFr-dAf_ZmuAXNEe_i06-0xXoDkDGbN0gXLR5DsJhwyr-rmgsAIpYP-hAatPPos3AFlmRBf3fcT7q4ICyzOO24LVJ5crDy-W2H8L_zoi1dmIEUcbSbQjoBwzZSUHyWay7Qphu6IDh35AyIZ1_9o165QQYChNgBY0QGwyXT9jMMpBVQE9-Uh8gEPfNnhx02EGgyHcNVeFNoKrtdwx-jb7qsgjsAp2e74pgCOuIpWmy1aHYeC2vQ3C4ru2OVes7Qu1-k4G21mlC1o-lvqO5AfbBg4cO7xqLgDh45GlrCJ7L_CezpkdZjCvpCshxPL3Dg3GdYdzP6jqDRvov3FM4b13mv6sSj3yyEGDfdXoO9UEqHrGjQfWASOK5LGYH947_4B5gcEZnBmcW2HGiz_8MDBj0x6BCs9L-3_9uMru0"
def experimental_total(frame):
    data=json.loads(zlib.decompress(base64.urlsafe_b64decode(COMPRESSED)).decode())
    median,mean,scale,coef,intercept=data
    features=symmetric_features(frame).to_numpy(dtype=float)
    med=np.asarray(median); avg=np.asarray(mean); dev=np.asarray(scale); weights=np.asarray(coef)
    if features.shape[1]!=len(weights): raise ValueError("Incompatible feature count")
    x=np.where(np.isfinite(features),features,med)
    correction=((x-avg)/dev)@weights+intercept
    return pd.to_numeric(frame["predictedTotal"],errors="raise").to_numpy()+correction
