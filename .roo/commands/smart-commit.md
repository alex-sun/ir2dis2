Perform a Git commit with an **AI-generated Conventional Commit message**.

Behavior:
1. Inspect which files have changed in the repository.  
2. Based on the changes, generate a commit message that follows the Conventional Commits format:  
   <type>(<scope>): <short description>  
   - type: feat, fix, docs, style, refactor, test, chore, build, ci  
   - scope: optional, usually the top-level directory or module affected  
   - short description: concise summary of the change  
3. Stage all modified and new files with `git add .`.  
4. Run `git commit -m "<generated message>"`.  
