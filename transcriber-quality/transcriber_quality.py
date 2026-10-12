"""
Detecting low-quality transcribers from data signals (crowdsourced speech transcription).
Usage:  python q2_transcriber_quality.py Data_Check.xlsx
Outputs: user_scorecard.csv, signal_validation.csv
"""
import re, sys, difflib
import numpy as np
import pandas as pd

PATH = sys.argv[1] if len(sys.argv) > 1 else "Data_Check.xlsx"
PUNCT = r"[\s\.,।!?\-'\"’‘“”…]"
TAG = r"\[|blank|ब्लैक|ब्लेंक|ब्लैंक|inaudible|नॉइस"

def norm(s): return re.sub(PUNCT, "", s)
def sim(a, b):
    if not a and not b: return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
def is_loop(s):  # Whisper hallucination: one token >50% of an 8+ word text
    w = s.split()
    return len(w) >= 8 and pd.Series(w).value_counts().iloc[0] / len(w) > 0.5

# ---------- load & features ----------
d = pd.read_excel(PATH)
d["w"] = d.whisper_text.fillna("").astype(str)
d["u"] = d.user_text.fillna("").astype(str)
d["wn"], d["un"] = d.w.map(norm), d.u.map(norm)
d["sim_to_whisper"] = [sim(a, b) for a, b in zip(d.wn, d.un)]
d["listen_ratio"] = d.time_taken_by_user / d.duration          # <1 = faster than the audio
d["unedited"] = d.is_edited.eq("No")
d["whisper_present"] = d.wn.ne("")
d["cosmetic_edit"] = d.is_edited.eq("Yes") & d.wn.eq(d.un) & d.whisper_present
d["is_tag"] = d.u.str.contains(TAG, case=False, regex=True)
d["kept_hallucination"] = d.w.map(is_loop) & d.u.map(is_loop)
d["rubber_stamp_unheard"] = d.unedited & d.whisper_present & (d.listen_ratio < 1)

# Data check: brief says cps = chars / time_taken, data says chars / duration
nchar = d.u.str.replace(r"\s", "", regex=True).str.len()
print("cps matches chars/duration:", round(((nchar / d.duration - d.segment_character_per_second).abs() < .01).mean(), 3))
print("cps matches chars/time_taken:", round(((nchar / d.time_taken_by_user - d.segment_character_per_second).abs() < .01).mean(), 3))

# user_id: only 10 IDs repeat; the rest are one row each -> used as population baseline
counts = d.user_id.value_counts()
d["tracked_user"] = d.user_id.map(counts) > 1

# ---------- validation via peer agreement on clips transcribed by several people ----------
shared = d[d.recording_url.duplicated(keep=False)].copy()
def peer(grp):
    t = grp.un.tolist()
    return pd.Series([np.median([sim(a, c) for j, c in enumerate(t) if j != i]) for i, a in enumerate(t)],
                     index=grp.index)
shared["peer_agreement"] = shared.groupby("recording_url", group_keys=False).apply(peer)
rows = []
for name, mask in {
    "unedited": shared.unedited,
    "faster_than_audio (ratio<1)": shared.listen_ratio < 1,
    "unedited AND faster_than_audio": shared.unedited & (shared.listen_ratio < 1),
    "everything else": ~(shared.unedited & (shared.listen_ratio < 1)),
}.items():
    s = shared[mask]
    rows.append({"signal": name, "rows": len(s),
                 "median_peer_agreement": round(s.peer_agreement.median(), 3),
                 "pct_disagree_with_peers(<0.8)": round((s.peer_agreement < .8).mean(), 3)})
val = pd.DataFrame(rows)
val.to_csv("signal_validation.csv", index=False)
print(f"\nPeer-agreement validation ({shared.recording_url.nunique()} shared clips, {len(shared)} rows)")
print(val.to_string(index=False))

# ---------- per-user scorecard ----------
def card(x):
    xt = x[x.time_taken_by_user < 600]  # drop idle-tab outliers for correlation
    wp = x[x.whisper_present]
    nt = x[~x.is_tag]
    return pd.Series({
        "tasks": len(x),
        "audio_hrs": round(x.duration.sum() / 3600, 3),
        "time_vs_duration_spearman": round(xt[["duration", "time_taken_by_user"]].corr("spearman").iloc[0, 1], 3),
        "pct_faster_than_audio_clips_gt6s": round((x[x.duration > 6].listen_ratio < 1).mean(), 3),
        "pct_unedited_when_whisper_present": round((~wp.is_edited.eq("Yes")).mean(), 3),
        "pct_rubber_stamp_unheard": round(x.rubber_stamp_unheard.mean(), 3),
        "pct_cosmetic_edits": round(x.cosmetic_edit.mean(), 3),
        "pct_cps_gt20_nontag": round((nt.segment_character_per_second > 20).mean(), 3),
        "kept_hallucinations": int(x.kept_hallucination.sum()),
        "distinct_blank_tags": x[x.is_tag].u.str.strip().nunique(),
    })
sc = d[d.tracked_user].groupby("user_id").apply(card)
sc.loc["BASELINE (single-row IDs)"] = card(d[~d.tracked_user])
sc = sc.sort_values("pct_unedited_when_whisper_present", ascending=False)
sc.to_csv("user_scorecard.csv")
print("\nUser scorecard"); print(sc.to_string())
