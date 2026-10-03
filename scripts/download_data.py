"""Download the Tashkeela diacritization benchmark (Fadel et al., 2019; MIT licence) and verify checksums."""

import hashlib
import urllib.request

from _common import DATA

BASE = "https://raw.githubusercontent.com/AliOsm/arabic-text-diacritization/master/dataset/"
SHA256 = {
    "train": "f8ce279b6788f6a4fd756075a087616c36d7803de46e48938e81c7d79cfcfcb5",
    "val": "0fde23882c51fa41248324ff9a5e1cc2a921714389d7c3cba419fd5eeae9c710",
    "test": "4e851ff836f0a178abb15d9f4a8bcf92748b77cc0d67030d9fae2fbe698baa12",
}

DATA.mkdir(exist_ok=True)
for name, digest in SHA256.items():
    path = DATA / f"{name}.txt"
    if not path.exists():
        print(f"downloading {name}.txt ...")
        urllib.request.urlretrieve(BASE + f"{name}.txt", path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        raise SystemExit(f"{path}: checksum mismatch ({actual}); delete it and retry")
    print(f"{name}.txt ok ({len(path.read_text(encoding='utf-8').splitlines()):,} lines)")
