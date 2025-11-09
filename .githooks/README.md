# Git Hooks

This directory contains git hooks that maintain code quality for this project.

## Installation

To install the hooks, run from the repository root:

```bash
# On Unix/Mac/Linux:
bash .githooks/install-hooks.sh

# On Windows (Git Bash or WSL):
bash .githooks/install-hooks.sh

# Or manually copy the hooks:
cp .githooks/pre-commit .git/hooks/pre-commit
cp .githooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

## Hooks Overview

### pre-commit

Runs automatically before each commit. Checks:
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking

The hook will:
1. Format your code automatically
2. Re-stage the formatted files
3. Fail the commit if type checking fails

### pre-push

Runs automatically before each push. Checks:
- **pytest**: Full test suite (72 tests)

The hook will prevent pushing if any tests fail.

## Bypassing Hooks

If you need to bypass the hooks (not recommended):

```bash
# Skip pre-commit hook
git commit --no-verify

# Skip pre-push hook
git push --no-verify
```

## Manual Testing

You can manually run the checks:

```bash
# Run formatting
python -m black *.py tests/*.py
python -m isort *.py tests/*.py

# Run type checking
python -m mypy *.py tests/*.py --ignore-missing-imports

# Run tests
python -m pytest tests/ -v
```

## Why Git Hooks?

Git hooks help maintain code quality by:
- Catching formatting issues before they reach CI
- Preventing type errors from being committed
- Ensuring all tests pass before pushing
- Maintaining consistent code style across contributors
- Saving time by catching issues locally

## Troubleshooting

**Hook not running:**
- Make sure you ran the install script
- Check that hooks are executable: `ls -la .git/hooks/pre-commit`
- Verify you're in the git repository

**Hook failing:**
- Read the error message carefully
- Run the failing command manually to debug
- Make sure you have the required tools installed (`black`, `isort`, `mypy`, `pytest`)

**Need to update hooks:**
- Edit the files in `.githooks/` directory
- Run the install script again to copy updated hooks
