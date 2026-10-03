"""Stress-test the guard: clean outputs must pass, realistic corrupted outputs must be rejected.

Each corruption mimics a way a language model silently alters Arabic text while "only adding diacritics".
"""

import json
import random
import time

from _common import RESULTS, read_lines
from diacritics_guard import check, strip
from diacritics_guard.chars import ARABIC_LETTERS, DIACRITICS, HARAKAT, SHADDA, SUKUN, split_units

rng = random.Random(42)
LETTERS = sorted(ARABIC_LETTERS)


def join(units):
    return "".join(b + m for b, m in units)


def pick(units, cond):
    idx = [i for i, u in enumerate(units) if cond(u)]
    return rng.choice(idx) if idx else None


def replace_base(units, cond, new):
    i = pick(units, cond)
    if i is None:
        return None
    units[i][0] = new(units[i][0])
    return join(units)


def insert_after(units, cond, text):
    i = pick(units, cond)
    if i is None:
        return None
    units.insert(i + 1, [text, ""])
    return join(units)


def drop_word(units):
    words = join(units).split(" ")
    if len(words) < 2:
        return None
    del words[rng.randrange(len(words))]
    return " ".join(words)


def delete_char(units):
    i = pick(units, lambda u: True)
    if i is None:
        return None
    del units[i]
    return join(units)


def diacritic_on_space(units):
    i = pick(units, lambda u: u[0] == " ")
    if i is None:
        return None
    units[i][1] = rng.choice(sorted(HARAKAT))
    return join(units)


def double_haraka(units):
    i = pick(units, lambda u: u[0] in ARABIC_LETTERS and len(u[1]) == 1 and u[1] in HARAKAT)
    if i is None:
        return None
    units[i][1] += rng.choice(sorted(HARAKAT - {units[i][1]}))
    return join(units)


def is_letter(u):
    return u[0] in ARABIC_LETTERS


# name -> (corrupt(units) -> output or None if not applicable, expected violation kind)
CORRUPTIONS = {
    "letter_substitution": (lambda u: replace_base(u, is_letter, lambda b: rng.choice([x for x in LETTERS if x != b])), "base_text_changed"),
    "hamza_normalisation": (lambda u: replace_base(u, lambda x: x[0] in "أإآ", lambda b: "ا"), "base_text_changed"),
    "ya_alef_maqsura_swap": (lambda u: replace_base(u, lambda x: x[0] in "يى", lambda b: "ى" if b == "ي" else "ي"), "base_text_changed"),
    "ta_marbuta_to_ha": (lambda u: replace_base(u, lambda x: x[0] == "ة", lambda b: "ه"), "base_text_changed"),
    "character_deleted": (delete_char, "base_text_changed"),
    "character_inserted": (lambda u: insert_after(u, lambda x: True, rng.choice(LETTERS)), "base_text_changed"),
    "word_dropped": (drop_word, "base_text_changed"),
    "whitespace_changed": (lambda u: replace_base(u, lambda x: x[0] == " ", lambda b: "  "), "base_text_changed"),
    "tatweel_inserted": (lambda u: insert_after(u, is_letter, "ـ"), "base_text_changed"),
    "zero_width_inserted": (lambda u: insert_after(u, is_letter, rng.choice("‌‍")), "base_text_changed"),
    "arabic_punctuation_latinised": (lambda u: replace_base(u, lambda x: x[0] in "،؛؟", lambda b: {"،": ",", "؛": ";", "؟": "?"}[b]), "base_text_changed"),
    "diacritic_on_space": (diacritic_on_space, "diacritic_on_non_letter"),
    "two_harakat_on_one_letter": (double_haraka, "invalid_combination"),
}


def partial_source(units):
    """Keep the gold diacritics on every third unit to simulate a partly diacritized input."""
    return join([[b, m if i % 3 == 0 else ""] for i, (b, m) in enumerate(units)])


def change_existing(units):
    """Change a haraka that the (partly diacritized) source already had."""
    idx = [i for i, (b, m) in enumerate(units) if i % 3 == 0 and b in ARABIC_LETTERS and set(m) & HARAKAT]
    if not idx:
        return None
    i = rng.choice(idx)
    marks = units[i][1]
    old = next(c for c in marks if c in HARAKAT)
    choices = HARAKAT - {old} - ({SUKUN} if SHADDA in marks else set())
    units[i][1] = marks.replace(old, rng.choice(sorted(choices)))
    return join(units)


gold = [g for g in read_lines("test") if g and g[0] not in DIACRITICS]
stats = {name: {"applicable": 0, "rejected": 0, "correct_kind": 0} for name in [*CORRUPTIONS, "existing_diacritic_changed"]}
clean = {"checked": 0, "false_rejections": 0}
calls, elapsed = 0, 0.0


def run(source, output):
    global calls, elapsed
    t = time.perf_counter()
    r = check(source, output)
    elapsed += time.perf_counter() - t
    calls += 1
    return r


for g in gold:
    units = split_units(g)
    plain, partial = strip(g), partial_source(units)
    for src in (plain, partial):  # clean outputs must always pass
        clean["checked"] += 1
        clean["false_rejections"] += not run(src, g).ok
    jobs = [(name, plain, fn, kind) for name, (fn, kind) in CORRUPTIONS.items()]
    jobs.append(("existing_diacritic_changed", partial, change_existing, "existing_diacritic_changed"))
    for name, src, fn, kind in jobs:
        out = fn([u[:] for u in units])
        if out is None or out == g:
            continue
        r = run(src, out)
        s = stats[name]
        s["applicable"] += 1
        s["rejected"] += not r.ok
        s["correct_kind"] += any(v.kind == kind for v in r.violations)

for s in stats.values():
    s["rejection_rate"] = round(100 * s["rejected"] / max(1, s["applicable"]), 2)
total = {k: sum(s[k] for s in stats.values()) for k in ("applicable", "rejected", "correct_kind")}
results = {
    "dataset": "Tashkeela benchmark (Fadel et al., 2019) - test split",
    "lines": len(gold),
    "clean_outputs": clean,
    "corrupted_outputs": total,
    "by_corruption": stats,
    "mean_microseconds_per_check": round(1e6 * elapsed / calls, 1),
}
RESULTS.mkdir(exist_ok=True)
(RESULTS / "guard_stress.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

print(f"clean outputs: {clean['checked']:,} checked, {clean['false_rejections']} falsely rejected")
print(f"corrupted outputs: {total['applicable']:,} generated, {total['rejected']:,} rejected, {total['correct_kind']:,} with the expected violation type")
for name, s in stats.items():
    print(f"  {name:32}{s['applicable']:>6}  rejected {s['rejection_rate']:6.2f}%")
print(f"mean check time: {results['mean_microseconds_per_check']} us/line   saved results/guard_stress.json")
