"""Train the baseline on the train split, diacritize the test split, guard every output, score DER/WER."""

import json
import time

from _common import RESULTS, read_lines
from diacritics_guard import FrequencyDiacritizer, check, report, strip

train, gold = read_lines("train"), read_lines("test")

t0 = time.perf_counter()
model = FrequencyDiacritizer().fit(train)
t1 = time.perf_counter()
sources = [strip(g) for g in gold]
pred = [model.diacritize(s) for s in sources]
t2 = time.perf_counter()

guard_failures = sum(not check(s, p).ok for s, p in zip(sources, pred))
scores = report(gold, pred)

results = {
    "dataset": "Tashkeela benchmark (Fadel et al., 2019) - test split",
    "test_lines": len(gold),
    "train_lines": len(train),
    "model": "FrequencyDiacritizer (word bigram -> word -> char trigram backoff)",
    "guard_failures_on_model_output": guard_failures,
    "train_seconds": round(t1 - t0, 1),
    "predict_seconds": round(t2 - t1, 1),
    **scores,
}
RESULTS.mkdir(exist_ok=True)
(RESULTS / "baseline.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(RESULTS / "test_pred.txt").write_text("\n".join(pred) + "\n", encoding="utf-8")

print(f"test lines: {len(gold):,}   guard failures on model output: {guard_failures}")
print(f"{'':6}{'with case ending':>20}{'without case ending':>22}")
for m in ("DER", "WER"):
    print(f"{m:6}{scores[m]['with_case_ending']:>19.2f}%{scores[m]['without_case_ending']:>21.2f}%")
print("saved results/baseline.json")
