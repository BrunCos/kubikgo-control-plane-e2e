# Synthetic coding pipeline exercise

This is an intentionally public test fixture containing only invented example
strings and a tiny Python standard-library exercise. It is not a production
product, a company system, or an endorsement of any service. No business data,
credentials, infrastructure configuration, external API, or deployment is needed.

The exercise checks a controlled path from an issue to a feature branch, a pull
request, automated tests, and human review. Nothing here authorizes merging or
deploying code. No license has been selected; public visibility is not a license
grant.

## Baseline

`normalize_label(value)` trims and collapses Unicode whitespace while preserving
letter case. Non-string input raises `TypeError`. The initial `main` branch is
expected to pass all baseline checks; the task in `TASK.md` is an additive change,
not an intentionally failing baseline.

Run from this repository's root with Python 3.12 or newer:

```sh
python3 -I -B -m unittest discover -s . -v
python3 -I -B validator01_syntax.py .
python3 -I -B validator02_behavior.py . baseline
```

The workflow uses one standard GitHub-hosted Ubuntu runner, a five-minute job
limit, read-only repository permissions, and an immutable official checkout action
pin. It does not reference stored secrets, upload artifacts, use caches, install
dependencies, deploy, or write back to GitHub. Only checkout needs network access;
the test code itself does not use the network. The hosted runner is not claimed
to be a network-isolation boundary.

The pin is `actions/checkout` v7.0.1, commit
`3d3c42e5aac5ba805825da76410c181273ba90b1`, checked against the official
[release](https://github.com/actions/checkout/releases/tag/v7.0.1) and
[commit](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1).

## Independent task validators

An operator can copy the three `validator*.py` scripts and
`immutable-files.sha256` into a separate, trusted, read-only validator bundle
before giving an agent its workspace. Pin and verify that bundle's digest. Do not
run the workspace's mutable copies as trusted validators.

The fixed validation commands for the completed task are:

```text
python3 -I -B TRUSTED/validator03_scope.py WORKSPACE TRUSTED/immutable-files.sha256
python3 -I -B TRUSTED/validator01_syntax.py WORKSPACE
python3 -I -B TRUSTED/validator02_behavior.py WORKSPACE task
```

These independently check syntax/module shape, behavioral acceptance, and exact
one-file change scope. The behavior validator executes candidate Python and must
run inside the approved execution sandbox without credentials or network access.
None of the validators is a replacement for that sandbox or human review.

CI is additional visible evidence, not a substitute for the trusted validators.
The task-phase behavior gate must fail while `normalize_labels` is absent from
the baseline. Keep validator/workflow changes outside the agent's task allowance.
