import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT))


def read_lines(name: str) -> list[str]:
    path = DATA / f"{name}.txt"
    if not path.exists():
        sys.exit(f"{path} not found - run: python scripts/download_data.py")
    return path.read_text(encoding="utf-8").splitlines()
