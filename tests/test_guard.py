import pytest

from diacritics_guard import check

SRC = "قال الولد، ثم ذهب إلى المدرسة؟"
GOOD = "قَالَ الْوَلَدُ، ثُمَّ ذَهَبَ إِلَى الْمَدْرَسَةِ؟"


def kinds(source, output):
    return {v.kind for v in check(source, output).violations}


def test_clean_output_passes():
    assert check(SRC, GOOD).ok
    assert check(SRC, SRC).ok  # adding nothing is allowed


def test_shadda_order_does_not_matter():
    fatha_first, shadda_first = "ر\u064eب\u064e\u0651", "ر\u064eب\u0651\u064e"
    assert check("رب", fatha_first).ok and check("رب", shadda_first).ok
    assert check("رب\u0651", fatha_first).ok  # source shadda kept, fatha added


@pytest.mark.parametrize(
    "output",
    [
        GOOD.replace("إِ", "ا"),  # hamza normalised
        GOOD.replace("إِلَى", "إِلَي"),  # alef maqsura -> ya
        GOOD.replace("ةِ", "هِ"),  # ta marbuta -> ha
        GOOD.replace("الْوَلَدُ", "الْوَلَـدُ"),  # tatweel
        GOOD.replace(" ثُمَّ", " ‌ثُمَّ"),  # zero-width non-joiner
        GOOD.replace("،", ","),  # punctuation latinised
        GOOD.replace(" ", "  ", 1),  # whitespace changed
        GOOD.replace(" ثُمَّ", ""),  # word dropped
    ],
)
def test_base_text_changes_are_rejected(output):
    assert kinds(SRC, output) == {"base_text_changed"}


def test_diacritic_on_non_letter_is_rejected():
    assert kinds(SRC, GOOD.replace(" ", " َ", 1)) == {"diacritic_on_non_letter"}
    assert kinds(SRC, GOOD.replace("،", "،ُ")) == {"diacritic_on_non_letter"}
    assert kinds("ب", "َب") == {"diacritic_on_non_letter"}


@pytest.mark.parametrize("marks", ["َُ", "ّْ", "ََ", "ّّ"])
def test_invalid_combinations_are_rejected(marks):
    assert kinds("ب", "ب" + marks) == {"invalid_combination"}


def test_existing_diacritics_must_be_kept():
    assert check("كتب", "كَتَبَ").ok
    assert check("كَتب", "كَتَبَ").ok  # keeps the source fatha, adds the rest
    assert check("كّتب", "كَّتَبَ").ok  # shadda kept, fatha added on the same letter
    assert kinds("كَتب", "كُتِبَ") == {"existing_diacritic_changed"}
    assert kinds("كَتب", "كتَبَ") == {"existing_diacritic_changed"}  # removed


def test_violation_reports_position():
    v = check(SRC, GOOD.replace("إِ", "ا")).violations[0]
    assert v.index == SRC.index("إ")
