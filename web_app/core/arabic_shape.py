"""Pure-Python Arabic contextual glyph shaping and visual BiDi helper for Matplotlib."""

from __future__ import annotations

import re

# Mapping of base Arabic characters (U+0621..U+064A) to Presentation Forms-B:
# (isolated, final, initial, medial) — None if character does not join to the left.
_ARABIC_FORMS: dict[str, tuple[str, str, str | None, str | None]] = {
    "\u0621": ("\uFE80", "\uFE80", None, None),        # HAMZA
    "\u0622": ("\uFE81", "\uFE82", None, None),        # ALEF WITH MADDA
    "\u0623": ("\uFE83", "\uFE84", None, None),        # ALEF WITH HAMZA ABOVE
    "\u0624": ("\uFE85", "\uFE86", None, None),        # WAW WITH HAMZA
    "\u0625": ("\uFE87", "\uFE88", None, None),        # ALEF WITH HAMZA BELOW
    "\u0626": ("\uFE89", "\uFE8A", "\uFE8B", "\uFE8C"),# YEH WITH HAMZA
    "\u0627": ("\uFE8D", "\uFE8E", None, None),        # ALEF
    "\u0628": ("\uFE8F", "\uFE90", "\uFE91", "\uFE92"),# BEH
    "\u0629": ("\uFE93", "\uFE94", None, None),        # TEH MARBUTA
    "\u062A": ("\uFE95", "\uFE96", "\uFE97", "\uFE98"),# TEH
    "\u062B": ("\uFE99", "\uFE9A", "\uFE9B", "\uFE9C"),# THEH
    "\u062C": ("\uFE9D", "\uFE9E", "\uFE9F", "\uFEA0"),# JEEM
    "\u062D": ("\uFEA1", "\uFEA2", "\uFEA3", "\uFEA4"),# HAH
    "\u062E": ("\uFEA5", "\uFEA6", "\uFEA7", "\uFEA8"),# KHAH
    "\u062F": ("\uFEA9", "\uFEAA", None, None),        # DAL
    "\u0630": ("\uFEAB", "\uFEAC", None, None),        # THAL
    "\u0631": ("\uFEAD", "\uFEAE", None, None),        # REH
    "\u0632": ("\uFEAF", "\uFEB0", None, None),        # ZAIN
    "\u0633": ("\uFEB1", "\uFEB2", "\uFEB3", "\uFEB4"),# SEEN
    "\u0634": ("\uFEB5", "\uFEB6", "\uFEB7", "\uFEB8"),# SHEEN
    "\u0635": ("\uFEB9", "\uFEBA", "\uFEBB", "\uFEBC"),# SAD
    "\u0636": ("\uFEBD", "\uFEBE", "\uFEBF", "\uFEC0"),# DAD
    "\u0637": ("\uFEC1", "\uFEC2", "\uFEC3", "\uFEC4"),# TAH
    "\u0638": ("\uFEC5", "\uFEC6", "\uFEC7", "\uFEC8"),# ZAH
    "\u0639": ("\uFEC9", "\uFECA", "\uFECB", "\uFECC"),# AIN
    "\u063A": ("\uFECD", "\uFECE", "\uFECF", "\uFED0"),# GHAIN
    "\u0640": ("\u0640", "\u0640", "\u0640", "\u0640"),# TATWEEL
    "\u0641": ("\uFED1", "\uFED2", "\uFED3", "\uFED4"),# FEH
    "\u0642": ("\uFED5", "\uFED6", "\uFED7", "\uFED8"),# QAF
    "\u0643": ("\uFED9", "\uFEDA", "\uFEDB", "\uFEDC"),# KAF
    "\u0644": ("\uFEDD", "\uFEDE", "\uFEDF", "\uFEE0"),# LAM
    "\u0645": ("\uFEE1", "\uFEE2", "\uFEE3", "\uFEE4"),# MEEM
    "\u0646": ("\uFEE5", "\uFEE6", "\uFEE7", "\uFEE8"),# NOON
    "\u0647": ("\uFEE9", "\uFEEA", "\uFEEB", "\uFEEC"),# HEH
    "\u0648": ("\uFEED", "\uFEEE", None, None),        # WAW
    "\u0649": ("\uFEEF", "\uFEF0", None, None),        # ALEF MAKSURA
    "\u064A": ("\uFEF1", "\uFEF2", "\uFEF3", "\uFEF4"),# YEH
}

_LAM_ALEF_LIGATURES: dict[str, tuple[str, str]] = {
    "\u0622": ("\uFEF5", "\uFEF6"),  # LAM + ALEF MADDA
    "\u0623": ("\uFEF7", "\uFEF8"),  # LAM + ALEF HAMZA ABOVE
    "\u0625": ("\uFEF9", "\uFEFA"),  # LAM + ALEF HAMZA BELOW
    "\u0627": ("\uFEFB", "\uFEFC"),  # LAM + ALEF
}

_ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF]")
_LATIN_RUN_RE = re.compile(r"[A-Za-z0-9$%€£.,:/\-_()]+")


def _can_join_left(ch: str) -> bool:
    forms = _ARABIC_FORMS.get(ch)
    return bool(forms and forms[2] is not None)


def _is_arabic_letter(ch: str) -> bool:
    return ch in _ARABIC_FORMS


def reshape_arabic(text: str) -> str:
    """Convert logical Arabic characters to connected Presentation Forms-B glyphs."""
    if not text or not _ARABIC_CHAR_RE.search(text):
        return text

    chars = list(text)
    out: list[str] = []
    i = 0
    n = len(chars)

    while i < n:
        ch = chars[i]
        if not _is_arabic_letter(ch):
            out.append(ch)
            i += 1
            continue

        prev_joins = i > 0 and _can_join_left(chars[i - 1])

        # Check Lam-Alef ligature
        if ch == "\u0644" and i + 1 < n and chars[i + 1] in _LAM_ALEF_LIGATURES:
            iso_lig, fin_lig = _LAM_ALEF_LIGATURES[chars[i + 1]]
            out.append(fin_lig if prev_joins else iso_lig)
            i += 2
            continue

        next_joins = i + 1 < n and _is_arabic_letter(chars[i + 1])
        iso, fin, ini, med = _ARABIC_FORMS[ch]

        if prev_joins and next_joins and med is not None:
            out.append(med)
        elif prev_joins and fin is not None:
            out.append(fin)
        elif next_joins and ini is not None:
            out.append(ini)
        else:
            out.append(iso)
        i += 1

    return "".join(out)


def format_arabic_for_matplotlib(text: str) -> str:
    """Reshape Arabic text and convert to visual LTR order for Matplotlib rendering."""
    if not text or not _ARABIC_CHAR_RE.search(text):
        return text

    reshaped = reshape_arabic(text)
    # Tokenize into LTR runs (numbers/Latin/symbols) vs RTL/whitespace runs, then reverse for visual order.
    tokens: list[tuple[bool, str]] = []
    pos = 0
    for match in _LATIN_RUN_RE.finditer(reshaped):
        if match.start() > pos:
            tokens.append((False, reshaped[pos : match.start()]))
        tokens.append((True, match.group(0)))
        pos = match.end()
    if pos < len(reshaped):
        tokens.append((False, reshaped[pos:]))

    visual_parts: list[str] = []
    for is_ltr, chunk in reversed(tokens):
        if is_ltr:
            # Swap parentheses inside LTR chunks if needed, keep token left-to-right
            visual_parts.append(chunk)
        else:
            swapped = chunk.translate(str.maketrans("()[]{}", ")(][}{"))
            visual_parts.append(swapped[::-1])

    return "".join(visual_parts)
