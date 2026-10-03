from diacritics_guard import der, wer

GOLD = ["كَتَبَ الْوَلَدُ"]


def test_perfect_prediction_scores_zero():
    assert der(GOLD, GOLD) == 0 and wer(GOLD, GOLD) == 0


def test_single_case_ending_error():
    pred = ["كَتَبَ الْوَلَدَ"]  # only the final letter of the second word differs
    assert der(GOLD, pred) == round(100 * 1 / 8, 2)  # 8 letters, 1 wrong
    assert wer(GOLD, pred) == 50.0  # 1 of 2 words wrong
    assert der(GOLD, pred, case_ending=False) == 0  # word-final letters are excluded
    assert wer(GOLD, pred, case_ending=False) == 0


def test_shadda_pair_order_is_one_class():
    assert der(["رَبَّ"], ["رَبَّ".replace("بَّ", "بَّ")]) == 0


def test_missing_diacritics_count_as_errors():
    # 8 letters, 7 carry a diacritic in gold (the alef of "al-" carries none)
    assert der(GOLD, ["كتب الولد"]) == 87.5
    assert der(GOLD, ["كتب الولد"], no_diacritic=False) == 100.0  # undiacritized gold letters excluded
