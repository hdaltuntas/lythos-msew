"""The two languages stay complete and in step."""
import re

from lythosmsew.i18n import ENTRIES, TRANSLATIONS, t
from lythosmsew.web.strings import REUSED, SHELL


def test_every_entry_has_both_languages():
    for key, pair in ENTRIES.items():
        assert isinstance(pair, tuple) and len(pair) == 2, key
        assert pair[0] and pair[1], key


def test_the_placeholders_are_the_same_in_both_languages():
    for key, (en, tr) in ENTRIES.items():
        assert set(re.findall(r"\{(\w+)", en)) == set(re.findall(r"\{(\w+)", tr)), key


def test_the_shell_reuses_only_keys_that_exist():
    for key in REUSED:
        assert key in TRANSLATIONS["en"], key
    for key, pair in SHELL.items():
        assert len(pair) == 2 and all(pair), key


def test_an_unknown_key_comes_back_as_itself():
    assert t("en", "no_such_key") == "no_such_key"


def test_a_parameter_that_is_a_key_is_translated():
    assert t("tr", "err_gamma", soil="soil_foundation").startswith("Temel zemini")


def test_turkish_is_actually_turkish():
    assert t("tr", "res_title") == "DONATILI ZEMİN DUVAR SONUÇLARI"


def test_every_key_the_program_asks_for_exists():
    """The keys spelled out in the source — t(…), L["…"], MSEWError("…") — are all there."""
    import os

    import lythosmsew
    root = os.path.dirname(lythosmsew.__file__)
    pattern = re.compile(r'(?:MSEWError|_message)\("(\w+)"|(?<![A-Za-z_])L\["(\w+)"\]')
    missing = set()
    for folder, _, files in os.walk(root):
        for name in files:
            if name.endswith(".py") and name not in ("i18n.py",):
                text = open(os.path.join(folder, name), encoding="utf-8").read()
                for match in pattern.finditer(text):
                    key = match.group(1) or match.group(2)
                    if key not in TRANSLATIONS["en"]:
                        missing.add(key)
    assert not missing, missing
