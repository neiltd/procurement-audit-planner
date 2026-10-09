---
name: citation-path-brackets
description: build_pack [metric:...] citations cannot take list-index paths like $.cleaning.exclusions[0].rows; {{...}} placeholders can
metadata:
  type: feedback
---

A `[metric:$.a.b[0].c]` citation fails E-CITE (the citation regex stops at the bracket), while the same path works as a `{{$.a.b[0].c|int}}` placeholder. Cite a rule or a dict-path metric for the step's required citation and put list-indexed values in as placeholders.

**Why:** hit when citing the redacted-row exclusion count in analytics.json `cleaning.exclusions`.

**How to apply:** any value under a JSON list in analytics.json goes in as a placeholder, never a citation. See [[prose-figure-traps]].
