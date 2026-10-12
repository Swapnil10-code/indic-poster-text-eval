"""Reproduce every number in the report from the anonymised ratings.

Usage (from the repo root):  python analysis/compute_results.py
Needs: pandas
"""
import pandas as pd
pd.set_option("display.width", 160)

R = pd.read_csv("data/ratings.csv")            # one row per rater x poster
V = pd.read_csv("data/best_poster_votes.csv")  # one row per rater x poster set
MODELS = ["Gemini 3.1 Flash Image Preview", "GPT Image 1", "Gemini 2.5 Flash Image"]

def summary(r, v):
    rows = []
    for m in MODELS:
        x = r[r.model == m]
        rows.append({
            "model": m,
            "ratings": len(x),
            "text_exactly_correct": (x.text == "Exactly correct").mean(),
            "text_wrong": (x.text == "Wrong / unreadable").mean(),
            "would_post_as_is": (x.post == "Yes").mean(),
            "picked_best": (v.winner == m).mean(),
        })
    return pd.DataFrame(rows).set_index("model").round(3)

print(f"Raters: {R.rater.nunique()} | ratings: {len(R)} | best-poster votes: {len(V)}\n")
print("== Overall ==");  print(summary(R, V), "\n")
for lang in ["Hindi", "Bengali"]:
    print(f"== {lang} ==");  print(summary(R[R.lang == lang], V[V.lang == lang]), "\n")
for tier in ["Easy", "Medium", "Hard"]:
    print(f"== {tier} (text exactly correct) ==")
    print(summary(R[R.tier == tier], V[V.tier == tier])["text_exactly_correct"], "\n")

# Text accuracy as a gate: would raters post posters they judged wrong?
print("Would post | rater said exactly correct:", round((R[R.text == "Exactly correct"].post == "Yes").mean(), 3))
print("Would post | rater said wrong/unreadable:", round((R[R.text == "Wrong / unreadable"].post == "Yes").mean(), 3), "\n")

# Rater reliability against the author's letter-by-letter audit (column `audit`)
print("Rater agreement with audit:", round((R.text == R.audit).mean(), 3))
print(R.assign(agree=R.text == R.audit).groupby("lang").agree.mean().round(3))
