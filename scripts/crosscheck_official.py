"""Score results/test_pred.txt with the benchmark's own evaluation script and compare to ours.

Downloads helpers/diacritization_stat.py from the benchmark repository, checks its SHA-256,
and calls its functions directly (its constants are passed in as lists, so no pickles are loaded).
"""

import functools
import hashlib
import importlib.util
import urllib.request

from _common import DATA, RESULTS, ROOT, read_lines
from diacritics_guard import report
from diacritics_guard.chars import ARABIC_LETTERS, DAMMA, DAMMATAN, FATHA, FATHATAN, KASRA, KASRATAN, SHADDA, SUKUN

URL = "https://raw.githubusercontent.com/AliOsm/arabic-text-diacritization/master/helpers/diacritization_stat.py"
SHA256 = "535b729c349965bfcb6863fc65c06a5465d3b900128ce19ce135998620e32fc8"
SINGLES = [FATHA, FATHATAN, DAMMA, DAMMATAN, KASRA, KASRATAN, SUKUN, SHADDA]
CLASSES = SINGLES + [SHADDA + h for h in SINGLES[:6]]

path = ROOT / "data" / "diacritization_stat.py"
if not path.exists():
    urllib.request.urlretrieve(URL, path)
if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
    raise SystemExit(f"{path}: unexpected checksum")
spec = importlib.util.spec_from_file_location("official", path)
official = importlib.util.module_from_spec(spec)
spec.loader.exec_module(official)
official.open = functools.partial(open, encoding="utf-8")  # the reference relies on the platform default

gold_file, pred_file = DATA / "test.txt", RESULTS / "test_pred.txt"
ours = report(read_lines("test"), pred_file.read_text(encoding="utf-8").splitlines())
letters = sorted(ARABIC_LETTERS)
grid = {
    "with_case_ending": {},
    "without_case_ending": {"case_ending": False},
    "with_case_ending_excl_no_diacritic": {"no_diacritic": False},
    "without_case_ending_excl_no_diacritic": {"case_ending": False, "no_diacritic": False},
}
mismatches = 0
for metric, fn in (("DER", official.calculate_der), ("WER", official.calculate_wer)):
    for name, kw in grid.items():
        ref = fn(str(gold_file), str(pred_file), letters, CLASSES, "Fadel", **kw)
        same = ref == ours[metric][name]
        mismatches += not same
        print(f"{metric} {name:40} official {ref:6.2f}   ours {ours[metric][name]:6.2f}   {'match' if same else 'MISMATCH'}")
print("all 8 numbers match the official script" if not mismatches else f"{mismatches} mismatches")
raise SystemExit(mismatches)
