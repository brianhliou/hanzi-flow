#!/usr/bin/env python3
"""
Shared pinyin conversion utilities.

This module provides tone mark ↔ tone number conversion for cases where
external data sources use different pinyin formats than our internal format.

INTERNAL FORMAT (preferred):
- Character reference data: Dual-format storage (pinyins_tone3 + pinyins_display)
- No conversion needed within our pipeline

EXTERNAL SOURCES (require conversion):
- Unihan database: Uses tone marks (yī, hǎo, ma)
- OpenAI API: Returns tone marks
- Legacy data: May use mixed formats

USAGE:
    from scripts.utils.pinyin_conversion import tone_marks_to_tone3

    # Convert external data
    pinyin = "yī"
    tone3 = tone_marks_to_tone3(pinyin)  # Returns "yi1"
"""

# Tone mark to (base, tone_number) mapping
# Covers all standard Mandarin tone marks including ü (v)
TONE_MARK_MAP = {
    # First tone (macron: ā)
    'ā': ('a', 1), 'ē': ('e', 1), 'ī': ('i', 1), 'ō': ('o', 1), 'ū': ('u', 1), 'ǖ': ('v', 1),
    # Second tone (acute: á)
    'á': ('a', 2), 'é': ('e', 2), 'í': ('i', 2), 'ó': ('o', 2), 'ú': ('u', 2), 'ǘ': ('v', 2),
    # Third tone (caron: ǎ)
    'ǎ': ('a', 3), 'ě': ('e', 3), 'ǐ': ('i', 3), 'ǒ': ('o', 3), 'ǔ': ('u', 3), 'ǚ': ('v', 3),
    # Fourth tone (grave: à)
    'à': ('a', 4), 'è': ('e', 4), 'ì': ('i', 4), 'ò': ('o', 4), 'ù': ('u', 4), 'ǜ': ('v', 4),
    # Neutral tone ü (no tone mark)
    'ü': ('v', 0),
}


def tone_marks_to_tone3(pinyin: str) -> str:
    """
    Convert pinyin with tone marks to tone3 format (tone numbers).

    Tone marks are replaced with base letters, tone number appended at end.
    Neutral tones (no marks) get no number suffix.

    Examples:
        'yī' -> 'yi1'
        'hǎo' -> 'hao3'
        'nǚ' -> 'nv3'
        'ma' -> 'ma' (neutral tone, no number)
        'de' -> 'de' (neutral tone, no number)

    Args:
        pinyin: Pinyin string with tone marks (e.g., 'nǐ', 'hǎo')

    Returns:
        Pinyin string with tone numbers (e.g., 'ni3', 'hao3')

    Notes:
        - ü is converted to v for ASCII compatibility
        - Neutral tones have no tone number suffix (not 0)
        - Input is processed character by character
    """
    if not pinyin:
        return ''

    result = []
    tone_number = 0  # 0 = neutral tone (no suffix)

    for char in pinyin.lower():
        if char in TONE_MARK_MAP:
            base_char, tone = TONE_MARK_MAP[char]
            result.append(base_char)
            if tone > 0:  # Only update if not neutral
                tone_number = tone
        else:
            result.append(char)

    # Append tone number only if not neutral (tone 0)
    base = ''.join(result)
    return base if tone_number == 0 else f"{base}{tone_number}"


def tone_marks_to_tone3_with_zero(pinyin: str) -> str:
    """
    Convert pinyin with tone marks to tone3 format, using '0' for neutral tones.

    Similar to tone_marks_to_tone3(), but neutral tones get explicit '0' suffix.
    Useful for systems that require explicit neutral tone markers (e.g., AWS Polly).

    Examples:
        'yī' -> 'yi1'
        'hǎo' -> 'hao3'
        'ma' -> 'ma0' (neutral tone, explicit 0)
        'de' -> 'de0' (neutral tone, explicit 0)

    Args:
        pinyin: Pinyin string with tone marks

    Returns:
        Pinyin string with tone numbers including '0' for neutral

    Notes:
        - Most systems prefer no suffix for neutral tones (use tone_marks_to_tone3)
        - AWS Polly TTS requires explicit '0' for neutral tones
    """
    if not pinyin:
        return ''

    result = []
    tone_number = 0

    for char in pinyin.lower():
        if char in TONE_MARK_MAP:
            base_char, tone = TONE_MARK_MAP[char]
            result.append(base_char)
            if tone > 0:
                tone_number = tone
        else:
            result.append(char)

    base = ''.join(result)
    return f"{base}{tone_number}"  # Always append, even for 0


def strip_tone_number(pinyin: str) -> str:
    """
    Remove tone number from pinyin, leaving only base syllable.

    Examples:
        'yi1' -> 'yi'
        'hao3' -> 'hao'
        'ma' -> 'ma'

    Args:
        pinyin: Pinyin string (with or without tone number)

    Returns:
        Base syllable without tone number

    Notes:
        - Useful for comparing syllables ignoring tones
        - Removes trailing digits only
    """
    if not pinyin:
        return ''

    # Remove trailing digit(s)
    import re
    return re.sub(r'\d+$', '', pinyin)


def normalize_pinyin_for_comparison(pinyin: str) -> str:
    """
    Normalize pinyin for comparison by removing tone information.

    Handles both tone marks and tone numbers. Useful for comparing
    whether two pinyin strings represent the same syllable regardless of tone.

    Examples:
        'yī' -> 'yi'
        'yi1' -> 'yi'
        'hǎo' -> 'hao'
        'hao3' -> 'hao'

    Args:
        pinyin: Pinyin in any format

    Returns:
        Base syllable without tone (lowercase)

    Notes:
        - First converts tone marks to tone3 if present
        - Then strips tone numbers
        - Result is lowercase base syllable
    """
    if not pinyin:
        return ''

    # Convert tone marks to tone3 (if any)
    tone3 = tone_marks_to_tone3(pinyin)

    # Strip tone numbers
    base = strip_tone_number(tone3)

    return base.lower().strip()
