# Commit Skill - Auto Commit and Deploy

When the user completes a code change, automatically commit and deploy to local Docker.

## Default Behavior

After completing any code modification task:
1. **Commit** - Stage and commit changes with appropriate message
2. **Push** - Push to GitHub remote
3. **Deploy** - Rebuild and restart affected Docker services

## Steps

### 1. Check Status
```bash
git status
git diff --stat
```

### 2. Stage and Commit
- Exclude `.idea/` and other IDE files
- Generate commit message based on changes
- Use conventional commit format

### 3. Push to Remote
```bash
git push github main
```

### 4. Deploy to Docker
```bash
# Rebuild and restart services
docker-compose up -d --build
```

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
- Exclude `.idea/workspace.xml` by default
- Warn if sensitive files are detected

## Smart Deploy

Only rebuild affected services:
- Frontend changes (`novawrite-ai---professional-novel-assistant/`) → rebuild frontend
- Backend changes (`backend/`) → rebuild backend
- AI service changes (`nova-ai-service/`) → rebuild ai-service
- Docker/config changes → rebuild all

## Usage

This skill runs automatically after task completion. Can also be triggered manually:
- `/commit` - Commit, push, and deploy
- `/commit --no-deploy` - Commit and push only
- `/commit --no-push` - Commit only

## Execution Flow

```
1. git status (check changes)
2. git add <files> (exclude .idea/)
3. git commit -m "message"
4. git push github main
5. docker-compose up -d --build
6. docker-compose ps (verify status)
```
