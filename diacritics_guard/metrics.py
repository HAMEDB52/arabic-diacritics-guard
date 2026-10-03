"""DER and WER as defined by the Tashkeela benchmark (Fadel et al., 2019, 'Fadel' style).

Reimplemented from the benchmark's helpers/diacritization_stat.py so results are directly
comparable; scripts/crosscheck_official.py confirms both produce identical numbers.
"""

from __future__ import annotations

from .chars import ARABIC_LETTERS, DIACRITICS, SHADDA, VALID_MARKS

_KEEP = ARABIC_LETTERS | DIACRITICS | {" "}
_PAIRS = {m for m in VALID_MARKS if len(m) == 2}


def _clean(line: str) -> str:
    line = " ".join("".join(c if c in _KEEP else " " for c in line).split())
    for _ in range(2):  # drop diacritics that start a word, twice, as the reference does
        line = "".join(c for i, c in enumerate(line) if c not in DIACRITICS or (i > 0 and line[i - 1] != " "))
    return line


def _classes(text: str, case_ending: bool) -> list:
    """One diacritic class per Arabic letter; None marks a word-final letter when case endings are ignored."""
    out = []
    for i, c in enumerate(text):
        if c not in ARABIC_LETTERS:
            continue
        j = i + 1
        while j < len(text) and text[j] in DIACRITICS:
            j += 1
        if not case_ending and (j == len(text) or text[j].isspace()):
            out.append(None)
            continue
        d = text[i + 1 : j]
        out.append(frozenset(d[:2]) if frozenset(d[:2]) in _PAIRS else frozenset(d[:1]))
    return out


def der(gold: list[str], pred: list[str], case_ending: bool = True, no_diacritic: bool = True) -> float:
    assert len(gold) == len(pred), "gold and prediction differ in lines"
    eq = ne = 0
    for g, p in zip(gold, pred):
        gc, pc = _classes(_clean(g), case_ending), _classes(_clean(p), case_ending)
        assert len(gc) == len(pc), "gold and prediction differ in letters"
        for a, b in zip(gc, pc):
            if (not no_diacritic and a == frozenset()) or (a is None and b is None):
                continue
            eq, ne = eq + (a == b), ne + (a != b)
    return round(100 * ne / max(1, eq + ne), 2)


def wer(gold: list[str], pred: list[str], case_ending: bool = True, no_diacritic: bool = True) -> float:
    assert len(gold) == len(pred), "gold and prediction differ in lines"
    eq = ne = 0
    for g, p in zip(gold, pred):
        gw, pw = _clean(g).split(), _clean(p).split()
        assert len(gw) == len(pw), "gold and prediction differ in words"
        for a_word, b_word in zip(gw, pw):
            gc, pc = _classes(a_word, case_ending), _classes(b_word, case_ending)
            if gc:
                ok = all(a == b or (not no_diacritic and a == frozenset()) for a, b in zip(gc, pc))
                eq, ne = eq + ok, ne + (not ok)
    return round(100 * ne / max(1, eq + ne), 2)


def report(gold: list[str], pred: list[str]) -> dict:
    """The benchmark's standard 2x2 grid for DER and WER."""
    grid = {
        "with_case_ending": dict(case_ending=True),
        "without_case_ending": dict(case_ending=False),
        "with_case_ending_excl_no_diacritic": dict(case_ending=True, no_diacritic=False),
        "without_case_ending_excl_no_diacritic": dict(case_ending=False, no_diacritic=False),
    }
    return {m.__name__.upper(): {k: m(gold, pred, **kw) for k, kw in grid.items()} for m in (der, wer)}
