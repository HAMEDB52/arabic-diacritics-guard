# arabic-diacritics-guard

Guarantee that an Arabic diacritizer — a language model or a trained model — **only added diacritics** and changed nothing else in the text, and measure how good those diacritics are.

Language models asked to "add tashkeel" often alter the text itself: they normalise hamza (`إلى` becomes `الى`), swap ya and alef maqsura, insert tatweel or zero-width characters, or latinise punctuation. These edits are invisible at a glance and corrupt the source. The guard rejects every one of them and reports where it happened.

## Results

All numbers below are produced by the scripts in this repository on the 2,500-line **test split of the Tashkeela benchmark** ([Fadel et al., 2019](https://arxiv.org/abs/1905.01965)).

**Guard**

| | Count | Result |
|---|---:|---|
| Correct outputs checked | 5,000 | **0 falsely rejected** |
| Corrupted outputs (14 failure modes) | 32,804 | **32,804 rejected**, each with the expected violation type |
| Mean check time | | ~120 µs per line, pure Python |

The text-equality rule is an exact comparison, so catching text edits is guaranteed by construction. The stress test exists to document which real failure modes are covered and to show that correct outputs are never rejected.

**Scorer, exercised on a baseline diacritizer**

A counting baseline (word bigram → word → character trigram backoff) trained on the 50,000-line train split:

| | With case ending | Without case ending |
|---|---:|---:|
| DER | 6.13% | 4.05% |
| WER | 16.98% | 7.95% |

All 2,500 baseline outputs passed the guard. The scorer is verified against the benchmark's own evaluation script: `crosscheck_official.py` scores the same predictions with the original `diacritization_stat.py`, and **all 8 DER/WER numbers match exactly**.

The baseline is a floor, not a competitive system. It is here so the evaluation pipeline measures something real; published neural systems on this benchmark are substantially more accurate.

## Reproduce

```bash
pip install -r requirements.txt
python scripts/download_data.py        # 38 MB, SHA-256 verified
python scripts/evaluate.py             # trains the baseline (~40 s on one CPU core), prints DER/WER
python scripts/guard_stress.py         # prints the guard results above (~8 s)
python scripts/crosscheck_official.py  # compares this scorer with the benchmark's official script
python -m pytest                       # 22 unit tests
```

The package uses only the Python standard library (3.9+): no compiled dependencies, no GPU. `pytest` is needed only for the tests. Results are written to `results/`.

## Using the guard

```python
from diacritics_guard import check

source = "ذهب إلى المدرسة"
output = "ذَهَبَ اِلَى الْمَدْرَسَةِ"     # the model normalised the hamza

result = check(source, output)
result.ok             # False
result.violations[0]  # Violation(kind='base_text_changed', index=4, detail="expected 'إلى المدرسة', got 'الى المدرسة'")
```

### Rules

1. **Same text.** With diacritics removed, the output must equal the source code point for code point. No Unicode normalisation is applied, because a normalised character is a changed character.
2. **Diacritics only on Arabic letters** — never on spaces, punctuation, digits or Latin text.
3. **Valid marks per letter:** one haraka, shadda alone, or shadda plus one non-sukun haraka. Shadda may come before or after the haraka.
4. **Existing diacritics are kept.** A partly diacritized source can be completed, but its marks cannot be changed or removed.

Violation kinds: `base_text_changed`, `diacritic_on_non_letter`, `invalid_combination`, `existing_diacritic_changed`. Each carries the position in the undiacritized text and a short snippet.

### Failure modes in the stress test

| Corruption | Example | Lines | Rejected |
|---|---|---:|---:|
| Letter substitution | any letter replaced | 2,500 | 100% |
| Hamza normalisation | `أ إ آ` to `ا` | 2,291 | 100% |
| Ya / alef maqsura swap | `ي` ↔ `ى` | 2,376 | 100% |
| Ta marbuta to ha | `ة` to `ه` | 1,811 | 100% |
| Character deleted | | 2,500 | 100% |
| Character inserted | | 2,500 | 100% |
| Word dropped | | 2,498 | 100% |
| Whitespace changed | single → double space | 2,498 | 100% |
| Tatweel inserted | `الولـد` | 2,500 | 100% |
| Zero-width character inserted | U+200C / U+200D | 2,500 | 100% |
| Arabic punctuation latinised | `،` to `,` | 1,332 | 100% |
| Diacritic on a space | | 2,498 | 100% |
| Two harakat on one letter | fatha and damma | 2,500 | 100% |
| Existing diacritic changed | source fatha changed to damma | 2,500 | 100% |

Correct outputs were checked against two sources per line: fully undiacritized, and partly diacritized (every third character keeps its gold marks).

## Metrics

`der` and `wer` follow the benchmark's "Fadel" definitions: text is reduced to the 36 Arabic letters, the 8 diacritics and spaces; each letter gets one diacritic class (none, one of 7 harakat, shadda, or shadda + haraka); "without case ending" excludes the last letter of every word; "excluding no diacritic" skips letters that carry no diacritic in the gold text. `report()` returns the standard 2×2 grid for both metrics.

## Layout

```
diacritics_guard/
  chars.py      character sets, strip(), split_units()
  guard.py      check() and the four rules
  metrics.py    DER / WER
  baseline.py   counting baseline diacritizer
scripts/        download, evaluate, stress test, cross-check against the official scorer
tests/          unit tests for the guard, metrics and baseline
results/        JSON written by the scripts
```

## Data

The Tashkeela benchmark is downloaded at run time from [AliOsm/arabic-text-diacritization](https://github.com/AliOsm/arabic-text-diacritization) (MIT licence) and is not redistributed here.

```bibtex
@inproceedings{fadel2019arabic,
  title     = {Arabic Text Diacritization Using Deep Neural Networks},
  author    = {Fadel, Ali and Tuffaha, Ibraheem and Al-Jawarneh, Bara' and Al-Ayyoub, Mahmoud},
  booktitle = {2019 2nd International Conference on Computer Applications \& Information Security (ICCAIS)},
  year      = {2019}
}
```
