"""Draw the three charts in assets/ from the anonymised ratings.  Usage: python analysis/make_charts.py"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

R = pd.read_csv("data/ratings.csv"); V = pd.read_csv("data/best_poster_votes.csv")
M = ["Gemini 3.1 Flash Image Preview", "GPT Image 1", "Gemini 2.5 Flash Image"]
C = dict(zip(M, ["#2a78d6", "#eb6834", "#1baf7a"]))

def grouped(groups, fn, ylab, out):
    fig, ax = plt.subplots(figsize=(7, 3.3)); x = np.arange(len(groups)); w = 0.26
    for i, m in enumerate(M):
        v = [fn(g, m) * 100 for g, _ in groups]
        bars = ax.bar(x + (i - 1) * w, v, w - 0.02, color=C[m], label=m, zorder=3)
        for b, val in zip(bars, v):
            ax.text(b.get_x() + b.get_width() / 2, val + 1.5, f"{val:.0f}%", ha="center", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels([l for _, l in groups]); ax.set_ylim(0, 112); ax.set_ylabel(ylab)
    ax.yaxis.grid(True, color="#ecebe8", zorder=0); ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.16))
    plt.tight_layout(); plt.savefig(out, dpi=220); plt.close()

sub = lambda g: R if g == "all" else R[R.lang == g]
grouped([("Hindi", "Hindi"), ("Bengali", "Bengali"), ("all", "All ratings")],
        lambda g, m: (sub(g)[sub(g).model == m].text == "Exactly correct").mean(),
        '% rated "Exactly correct"', "assets/chart_exact_by_script.png")
metric = {"exact": lambda m: (R[R.model == m].text == "Exactly correct").mean(),
          "post": lambda m: (R[R.model == m].post == "Yes").mean(),
          "win": lambda m: (V.winner == m).mean()}
grouped([("exact", "Text exactly correct"), ("post", '"Would post as-is"'), ("win", "Picked best overall")],
        lambda g, m: metric[g](m), "% of ratings", "assets/chart_three_measures.png")
print("Charts written to assets/")
