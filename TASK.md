# Proposed issue: add stable batch label normalization

Implement `normalize_labels(values: list[str]) -> list[str]` in
`src/task_intake.py`, after `normalize_label`. Change no other file.

Acceptance criteria:

1. Require a list containing only strings; otherwise raise `TypeError`.
2. Normalize each item with the existing `normalize_label` behavior.
3. Omit normalized empty strings.
4. Remove duplicates using `str.casefold()` equality, retaining the first
   normalized spelling and the input's original order.
5. Return a new list; never mutate the caller's input.
6. Keep all existing `normalize_label` behavior unchanged.
7. Use only Python built-ins, without imports, network, filesystem access,
   dependencies, module-level side effects, or unrelated changes.

Examples (all synthetic):

```text
[" Alpha ", "alpha", "BETA", " beta ", " "] -> ["Alpha", "BETA"]
["Straße", "STRASSE", "Omega"] -> ["Straße", "Omega"]
["delta", "Alpha", "beta"] -> ["delta", "Alpha", "beta"]
[] -> []
```

Run the baseline tests and all three trusted task validators. Deliver one feature
branch and one pull request with test evidence. Do not merge or deploy. No API,
account credential, external data, or production access is required for this task.
