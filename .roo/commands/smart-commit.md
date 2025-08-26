# Smart Commit

## Goal
1. Analyze which files have been changed in the Git repository.
2. Generate a commit message automatically based on those changes.
3. Stage all changes and perform the commit with the generated message.

## Commit Message Convention
Follow the Conventional Commits style, which is widely adopted in open-source projects.

Format:
<type>(<scope>): <short description>

- type: one of feat, fix, docs, style, refactor, test, chore, build, ci
- scope: optional, usually the main directory or module affected
- short description: concise summary of the change

## Examples
feat(auth): add password reset endpoint
fix(ui): correct button alignment in navbar
docs(readme): update installation instructions

## Behavior
- Inspect the list of changed files (staged or unstaged) to understand the nature of changes.
- Infer the type from the nature of changes (new feature, bug fix, docs update, tests, etc.).
- Infer the scope from the top-level directory or key module touched.
- Compose a short, conventional commit message in the specified format.
- Stage all modified and new files.
- Execute: git commit -m "<generated message>".
