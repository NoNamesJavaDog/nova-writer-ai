# Commit Skill - Auto Commit Code to GitHub

When the user requests to commit code, follow these steps:

## Steps

1. **Check status** - Run `git status` to view all modified files
2. **View changes** - Run `git diff` to see specific changes
3. **Check history** - Run `git log --oneline -5` to understand the project's commit style
4. **Analyze changes** - Generate an appropriate commit message based on the changes
5. **Stage files** - Use `git add` to stage relevant files (default: all changes unless specified)
6. **Commit code** - Create the commit following the project's style

## Commit Message Convention

Use concise descriptions with these prefixes:
- `feat: xxx` - New feature
- `fix: xxx` - Bug fix
- `docs: xxx` - Documentation update
- `refactor: xxx` - Code refactoring
- `style: xxx` - Code formatting
- `test: xxx` - Test related
- `chore: xxx` - Build/tooling related

## Safety Rules

- **DO NOT** commit files containing sensitive information (e.g., `.env`, `credentials.json`)
- **DO NOT** use dangerous options like `--force` or `--no-verify`
- **DO NOT** push to remote automatically unless the user explicitly requests it
- Warn the user if sensitive files are detected in the staging area

## Usage Examples

User input:
- `/commit` - Commit all changes
- `/commit -m "fix: resolve login issue"` - Use specified commit message
- `/commit --push` - Commit and push to remote

## Execution Flow

```
1. git status (check status)
2. git diff (view changes)
3. git log --oneline -5 (check history style)
4. Analyze and generate commit message
5. git add . (or specified files)
6. git commit -m "message"
7. If --push argument provided, execute git push
```
