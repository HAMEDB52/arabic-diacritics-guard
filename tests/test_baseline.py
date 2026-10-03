from diacritics_guard import FrequencyDiacritizer, check, strip

TRAIN = ["كَتَبَ الْوَلَدُ الدَّرْسَ", "قَرَأَ الْوَلَدُ الْكِتَابَ", "كَتَبَ الطَّالِبُ"]


def test_learns_seen_words_and_preserves_text():
    model = FrequencyDiacritizer().fit(TRAIN)
    src = "كتب الولد، الدرس  الجديد!"  # punctuation, double space and an unseen word
    out = model.diacritize(src)
    assert check(src, out).ok
    assert strip(out) == src
    assert out.startswith("كَتَبَ الْوَلَدُ")
