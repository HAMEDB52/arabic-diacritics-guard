"""A counting baseline: word bigram -> word -> character trigram -> character backoff.

It exists to give the evaluation pipeline something real to measure. It is a floor,
not a competitive diacritizer.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Iterable

from .chars import ARABIC_LETTERS, split_units, strip

_WS = re.compile(r"(\s+)")


def _argmax(table: dict) -> dict:
    return {k: c.most_common(1)[0][0] for k, c in table.items()}


class FrequencyDiacritizer:
    def fit(self, lines: Iterable[str]) -> "FrequencyDiacritizer":
        bi, uni, tri, one = (defaultdict(Counter) for _ in range(4))
        for line in lines:
            prev = "<s>"
            for word in line.split():
                plain = strip(word)
                bi[prev, plain][word] += 1
                uni[plain][word] += 1
                prev = plain
                units = split_units(word)
                chars = [" ", *(b for b, _ in units), " "]
                for j, (b, marks) in enumerate(units, 1):
                    if b in ARABIC_LETTERS:
                        tri[chars[j - 1], b, chars[j + 1]][marks] += 1
                        one[b][marks] += 1
        self.bi, self.uni, self.tri, self.one = map(_argmax, (bi, uni, tri, one))
        return self

    def _by_chars(self, word: str) -> str:
        chars = [" ", *word, " "]
        return "".join(
            c + (self.tri.get((chars[j - 1], c, chars[j + 1])) or self.one.get(c, "") if c in ARABIC_LETTERS else "")
            for j, c in enumerate(word, 1)
        )

    def diacritize(self, text: str) -> str:
        """Diacritize undiacritized text. Whitespace and non-Arabic characters are preserved exactly."""
        parts, prev = _WS.split(strip(text)), "<s>"
        for i, tok in enumerate(parts):
            if tok and not tok.isspace():
                parts[i] = self.bi.get((prev, tok)) or self.uni.get(tok) or self._by_chars(tok)
                prev = tok
        return "".join(parts)
