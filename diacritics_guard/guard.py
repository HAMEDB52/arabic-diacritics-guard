"""Verify that a diacritizer only *added* diacritics and changed nothing else."""

from __future__ import annotations

from dataclasses import dataclass, field

from .chars import ARABIC_LETTERS, DIACRITICS, VALID_MARKS, split_units, strip


@dataclass(frozen=True)
class Violation:
    kind: str  # base_text_changed | diacritic_on_non_letter | invalid_combination | existing_diacritic_changed
    index: int  # position in the undiacritized text
    detail: str


@dataclass
class GuardResult:
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


def _leading(text: str) -> str:
    return text[: len(text) - len(text.lstrip("".join(DIACRITICS)))]


def check(source: str, output: str) -> GuardResult:
    """Return every way `output` differs from `source` other than added diacritics on Arabic letters.

    Rules:
      1. With diacritics removed, output must equal source byte-for-byte (no normalisation).
      2. Diacritics may only sit on Arabic letters.
      3. Each letter's marks must be a valid combination (e.g. no two harakat, no shadda+sukun).
      4. Diacritics already present in the source must be kept.
    """
    res = GuardResult()
    src, out = strip(source), strip(output)
    if src != out:
        i = next((k for k, (a, b) in enumerate(zip(src, out)) if a != b), min(len(src), len(out)))
        res.violations.append(Violation("base_text_changed", i, f"expected {src[i:i + 15]!r}, got {out[i:i + 15]!r}"))
        return res

    if _leading(output) != _leading(source):
        res.violations.append(Violation("diacritic_on_non_letter", 0, "diacritic before the first character"))

    for i, ((base, s_marks), (_, o_marks)) in enumerate(zip(split_units(source), split_units(output))):
        if o_marks == s_marks:
            continue
        if base not in ARABIC_LETTERS:
            res.violations.append(Violation("diacritic_on_non_letter", i, f"{base!r} got {o_marks!r}"))
        elif len(set(o_marks)) != len(o_marks) or frozenset(o_marks) not in VALID_MARKS:
            res.violations.append(Violation("invalid_combination", i, f"{base!r} got {o_marks!r}"))
        elif not set(s_marks) <= set(o_marks):
            res.violations.append(Violation("existing_diacritic_changed", i, f"{base!r} had {s_marks!r}, got {o_marks!r}"))
    return res
