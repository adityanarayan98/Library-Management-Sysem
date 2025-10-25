# Easy Steps to Push Code to GitHub

1. **Check Repository Status**
   - Run: `git status`
   - This shows if there are changes to commit or if everything is clean.

2. **Add Changes (if any)**
   - Run: `git add .`
   - This stages all modified and new files for commit.

3. **Commit Changes**
   - Run: `git commit -m "Describe your changes"`
   - Replace "Describe your changes" with a short message about what you did.

4. **Fetch Remote Updates**
   - Run: `git fetch origin`
   - This gets the latest info from GitHub without changing your files.

5. **Push to GitHub**
   - Run: `git push origin main`
   - If it says "rejected" because of differences:
     - Option 1: Merge changes - `git pull origin main` (fix conflicts if needed), then push again.
     - Option 2: Force push (overwrites GitHub) - `git push origin main --force` (be careful!)

6. **Check Success**
   - Visit your GitHub repo to see the new files.
   - Run `git status` again to confirm.

**Tips:**
- Use .gitignore to skip files like __pycache__ or big executables.
- For files over 50 MB, use Git LFS.
- Always commit before pushing!
