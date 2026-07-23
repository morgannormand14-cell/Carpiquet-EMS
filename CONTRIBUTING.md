# Contributing to Carpiquet EMS

Thank you for helping improve Carpiquet EMS.

## Workflow

1. Open or reference an issue.
2. Create a focused branch.
3. Add or update documentation.
4. Add tests for behaviour changes.
5. Open a pull request against `develop`.

## Branches

- `main`: released versions
- `develop`: integration branch
- `feature/<name>`: new functionality
- `fix/<name>`: non-urgent correction
- `hotfix/<name>`: urgent released-version fix
- `docs/<name>`: documentation only

## Conventional Commits

Examples:

```text
feat(dashboard): add health overview
fix(simulation): correct deadband handling
docs(spec): add EMS-011 stale data rule
test(algorithm): cover minimum SOC protection
chore(release): prepare v0.3.0-alpha
```

## Pull Request Requirements

- clear description;
- linked rule, RFC or issue where applicable;
- no unrelated changes;
- tests passing;
- documentation updated;
- simulation safety preserved.

## Coding Principles

- small modules;
- descriptive names;
- pure core calculations where practical;
- Home Assistant APIs isolated from the core;
- no real-control behaviour without explicit safety review.
