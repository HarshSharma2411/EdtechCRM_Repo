# EdTech CRM — GitHub Copilot Agents

Custom agents for specialized tasks in the EdTech CRM project.

## Available Agents

### 1. Spell Checker & Typo Detective
**File:** `.github/agents/spell-checker.md`

Scans the codebase for spelling errors, typos, and common misspellings. Reports findings with precise file location, line number, incorrect word, and correction.

**When to use:**
- Check for spelling errors across the project
- Review code quality for typos and misspellings
- Scan specific files for spelling issues

**Example prompts:**
- "Scan the entire project for spelling errors and report them."
- "Check all Python docstrings for typos."
- "Find misspelled words in HTML templates."

---

## How to Use Custom Agents

In GitHub Copilot Chat, reference an agent by its name:
- `@Spell Checker & Typo Detective: scan the project for typos`
- `@Spell Checker & Typo Detective: check comments for misspellings`

Or activate automatically when certain keywords are detected:
- "spell check"
- "find typos"
- "check spelling"
