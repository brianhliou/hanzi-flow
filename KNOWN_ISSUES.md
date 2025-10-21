# Known Issues

## Practice Page

### Subtle layout shift when transitioning between sentences
**Status:** Low priority - rare and subtle

**Description:**
When moving to a new sentence on the practice page, there's occasionally a subtle visual shift where the previous line's characters appear to shift toward the center. This happens rarely and is hard to reproduce consistently.

**Suspected cause:**
The interaction between:
- `text-center` alignment on the sentence container
- `inline-flex` grouping with `whiteSpace: nowrap` for punctuation grouping
- Different wrapping patterns between sentences

When a character + punctuation group wraps to the next line (e.g., `蓝"。`), the previous line becomes shorter and re-centers, creating a subtle alignment shift.

**Impact:**
Slightly jarring but ignorable. Does not affect functionality.

**Next steps:**
- Need to identify specific sentence pairs that trigger this
- Investigate layout computation timing during sentence transitions
- Consider if font rendering/measurement plays a role

**Related code:**
- `/app/app/practice/page.tsx` lines 44-55 (punctuation detection)
- `/app/app/practice/page.tsx` lines 437-548 (rendering with grouping logic)
