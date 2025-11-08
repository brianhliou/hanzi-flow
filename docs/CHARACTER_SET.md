# Chinese Hanzi Coverage in Unicode

## Overview
This directory aims to be a **complete database of all Chinese Hanzi (漢字)** — including common, rare, and historical forms — as defined in the Unicode Standard.  
Unicode encodes Han characters in a shared framework called **Han unification**, which merges identical characters across Chinese, Japanese, Korean, and Vietnamese traditions.

Because of this, Chinese Hanzi are **not stored in a single contiguous block**, but distributed across multiple *CJK Unified Ideograph* blocks and their extensions.  
This README explains which blocks to include, which to exclude, and how to separate Chinese-specific characters from pan-CJK data.

---

## 1. What “Han Unification” Means
Unicode treats all Han-derived writing systems (Hanzi, Kanji, Hanja, Chu Nôm) as part of one unified script.  
- When two regions use a character with **identical shape and meaning**, Unicode assigns **one shared code point**.  
- When shapes or semantics differ, each form receives its **own code point**.  
- Therefore, the “CJK Unified Ideographs” set includes characters from **all** East Asian traditions.

### Implication
There is **no pure Chinese-only block** in Unicode.  
To isolate Chinese Hanzi, you must later filter using metadata from the **Unihan Database** (see Section 4).

---

## 2. Unicode Blocks Containing True Han Ideographs

Include **only these** blocks to cover every authentic Han character (both simplified and traditional).

Blocks are listed in **strict codepoint order** (not alphabetical):

| Block | Range | Approx. Count | Plane | Notes |
|-------|--------|----------------|--------|--------|
| CJK Unified Ideographs Extension A | U+3400–U+4DBF | 6,592 | BMP | Additional common forms |
| CJK Unified Ideographs | U+4E00–U+9FFF | 20,992 | BMP | Core modern set |
| CJK Unified Ideographs Extension B | U+20000–U+2A6DF | 42,720 | SIP | Rare & historical |
| CJK Unified Ideographs Extension C | U+2A700–U+2B73F | 4,160 | SIP | More rare ideographs |
| CJK Unified Ideographs Extension D | U+2B740–U+2B81F | 224 | SIP | Urgent additions |
| CJK Unified Ideographs Extension E | U+2B820–U+2CEAF | 5,776 | SIP | Further historical forms |
| CJK Unified Ideographs Extension F | U+2CEB0–U+2EBEF | 7,488 | SIP | Expanded rare set |
| CJK Unified Ideographs Extension I | U+2EBF0–U+2EE5F | 624 | SIP | Added in Unicode 15.1 (2023) |
| CJK Unified Ideographs Extension G | U+30000–U+3134F | 4,944 | TIP | Latest large expansion |
| CJK Unified Ideographs Extension H | U+31350–U+323AF | 4,192 | TIP | Very rare/historical |

### Total
**97,712 assigned characters** as of Unicode 15.1 (10 blocks).

**Note:** Extension J (U+323B0–U+33479, ~4,298 chars) is proposed for Unicode 16 but not yet official. The v1 SOT pipeline excludes it for stability, including only officially released Unicode blocks.

---

## 3. Blocks to Exclude

| Block | Range | Reason to Exclude |
|-------|--------|------------------|
| CJK Compatibility Ideographs | U+F900–U+FAFF | Duplicates for round-trip encoding |
| CJK Compatibility Ideographs Supplement | U+2F800–U+2FA1F | Additional duplicates |
| CJK Radicals Supplement | U+2E80–U+2EFF | Component radicals, not characters |
| Kangxi Radicals | U+2F00–U+2FDF | Radical shapes, not characters |
| CJK Strokes | U+31C0–U+31EF | Stroke components only |
| Ideographic Description Characters | U+2FF0–U+2FFF | Structural markup, not characters |

Including these would contaminate the dataset with non-character symbols or duplicates.

---

## 4. Simplified vs. Traditional Classification

Unicode itself **does not label** characters as simplified or traditional.  
To add that metadata, use the **Unihan Database**, published by the Unicode Consortium. Key fields:

| Field | Meaning |
|--------|----------|
| `kSimplifiedVariant` | Lists the simplified form(s) of a traditional character |
| `kTraditionalVariant` | Lists the traditional form(s) of a simplified character |
| `kIICore` | Identifies inclusion in core regional standards |
| `kIRG_GSource` | Marks characters sourced from China (GB 18030, etc.) |
| `kIRG_TSource`, `kIRG_HSource`, `kIRG_JSource`, etc. | Mark Taiwan, Hong Kong, Japan, etc. sources |
| `kTotalStrokes` | Stroke count (for lookup) |
| `kRSUnicode` | Radical–stroke decomposition |

Combining these fields allows labeling each code point as:
- Simplified-only  
- Traditional-only  
- Shared  
- Regional (TW, HK, JP, KR, VN)  

---

## 5. Unicode Planes Overview

| Plane | Name | Contains |
|--------|------|----------|
| Plane 0 (BMP) | Basic Multilingual Plane | Main + Extension A |
| Plane 2 (SIP) | Supplementary Ideographic Plane | Extensions B–F, I |
| Plane 3 (TIP) | Tertiary Ideographic Plane | Extensions G–H |
| Plane 10 | Proposed for Unicode 16 | Extension J |

---

## 6. Recommended Implementation Steps

1. **Collect all code points** from the 11 Unified Ideograph ranges.  
2. **Download Unihan.zip** from [https://www.unicode.org/Public/UNIDATA/Unihan.zip](https://www.unicode.org/Public/UNIDATA/Unihan.zip).  
3. **Parse relevant fields** for language and variant tagging.  
4. **Filter** by `kIRG_GSource` and `kSimplifiedVariant` / `kTraditionalVariant` for Chinese focus.  
5. Optionally add **stroke count, pronunciation (pinyin), and frequency** data from external corpora.  

---

## 7. Data Scale and Practical Notes

- Total characters: ≈ 97,000+  
- Typical modern use: ≤ 3,000 (HSK 1–9 ≈ 3,263)  
- Most rare extensions contain archaic, place-name, or variant forms.  
- Database design: each character = 1 record with metadata (Unicode code point, radical, stroke count, variants, region tags).

---

## 8. References

- [Unicode CJK Unified Ideographs](https://en.wikipedia.org/wiki/CJK_Unified_Ideographs)  
- [Unicode Consortium: Unihan Database](https://www.unicode.org/charts/unihan.html)  
- [IRG (Ideographic Rapporteur Group)](https://www.unicode.org/consortium/irg.html)  
- [CJK Unified Ideographs Extensions](https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_Extension)  

---

## 9. Summary

To construct an authoritative dataset of all Chinese Hanzi:
- Include **CJK Unified Ideographs + Extensions A–J**.  
- Exclude compatibility, radical, and stroke blocks.  
- Enrich with **Unihan metadata** to distinguish simplified, traditional, and regional forms.  
- Expect ~97,000 total code points covering the full Chinese written heritage.
