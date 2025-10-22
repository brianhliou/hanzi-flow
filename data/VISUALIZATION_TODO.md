# Visualization Improvements TODO

## Part 1: Fix Existing Visualizations

### 1.1 Character Frequency Distribution ✅ DONE
**File:** `scripts/character_set/analyze_frequency.py`
**Output:** `data/character_set/frequency_distribution.png`

**Completed:**
- ✅ Make character counts dynamic (not hardcoded "5,002")
- ✅ Verify output path is correct (`data/character_set/` not `data/`)
- ✅ Add better subtitle explaining what the plots show
- ✅ Added coverage milestones for 500, 1000, 2000 characters

**Final state:** Dual-plot showing log scale + linear top 2000. Reference lines (100, 1000 occurrences) and coverage annotation included.

---

### 1.2 HSK Sentence Distribution ✅ DONE
**File:** `scripts/sentences/classify_sentence_hsk.py`
**Output:** `data/sentences/hsk_distribution.png`

**Completed:**
- ✅ Add percentage labels alongside counts
- ✅ Add subtitle with total sentence count
- ✅ Better explain "7-9" grouping in legend
- ✅ Add color legend explaining categories
- ✅ Remove "null" category from chart (mentioned in subtitle)
- ✅ Fixed y-axis limit to 18,000 for proper spacing

**Final state:** Clean bar chart with counts, percentages, legend, and proper headroom.

---

### 1.3 HSK Distribution Comparison (SKIP)
**File:** `scripts/sentences/analyze_hsk_coverage.py`
**Output:** `data/sentences/hsk_distribution_comparison.png`

**Decision:** This was a one-time analysis for the "beyond-hsk" category decision. Already made the decision, so no need to polish this visualization.

---

## Part 2: New Visualizations to Create

### 2.1 Sentence Length Distribution ✅ DONE
**Files:**
- `scripts/sentences/analyze_sentence_length.py` (by HSK level)
- `scripts/sentences/analyze_overall_sentence_length.py` (overall)

**Outputs:**
- `data/sentences/sentence_length_distribution.png` (violin plots by HSK)
- `data/sentences/overall_sentence_length_distribution.png` (histogram)

**Completed:**
- ✅ Violin plots showing distribution by HSK level (cleaner than box plots)
- ✅ Shows content difficulty progression (6.6 chars at HSK 1 → 12.6 at beyond-HSK)
- ✅ Median indicators clearly visible
- ✅ Frequent horizontal grid lines (every 25 chars)
- ✅ Statistics box on left side
- ✅ Overall histogram showing aggregate pattern (peak at 8-9 chars)
- ✅ Character count is Chinese characters only (no punctuation/English/numbers)

**Why:** Demonstrates that higher HSK levels have progressively longer/more complex sentences.

---

### 2.2 Character Coverage Curve ✅ DONE
**File:** `scripts/character_set/analyze_coverage_curve.py`
**Output:** `data/character_set/character_coverage_curve.png`

**Completed:**
- ✅ X-axis: Number of characters learned (ranked by frequency)
- ✅ Y-axis: % of corpus text covered
- ✅ Milestone markers (500, 1000, 2000, 3000 chars) all positioned below curve
- ✅ Overlay official HSK cumulative boundaries (300, 600, 900, 1200, 1500, 1800, 3000)
- ✅ All HSK labels vertically aligned at top
- ✅ HSK 4-6 lines made more visible with red color
- ✅ Key insights box moved to right side
- ✅ Green zone showing optimal learning efficiency (80-95%)
- ✅ Clear subtitle explaining character-level coverage

**Final state:** HIGH IMPACT visualization showing 1000 chars = 90.7% coverage with official HSK boundaries.

---

### 2.3 Vocabulary Growth by HSK Level ✅ DONE
**File:** `scripts/character_set/analyze_vocabulary_growth.py`
**Output:** `data/character_set/vocabulary_growth_by_hsk.png`

**Completed:**
- ✅ Bar chart showing characters introduced at each HSK level
- ✅ Cumulative line overlay showing total vocabulary
- ✅ Shows learning progression from HSK 1 → 9 → Beyond HSK
- ✅ Annotate counts on bars and cumulative line
- ✅ Uses official HSK 3.0 counts (not analyzed from data)
- ✅ Color-coded matching other visualizations

**Final state:** Shows official HSK 3.0 curriculum structure (3000 official + 1000 beyond = 4000 total).

---

### 2.4 Script Distribution (Simplified vs Traditional vs Neutral vs Ambiguous) ✅ DONE
**File:** `scripts/sentences/analyze_script_distribution.py`
**Output:** `data/sentences/script_distribution.png`

**Completed:**
- ✅ Bar chart showing sentence counts by script type
- ✅ Categories: Simplified (42.6%), Traditional (41.7%), Neutral (15.6%), Ambiguous (0.2%)
- ✅ Percentages labeled on bars
- ✅ Removed pie chart for cleaner single-view layout
- ✅ Fixed y-axis limit to 40,000 for proper spacing
- ✅ Proper spacing between title, subtitle, and footer
- ✅ Note explaining classification logic

**Final state:** Clean bar chart demonstrating balanced multi-script support.

---

### 2.5 Data Pipeline Flowchart (Optional - Manual Creation)
**Tool:** draw.io, Excalidraw, or matplotlib
**Output:** `data/data_pipeline_diagram.png`

**Features:**
- [ ] Visual flowchart: Data sources → Processing scripts → Production JSON
- [ ] Boxes for: Tatoeba, CC-CEDICT, HSK lists, OpenAI translations
- [ ] Arrows showing data flow
- [ ] File formats labeled at each stage

**Why:** Great for README and portfolio. Shows data engineering rigor.

---

### 2.6 NSS Algorithm Visualization (Advanced - Optional)
**Proposed file:** `scripts/visualization/visualize_nss_algorithm.py`
**Output:** `data/nss_algorithm_demo.png`

**Features:**
- [ ] Sample sentence queue with difficulty scores displayed
- [ ] Color-coded by unknown character count (green=easy, yellow=target, red=hard)
- [ ] Shows how algorithm balances new vs review
- [ ] Annotated with scoring factors (base gain, novelty, k-penalty)

**Why:** Demonstrates technical sophistication. Explains the core adaptive learning algorithm.

---

## Priority Order

1. **✅ Fix character frequency viz** (DONE)
2. **✅ Fix HSK distribution viz** (DONE)
3. **✅ Create character coverage curve** (DONE - HIGH IMPACT)
4. **✅ Create script distribution chart** (DONE)
5. **✅ Create vocabulary growth chart** (DONE)
6. **✅ Create sentence length distribution** (DONE - both by-HSK and overall)
7. Create data pipeline diagram (optional - manual, 1 hour)
8. Create NSS algorithm viz (optional - advanced, 2+ hours)

## Summary

**Completed 6 core visualizations:**
1. Character Frequency Distribution (dual log/linear plots)
2. HSK Sentence Distribution (bar chart)
3. Character Coverage Curve (power law demonstration)
4. Script Distribution (Simplified/Traditional/Neutral/Ambiguous)
5. HSK Vocabulary Growth (official curriculum)
6. Sentence Length Distribution (violin plots + histogram)

All visualizations use consistent styling, clear labels, proper spacing, and are ready for portfolio/documentation use!

---

## Notes

- All visualizations should use consistent styling (colors, fonts, DPI=150)
- Save as high-res PNG (150 DPI minimum) for portfolio use
- Consider creating a `scripts/visualization/` folder for reusable plotting utilities
- Add all new scripts to `.gitignore` if they create temporary files
- Document how to regenerate each visualization in script docstrings
