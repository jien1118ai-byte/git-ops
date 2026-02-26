# Git-Ops：獨立運行的自然語言 Git 工具

**一個將自然語言轉換為安全、可執行 Git 命令的獨立 Python 工具。**

🌟 **零 AI 依賴** - 完全離線運行，無需 Claude Code 或任何 AI 服務
⚡ **零 Token 成本** - 無限次執行 Git 操作完全免費
🛡️ **安全至上** - 內建預檢查機制和確認提示
🌐 **雙語支援** - 支援英文和繁體中文指令

---

## 快速開始

### 1. 前置需求

- Python 3.6+
- 已安裝並設定好的 Git
- 無需其他依賴套件！

### 2. 基本使用

```bash
# 進入 git-ops 目錄
cd /path/to/git-ops

# 使用自然語言
python3 scripts/git_ops.py --from-text "stash my changes"

# 執行生成的命令
python3 scripts/git_ops.py --from-text "commit 'fix bug' and push" | bash
```

### 3. 一鍵設定（推薦）

將以下內容加入 `~/.bashrc` 或 `~/.zshrc`：

```bash
alias gops='python3 /home/janes/Projects/AI/git-ops/scripts/git_ops.py --from-text'
```

重新載入 shell：
```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

現在可以在任何地方使用：
```bash
gops "stash and checkout main" | bash
gops "commit 'add feature' and push" | bash
```

---

## 支援的操作（共 17 種）

### 🔄 工作區管理
- **Stash（暫存）** - 儲存、列出、套用、彈出、刪除、顯示、清空暫存
- **Reset（重置）** - 撤銷 commit、取消暫存檔案（soft/mixed/hard）
- **Restore（恢復）** - 丟棄檔案中的更改
- **Clean（清理）** - 移除未追蹤的檔案

### 🌿 分支操作
- **Checkout/Switch（切換）** - 切換分支或建立新分支
- **Merge（合併）** - 使用各種策略合併分支
- **Rebase（變基）** - 重整分支、互動式壓縮 commits

### 📝 Commit 管理
- **Commit（提交）** - 建立帶訊息的 commit
- **Cherry-pick（挑選）** - 套用特定的 commits
- **Revert（還原）** - 安全地還原 commits
- **Amend（修改）** - 修改最後一次 commit

### 🔍 資訊與搜尋
- **Log（記錄）** - 查看帶篩選的 commit 歷史
- **Show（顯示）** - 顯示 commit 詳情
- **Diff（差異）** - 比較變更
- **Grep（搜尋）** - 在追蹤的檔案中搜尋程式碼
- **Blame（追蹤）** - 找出誰修改了每一行
- **Reflog（操作記錄）** - 查看操作歷史

### 🏷️ 標籤與進階功能
- **Tag（標籤）** - 建立、列出、刪除、推送標籤
- **Bisect（二分搜尋）** - 二分查找 bug

---

## 使用範例

### 自然語言指令

#### Stash 操作
```bash
gops "stash my changes" | bash
gops "stash with message 'work in progress'" | bash
gops "stash list" | bash
gops "apply stash 0" | bash
gops "pop stash" | bash
```

#### 搜尋與檢查
```bash
gops "search for 'TODO' in *.py files" | bash
gops "grep 'login' ignore case" | bash
gops "blame src/auth.py" | bash
gops "show reflog" | bash
gops "show last 10 commits" | bash
```

#### 重置與撤銷
```bash
gops "undo last commit" | bash
gops "unstage all files" | bash
gops "hard reset to origin/main" | bash
```

#### 分支管理
```bash
gops "checkout main" | bash
gops "create branch feature/new-ui" | bash
gops "create and checkout branch hotfix/bug-123" | bash
gops "delete branch old-feature locally" | bash
```

#### Commit 與 Push
```bash
gops "commit 'fix authentication bug' and push" | bash
gops "amend last commit" | bash
```

#### 進階操作
```bash
gops "cherry-pick abc123 def456" | bash
gops "merge develop with no-ff" | bash
gops "squash last 3 commits" | bash
gops "rebase main interactively" | bash
gops "create tag v1.0.0 with message 'release' and push" | bash
```

### 中文指令範例

```bash
gops "暫存我的更改" | bash
gops "顯示日誌" | bash
gops "作者為 張三" | bash
gops "切換 main" | bash
gops "創建分支 feature/新功能" | bash
gops "恢復 config.py" | bash
gops "丟棄更改在 package.json" | bash
gops "搜尋 TODO 在 *.py 檔案" | bash
gops "列出標籤" | bash
```

### 結構化命令（替代語法）

```bash
# Stash 操作
python3 scripts/git_ops.py stash save -m "temporary work"
python3 scripts/git_ops.py stash list
python3 scripts/git_ops.py stash pop 0

# 搜尋操作
python3 scripts/git_ops.py grep "TODO" --file-pattern "*.py"
python3 scripts/git_ops.py grep "pattern" -i

# Reset 操作
python3 scripts/git_ops.py reset HEAD~1 --soft
python3 scripts/git_ops.py reset --hard origin/main

# 分支操作
python3 scripts/git_ops.py checkout main
python3 scripts/git_ops.py checkout -b feature/new

# Tag 操作
python3 scripts/git_ops.py tag create v1.0.0 -m "Release"
python3 scripts/git_ops.py tag list

# Rebase
python3 scripts/git_ops.py rebase main -i
```

---

## 進階使用

### 1. 執行前預覽

```bash
# 先預覽生成的命令
gops "commit 'fix bug' and push"

# 複製貼上執行，或用管道傳給 bash
gops "commit 'fix bug' and push" | bash
```

### 2. 儲存為腳本

```bash
# 儲存以便稍後檢查
gops "complex operation" > /tmp/git-command.sh
cat /tmp/git-command.sh  # 檢查
bash /tmp/git-command.sh # 執行
```

### 3. 條件執行

```bash
# 只在前一個命令成功後才執行
gops "checkout main" | bash && gops "pull" | bash
```

### 4. 在腳本中使用

```bash
#!/bin/bash
# deploy.sh

GOPS="python3 /path/to/git-ops/scripts/git_ops.py --from-text"

# 自動化部署工作流程
$GOPS "stash" | bash
$GOPS "checkout main" | bash
$GOPS "pull" | bash
$GOPS "checkout -" | bash
$GOPS "stash pop" | bash
$GOPS "merge main" | bash
```

### 5. 建立輔助函數

加入 `~/.bashrc`：

```bash
# 自動執行 gops 命令
gopsrun() {
    python3 /path/to/git-ops/scripts/git_ops.py --from-text "$*" | bash
}

# 僅預覽
gopsview() {
    python3 /path/to/git-ops/scripts/git_ops.py --from-text "$*"
}
```

使用：
```bash
gopsrun "commit 'fix' and push"    # 自動執行
gopsview "hard reset to origin"    # 僅預覽
```

---

## 環境變數

### REMOTE
覆寫預設的遠端儲存庫（預設：`origin`）

```bash
REMOTE=upstream gops "push" | bash
```

### CONFIRM_DESTRUCTIVE
跳過確認提示（謹慎使用！）

```bash
CONFIRM_DESTRUCTIVE=0 gops "hard reset to HEAD~1" | bash
```

---

## 安全特性

所有生成的命令都包含：

1. ✅ **Git 儲存庫檢查** - 確保你在 git repo 中
2. ✅ **Detached HEAD 偵測** - 在 detached 狀態下阻擋寫入操作
3. ✅ **同步前預先 fetch** - push/pull 前總是先 fetch
4. ✅ **安全的強制推送** - 使用 `--force-with-lease` 而非 `--force`
5. ✅ **確認提示** - 破壞性操作需確認：
   - Hard reset
   - 分支刪除
   - Stash 清空/刪除
   - 標籤刪除
   - 檔案清理（除非 dry-run）

---

## 中文語言支援

工具完全支援繁體中文關鍵字：

```bash
gops "顯示日誌" | bash
gops "作者為 john" | bash
gops "切換 main" | bash
gops "創建分支 feature/test" | bash
gops "恢復 config.py" | bash
gops "丟棄更改" | bash
gops "搜尋 TODO" | bash
gops "列出標籤" | bash
gops "刪除分支 old-feature" | bash
gops "強制重置到 origin/main" | bash
```

支援的關鍵字：
- 日誌 (log)
- 作者 (author)
- 切換 (switch)
- 分支 (branch)
- 恢復 (restore)
- 丟棄 (discard)
- 搜尋/查找 (search/find)
- 強制 (hard)
- 保留更改 (soft)
- 包含未追蹤 (include untracked)
- 刪除 (delete)
- 列出 (list)
- 顯示 (show)
- 合併 (merge)
- 最近/上一個 (last)

---

## 整合範例

### Git Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Commit 前執行測試
npm test || exit 1
```

工具會自動遵守所有 git hooks。

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- name: Tag release
  run: |
    python3 scripts/git_ops.py --from-text "create tag v${{ github.run_number }}" | bash
```

### Cron Job

```bash
# 每日自動備份
0 2 * * * cd /path/to/repo && python3 /path/to/git-ops/scripts/git_ops.py --from-text "commit 'daily backup' and push" | bash
```

---

## 故障排除

### 找不到命令：python3

試試用 `python` 代替：
```bash
python scripts/git_ops.py --from-text "status"
```

### 權限不足

確保腳本可讀：
```bash
chmod +r scripts/git_ops.py
```

### 不在 git 儲存庫中

工具只能在 git 儲存庫內運作。先進入你的 git repo：
```bash
cd /path/to/your/git/repo
gops "status" | bash
```

### 確認提示阻擋自動化

使用環境變數跳過提示：
```bash
CONFIRM_DESTRUCTIVE=0 gops "dangerous operation" | bash
```

**警告**：只在可信任的自動化腳本中使用！

---

## 與其他工具的比較

| 功能 | git-ops | 原生 Git | GUI 工具 | AI 助手 |
|------|---------|----------|----------|---------|
| **自然語言** | ✅ | ❌ | ❌ | ✅ |
| **離線使用** | ✅ | ✅ | ✅ | ❌ |
| **免費** | ✅ | ✅ | 不一定 | 需要 Token |
| **安全檢查** | ✅ | 手動 | ✅ | 不一定 |
| **可編寫腳本** | ✅ | ✅ | ❌ | ❌ |
| **學習曲線** | 低 | 中 | 低 | 低 |
| **速度** | 快 | 快 | 中 | 慢 |
| **成本** | 免費 | 免費 | 不一定 | Token 費用 |

---

## 提示與最佳實踐

### 1. 從預覽開始
執行複雜命令前總是先預覽：
```bash
gops "dangerous operation"  # 先檢查
# 如果看起來沒問題：
gops "dangerous operation" | bash
```

### 2. 使用描述性訊息
```bash
# 好的
gops "commit 'fix: 解決登入流程中的認證超時問題' and push"

# 不理想
gops "commit 'fix' and push"
```

### 3. 善用別名
為常用操作建立捷徑：
```bash
alias gs='gops "stash"'
alias gsu='gops "stash pop"'
alias gm='gops "checkout main"'
alias gc='gops "checkout"'
```

### 4. 與標準 Git 結合使用
```bash
# 用 git-ops 處理複雜操作
gops "squash last 5 commits" | bash

# 用原生 git 進行簡單查詢
git status
git log --oneline
```

### 5. 版本控制你的別名
將 git-ops 別名加入 dotfiles 儲存庫，以便在多台機器間保持一致。

---

## 取得協助

### 查看所有可用操作
```bash
python3 scripts/git_ops.py --help
```

### 查看特定操作的說明
```bash
python3 scripts/git_ops.py stash --help
python3 scripts/git_ops.py grep --help
python3 scripts/git_ops.py reset --help
```

### 範例
查看 `SKILL.md` 了解所有 17 種操作的完整範例。

---

## 實用場景

### 場景 1：快速切換工作流程
```bash
# 臨時切換去修 bug
gops "stash" | bash
gops "checkout hotfix/urgent-bug" | bash
# ... 修 bug，commit，push
gops "checkout -" | bash  # 回到原本的分支
gops "stash pop" | bash
```

### 場景 2：整理 Commit 歷史
```bash
# 壓縮最近 5 個 commits
gops "squash last 5 commits" | bash
# 在互動式編輯器中調整
```

### 場景 3：搜尋與追蹤
```bash
# 找出所有包含 TODO 的 Python 檔案
gops "search for 'TODO' in *.py" | bash

# 找出誰修改了關鍵檔案
gops "blame src/critical.js" | bash
```

### 場景 4：安全的強制推送
```bash
# 使用 --force-with-lease 而非 --force
gops "force push" | bash
```

### 場景 5：標籤管理
```bash
# 建立並推送 release tag
gops "create tag v2.0.0 with message '重大版本更新' and push" | bash
```

---

## 授權

本工具是 git-ops 專案的一部分。自由使用！

---

## 貢獻

發現 bug 或想新增功能？程式碼在 `scripts/git_ops.py`。

主要修改的函數：
- `parse_operation_from_text()` - 新增自然語言模式
- `render()` - 新增命令生成邏輯
- `main()` - 新增 CLI 子命令

---

## 常見問題 FAQ

### Q: 可以在 Windows 上使用嗎？
A: 可以！只要有 Python 和 Git。在 PowerShell 中使用：
```powershell
python scripts/git_ops.py --from-text "status" | bash
```

### Q: 生成的腳本可以儲存重複使用嗎？
A: 可以！儲存後可以隨時執行：
```bash
gops "complex workflow" > my-workflow.sh
bash my-workflow.sh
```

### Q: 支援其他語言嗎？
A: 目前支援英文和繁體中文。可以修改 `parse_operation_from_text()` 函數來新增其他語言。

### Q: 安全嗎？
A: 是的！所有破壞性操作都有確認提示，且使用 `--force-with-lease` 而非 `--force`。但還是建議先預覽命令。

### Q: 會與我現有的 git 設定衝突嗎？
A: 不會。git-ops 只是生成標準的 git 命令，完全遵守你的 git 設定和 hooks。

---

**享受無憂的自然語言 Git 操作！🚀**
