# Repository Access Issues - Diagnosis & Solutions

## ✅ FIXED
- Removed build artifacts (build/, dist/, __pycache__/) from Git tracking
- Added proper .gitignore file
- Changes pushed to GitHub

## ⚠️ REMAINING ISSUES

### Issue 1: Repository Size (670 MB)
**Problem:** Repository history contains large files that were previously committed.

**Solutions:**

**Option A: Clean History (Recommended if no other active users)**
```powershell
# WARNING: This rewrites Git history!
# Coordinate with team before running

# Clean large files from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch dist/testhead_gui.exe" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

**Option B: Start Fresh (Easiest)**
1. Create new repository on GitHub
2. Clone fresh copy without history:
   ```powershell
   git clone --depth=1 https://github.com/qsc-josegutierrez/langley_testhead.git langley_testhead_fresh
   cd langley_testhead_fresh
   git remote set-url origin https://github.com/qsc-josegutierrez/NEW_REPO_NAME.git
   git push -u origin master
   ```

### Issue 2: Repository Access Control

**If Repository is Private:**
Others need to be added as collaborators:
1. Go to: https://github.com/qsc-josegutierrez/langley_testhead
2. Click **Settings** → **Collaborators**
3. Click **Add people**
4. Enter their GitHub username or email
5. They'll receive invitation email

**Check Repository Visibility:**
```
Settings → General → Danger Zone → Change repository visibility
```

## 📋 INSTRUCTIONS FOR TEAM MEMBERS

### First-Time Clone
```powershell
# Clone repository
git clone https://github.com/qsc-josegutierrez/langley_testhead.git

# Navigate to folder
cd langley_testhead

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Common Pull Errors & Solutions

**Error: "Repository not found" or "Permission denied"**
- Check if you have access (see collaborator invitation email)
- Verify you're signed into correct GitHub account
- Try: `git remote -v` to verify URL

**Error: "Large files detected"**
- Repository size issue (see Issue 1 above)
- Contact repository owner to clean history

**Error: "Authentication failed"**
```powershell
# Update credentials
git config --global credential.helper manager-core
```

## 🔍 VERIFICATION COMMANDS

```powershell
# Check remote configuration
git remote -v

# Check repository status
git status

# Check branch
git branch -a

# Pull latest changes
git pull origin master
```

## 📦 WHAT SHOULD BE IN REPOSITORY

**✅ Include:**
- Source code (.py files)
- Configuration templates (config/)
- Documentation (.md, .txt files)
- requirements.txt
- .spec files for PyInstaller
- README files

**❌ Exclude (.gitignore):**
- Virtual environments (.venv/, venv/)
- Compiled executables (dist/)
- Build artifacts (build/)
- Python cache (__pycache__/, *.pyc)
- IDE settings (.vscode/, .idea/)
- OS files (.DS_Store, Thumbs.db)

## 🚀 DEPLOYING EXECUTABLES

Instead of committing executables to Git:

**Option 1: GitHub Releases**
1. Build executable: `pyinstaller testhead_gui.spec --clean`
2. Create release on GitHub
3. Upload dist/testhead_gui.exe as release asset
4. Team downloads from Releases page

**Option 2: Shared Network Drive**
- Copy dist/ folder to shared drive
- Update path in deployment docs

**Option 3: Build Locally**
- Each developer builds their own executable
- Included .spec files ensure consistent builds

## 📞 NEED HELP?

If team members still can't pull:
1. Verify they have GitHub accounts
2. Check repository visibility (public vs private)
3. Confirm they're added as collaborators
4. Check repository size hasn't exceeded limits
5. Verify network/firewall doesn't block GitHub

## Current Status
- ✅ .gitignore added
- ✅ Build artifacts removed from tracking
- ⚠️ Repository size needs cleanup (670 MB in history)
- ❓ Need to verify team member access/permissions
