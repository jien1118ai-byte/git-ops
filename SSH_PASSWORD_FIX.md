# SSH 密碼輸入修復
# SSH Password Input Fix

## 問題描述 / Problem

當使用 SSH 協議的 Git 倉庫（如 `git@github.com:...`）時，如果需要輸入密碼，會出現錯誤：

```
ssh_askpass: exec(/usr/bin/ssh-askpass): No such file or directory
Permission denied, please try again.
...
fatal: Could not read from remote repository.
```

**原因：**
- SSH 嘗試使用 `ssh-askpass` 程序來獲取密碼
- 但系統中沒有安裝 `ssh-askpass`
- 導致無法輸入密碼

---

## 解決方案 / Solution

**已修改 `scripts/git_ops.py`：**

在 `bash_prelude()` 函數中添加了：

```bash
# Disable ssh-askpass, allow terminal password input
unset SSH_ASKPASS
unset SSH_ASKPASS_REQUIRE
export GIT_SSH_COMMAND='ssh -o ControlMaster=no'
```

**這些設定的作用：**

1. **`unset SSH_ASKPASS`**
   - 移除 SSH_ASKPASS 環境變數
   - SSH 將不會嘗試使用 ssh-askpass 程序
   - 改為直接在終端提示輸入密碼

2. **`unset SSH_ASKPASS_REQUIRE`**
   - 確保不強制要求使用 askpass
   - 允許使用終端輸入

3. **`export GIT_SSH_COMMAND='ssh -o ControlMaster=no'`**
   - 設置 Git 使用標準 SSH
   - 禁用 ControlMaster（可能會干擾密碼輸入）
   - 確保每次都是新的 SSH 連接

---

## 使用方式 / Usage

### 現在可以正常輸入密碼

```bash
# 使用 git-ops
gops "pull" | bash

# 會提示輸入密碼
Password: [在這裡輸入密碼]

# 或者 commit and push
gops "commit 'fix' and push" | bash
Password: [在這裡輸入密碼]
```

---

## 測試驗證 / Testing

### 測試 1：檢查生成的腳本

```bash
python3 scripts/git_ops.py --from-text "pull" --no-log | head -20
```

**應該看到：**
```bash
export GIT_TERMINAL_PROMPT=1
unset SSH_ASKPASS
unset SSH_ASKPASS_REQUIRE
export GIT_SSH_COMMAND='ssh -o ControlMaster=no'
```

### 測試 2：實際執行

```bash
# 在需要 SSH 密碼的倉庫中
gops "pull" | bash

# 應該會看到密碼提示，而不是錯誤
```

---

## 替代方案 / Alternative Solutions

如果你不想每次都輸入密碼，可以考慮：

### 方案 1：使用 SSH Key（推薦）

```bash
# 1. 生成 SSH key（如果沒有）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 添加 public key 到 Git 服務（GitHub/GitLab/etc）
cat ~/.ssh/id_ed25519.pub
# 複製內容，添加到你的 Git 服務的 SSH keys 設定

# 3. 測試連接
ssh -T git@github.com  # 或你的 Git 服務器

# 之後就不需要輸入密碼了
```

### 方案 2：使用 SSH Agent

```bash
# 啟動 ssh-agent
eval "$(ssh-agent -s)"

# 添加你的 SSH key
ssh-add ~/.ssh/id_ed25519

# 現在這個 session 中不需要輸入密碼
```

### 方案 3：使用 HTTPS + Credential Helper

```bash
# 改用 HTTPS URL
git remote set-url origin https://github.com/user/repo.git

# 設置 credential helper（會記住密碼）
git config --global credential.helper store

# 第一次輸入密碼後，之後會自動使用
```

---

## 如果仍然無法輸入密碼

### 檢查 1：確認終端是互動式的

```bash
# 確保在互動式終端中執行
# 不要在背景執行或從腳本中呼叫
```

### 檢查 2：手動測試 SSH

```bash
# 測試 SSH 連接
ssh -T git@github.com

# 或你的 Git 服務器
ssh -T git@your-server.com

# 如果這個可以輸入密碼，git-ops 也應該可以
```

### 檢查 3：查看完整錯誤訊息

```bash
# 查看詳細錯誤
GIT_TRACE=1 gops "pull" | bash
```

---

## 技術細節 / Technical Details

### 修改位置

**檔案：** `scripts/git_ops.py`

**函數：** `bash_prelude()`

**修改前：**
```python
def bash_prelude() -> str:
    return r"""set -euo pipefail
export GIT_TERMINAL_PROMPT=1

# ---- preflight ----
...
```

**修改後：**
```python
def bash_prelude() -> str:
    return r"""set -euo pipefail
export GIT_TERMINAL_PROMPT=1

# Disable ssh-askpass, allow terminal password input
unset SSH_ASKPASS
unset SSH_ASKPASS_REQUIRE
export GIT_SSH_COMMAND='ssh -o ControlMaster=no'

# ---- preflight ----
...
```

---

## 環境變數說明

| 變數 | 作用 | 設定值 |
|------|------|--------|
| `GIT_TERMINAL_PROMPT` | 允許 Git 在終端提示輸入 | `1` (啟用) |
| `SSH_ASKPASS` | SSH 使用的密碼輸入程序 | `unset` (不使用) |
| `SSH_ASKPASS_REQUIRE` | 是否強制使用 askpass | `unset` (不強制) |
| `GIT_SSH_COMMAND` | Git 使用的 SSH 命令 | `ssh -o ControlMaster=no` |

---

## 相關問題排除

### Q: 為什麼不直接安裝 ssh-askpass？

A: 因為：
1. ssh-askpass 需要圖形界面（GUI）
2. 在 CLI 環境中不適用
3. 終端直接輸入更簡單、更普遍

### Q: 這會影響 SSH key 認證嗎？

A: 不會！
- 如果有設定 SSH key，會優先使用 key
- 只有在需要密碼時才會提示

### Q: 這個修改安全嗎？

A: 是的！
- 只是改變密碼輸入的方式（GUI askpass → 終端）
- 不會儲存或傳輸密碼
- 實際上更安全（不依賴外部程序）

---

## 更新記錄 / Change Log

**2026-01-30:**
- 添加 SSH password 輸入支援
- 移除對 ssh-askpass 的依賴
- 允許終端直接輸入密碼

---

## 總結

**修改前：**
- ❌ 需要 ssh-askpass 程序
- ❌ 無法輸入密碼
- ❌ 出現錯誤

**修改後：**
- ✅ 不需要 ssh-askpass
- ✅ 可以在終端輸入密碼
- ✅ 正常運作

**建議：**
- 🔑 長期使用建議設定 SSH key
- 🚀 短期使用可以輸入密碼
- 💡 兩種方式都支援

---

*Fixed: 2026-01-30*
*Issue: SSH password input not working*
*Solution: Disable ssh-askpass, use terminal input*
