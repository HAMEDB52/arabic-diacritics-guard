"""Arabic character sets shared by the guard, the baseline and the metrics."""

FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
FATHA, DAMMA, KASRA, SHADDA, SUKUN = "َ", "ُ", "ِ", "ّ", "ْ"

HARAKAT = frozenset({FATHA, FATHATAN, DAMMA, DAMMATAN, KASRA, KASRATAN, SUKUN})
DIACRITICS = HARAKAT | {SHADDA}

# U+0621..U+063A and U+0641..U+064A: the 36 letters used by the Tashkeela benchmark.
ARABIC_LETTERS = frozenset(map(chr, [*range(0x0621, 0x063B), *range(0x0641, 0x064B)]))

# A letter carries nothing, one haraka, shadda alone, or shadda + one non-sukun haraka.
VALID_MARKS = frozenset(
    {frozenset()}
    | {frozenset({h}) for h in HARAKAT}
    | {frozenset({SHADDA})}
    | {frozenset({SHADDA, h}) for h in HARAKAT - {SUKUN}}
)


def strip(text: str) -> str:
    """Remove all diacritics, leave every other code point untouched."""
    return "".join(c for c in text if c not in DIACRITICS)


def split_units(text: str) -> list[list[str]]:
    """Split text into [base_char, diacritics] pairs. Diacritics before the first base char are dropped."""
    units: list[list[str]] = []
    for c in text:
        if c not in DIACRITICS:
            units.append([c, ""])
        elif units:
            units[-1][1] += c
    return units
