---
name: project-wizard
description: Interactive project scaffolding wizard. Asks about type, stack, features, then generates structure, tooling, CLAUDE.md, and git init.
requires:
  bins:
    - git
# Context cost: ~144 lines (~2.5K tokens)
---

# Project Wizard Skill

## Trigger
Activated when asked to:
- "Set up a new project"
- "Initialize a project"
- "Create a project from scratch"
- "Start a new app/application"
- "Bootstrap a project"

## Purpose
Interactive project setup wizard that:
1. Asks clarifying questions about the project
2. Scaffolds the appropriate template
3. Configures all tooling automatically
4. Sets up Claude Code integration
5. Creates project-specific CLAUDE.md

## Wizard Flow

### Step 1: Project Type Discovery
Ask the user:
```
What type of project are you building?

1. 🌐 Web Frontend (React, Vue, Svelte)
2. 🔧 Backend API (Python, Node, Go)
3. 📱 Full-Stack App (Frontend + Backend)
4. 🖥️  CLI Tool (Command-line application)
5. 🧩 Browser Extension (Chrome/Firefox)
6. 📦 Library/Package (Reusable module)
7. 🤖 Other (I'll describe it)
```

### Step 2: Technology Stack
Based on project type, ask about:
- **Frontend**: React/Vue/Svelte, TypeScript?, Styling (Tailwind/CSS/Styled)
- **Backend**: Python/Node/Go/Rust, Framework, Database
- **Testing**: Jest/Vitest/Pytest, E2E (Playwright/Cypress)
- **Deployment**: Docker?, CI/CD platform

### Step 3: Project Details
```
Project name: _______________
Description: _______________
Git repository: (Y/n)
License: MIT/Apache/GPL/None
```

### Step 4: Features Selection
```
Select features to include:

□ Authentication (JWT/OAuth)
□ Database integration
□ API documentation (OpenAPI/Swagger)
□ Docker configuration
□ CI/CD pipeline (GitHub Actions)
□ Pre-commit hooks
□ Quality gates
□ VS Code settings
```

### Step 5: Execute Setup
Run the following in sequence:

1. **Scaffold Project**
   - Use appropriate `/new/*` template
   - Create directory structure
   - Initialize package manager

2. **Configure Tooling**
   - ESLint/Prettier or Ruff
   - TypeScript/type hints
   - Testing framework
   - Run `/auto/setup-hooks`

3. **Set Up Quality Gates**
   - Configure `/gate/security` thresholds
   - Configure `/gate/coverage` targets
   - Configure `/gate/performance` limits

4. **Create Claude Integration**
   - Generate project-specific `CLAUDE.md`
   - Create `.claudeignore`
   - Set up `.claude/hooks.json`
   - Create project decisions log

5. **Initialize Git**
   - `git init`
   - Create `.gitignore`
   - Initial commit

6. **Final Setup**
   - Install dependencies
   - Run initial build/test
   - Open in editor (optional)

## Generated CLAUDE.md Template
```markdown
# {Project Name}

## Quick Reference
- **Stack:** {technologies}
- **Package Manager:** {npm/yarn/pip/cargo}
- **Dev Server:** `{dev command}`
- **Test Command:** `{test command}`
- **Build Command:** `{build command}`

## Architecture
{Generated based on project type}

## Development Workflow
1. Start dev server: `{command}`
2. Run tests: `{command}`
3. Create commit: `/git/commit`
4. Quality check: `/gate/all`

## Project Decisions
See `.claude/decisions/` for ADRs.

## Team Conventions
- {Generated based on choices}
```

## Output
After completion, display:
```
✅ PROJECT SETUP COMPLETE!
==========================

📁 Created: {project-name}/
📦 Installed: {package count} dependencies
🔧 Configured: {tools list}
📋 Quality gates: Active
🪝 Git hooks: Installed

Next steps:
  cd {project-name}
  {dev command}

Happy coding! 🚀
```
