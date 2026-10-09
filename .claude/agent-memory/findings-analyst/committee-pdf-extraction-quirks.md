---
name: committee-pdf-extraction-quirks
description: pdftotext quirks in the WBC committee PDFs (dropped dashes, blank merged cells, shading) and how to quote around them so verify_history.py passes
metadata:
  type: reference
---

Extraction lessons for the committee PDFs (how-to only; no findings here):

- **Plain mode drops line-end dashes in wrapped table cells.** A cell printed "X -" / "Y" across two lines comes out as "X Y" in plain text, while `-layout` keeps "X -" but puts the next column's text between the two halves. Neither mode has the printed "X - Y" in one piece. Fix: put the printed value in the record field (fields aren't checked) and use a fragment that verifies for the `quote`/`cells` (the layout line, or the plain text as extracted).
- **Some first-column cells are blank** in the completed-work tables (school rows under a single "Primary" cell; the follow-up rows under a "Schools Primary" heading row). The PDF image shows them empty, so `service` is null for those rows.
- **Shading and colour carry meaning that text can't show**: appetite levels in the strategy's appetite table, RAG colours in the matrix and band table. Render with `pdftoppm -r 70 -png -f N -l N` and Read the PNG to check. Record only colour words that are printed; a band with a colour but no printed word gets `rag: null`.
- The strategy's PDF page numbers match its printed footers; the covering report is pages 1-4 and Appendix A starts on page 5.
- For iteration, build history.json from a scratchpad Python script and rerun the verifier. Quote layout lines for table rows and plain text for wrapped single cells. Every quote passed on the first run this way.

Related: [[findings-analyst-workflow]]
