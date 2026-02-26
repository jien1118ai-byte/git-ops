# Git-Ops 密碼輸入限制說明
# Password Input Limitations

## ⚠️ 重要限制

**Git-Ops 在 Claude Code 中無法輸入 SSH 密碼**

### 原因

當你在 Claude Code 中執行：
```bash
gops "pull" | bash
```

這個過程是：
```
gops 生成腳本 → 通過管道 (|) → 傳給 bash 執行
```

**問題：**
- 管道 (`|`) 會導致 bash 沒有連接到真正的 TTY（終端）
- SSH 需要 TTY 才能互動式提示密碼
- Claude Code 的執行環境不是完整的互動式終端

**結果：**
- ❌ 無法輸入密碼
- ❌ SSH 認證失敗

---

## ✅ 解決方案

### 方案 1：儲存腳本到檔案，然後在真正的終端執行（推薦）

```bash
# 在 Claude Code 中生成腳本並儲存
gops "pull" > /tmp/git-pull.sh

# 在你的終端（不是 Claude Code）執行
bash /tmp/git-pull.sh

# 這樣可以輸入密碼！
Password: [輸入密碼]
```

---

### 方案 2：直接在終端執行 git 指令

```bash
# 就像我建議的，直接在終端執行
git pull

# 會提示輸入密碼
Password: [輸入密碼]
```

---

### 方案 3：使用 SSH Key（最佳長期方案）⭐

```bash
# 1. 生成 SSH key（如果沒有）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 顯示 public key
cat ~/.ssh/id_ed25519.pub

# 3. 複製內容，添加到你的 Git 服務
#    GitHub: Settings → SSH and GPG keys → New SSH key
#    GitLab: Preferences → SSH Keys → Add new key

# 4. 測試
ssh -T git@github.com  # 或你的 Git 服務器

# 5. 之後就不需要密碼了！
gops "pull" | bash  # 直接成功 ✅
```

---

### 方案 4：改用 HTTPS + Credential Helper

```bash
# 1. 改為 HTTPS URL
git remote set-url origin https://github.com/user/repo.git

# 2. 設置 credential helper（記住密碼）
git config --global credential.helper store

# 3. 第一次手動執行
git pull
# 輸入用戶名和密碼

# 4. 之後 git-ops 可以直接用
gops "pull" | bash  # 不需要密碼 ✅
```

---

## 🎯 Git-Ops 的正確使用方式

### 在 Claude Code 中適合用的操作

**✅ 不需要密碼的操作：**
```bash
gops "status" | bash              # ✅ 查看狀態
gops "log graph" | bash           # ✅ 查看歷史
gops "diff" | bash                # ✅ 查看差異
gops "show HEAD" | bash           # ✅ 查看提交
gops "search for TODO" | bash     # ✅ 搜尋程式碼
gops "stash" | bash               # ✅ Stash 變更
```

**❌ 需要密碼的操作：**
```bash
gops "pull" | bash                # ❌ 如果需要密碼
gops "push" | bash                # ❌ 如果需要密碼
gops "commit and push" | bash     # ❌ 如果需要密碼
```

---

### 需要密碼時的正確流程

**步驟 1：用 git-ops 生成腳本**
```bash
# 在 Claude Code 中
gops "pull" > /tmp/git-pull.sh
```

**步驟 2：在真正的終端執行**
```bash
# 在你的終端（Ctrl+Alt+T 或你的終端應用）
bash /tmp/git-pull.sh

# 輸入密碼
Password: [輸入]
```

---

## 💡 推薦的工作流程

### 情境 1：需要 pull/push（有密碼）

```bash
# 方案 A：直接在終端用 git（最簡單）
git pull
git push

# 方案 B：設置 SSH key（一次性設置，永久解決）
# 參見上面的方案 3

# 方案 C：改用 HTTPS + credential helper
# 參見上面的方案 4
```

### 情境 2：本地操作（不需要密碼）

```bash
# 在 Claude Code 中直接用 git-ops
gops "stash" | bash
gops "checkout main" | bash
gops "commit 'fix bug'" | bash
gops "log graph" | bash
```

### 情境 3：需要 push（已設置 SSH key）

```bash
# 設置好 SSH key 後，git-ops 完全可用
gops "commit 'update' and push" | bash  # ✅ 直接成功
```

---

## 🔧 檢查你的設置

### 檢查是否已設置 SSH key

```bash
# 檢查是否有 SSH key
ls ~/.ssh/id_*.pub

# 如果有輸出（如 id_ed25519.pub），表示有 key

# 測試 SSH 連接
ssh -T git@github.com

# 如果看到 "Hi username!" 表示 SSH key 已設置好
# 如果提示密碼，表示還沒設置
```

### 檢查遠端 URL

```bash
# 查看使用的是 SSH 還是 HTTPS
git remote -v

# SSH 格式：git@github.com:user/repo.git
# HTTPS 格式：https://github.com/user/repo.git
```

---

## 📋 完整解決方案對比

| 方案 | 優點 | 缺點 | 適合場景 |
|------|------|------|---------|
| **SSH Key** ⭐ | 一次設置、永久解決、最安全 | 需要初始設置 | 日常開發（推薦） |
| **HTTPS + Credential** | 簡單、跨平台 | 密碼存在本地 | 臨時使用 |
| **直接用 git** | 最簡單 | 失去 git-ops 便利 | 偶爾需要密碼時 |
| **儲存腳本執行** | 保留 git-ops | 多一個步驟 | 想用 git-ops 又沒 key |

---

## 🎓 為什麼管道會失去 TTY？

### 技術解釋

```bash
# 方式 1：直接執行（有 TTY）
bash script.sh
# bash 連接到你的終端 → 可以輸入密碼 ✅

# 方式 2：通過管道（沒有 TTY）
echo "commands" | bash
# bash 的輸入來自管道，不是終端 → 無法輸入密碼 ❌

# git-ops 的情況
gops "pull" | bash
# 相當於：python3 ... | bash
# bash 的輸入來自 python 的輸出，不是終端 ❌
```

### 解決方法

```bash
# 方法 1：不用管道
gops "pull" > script.sh
bash script.sh  # 直接執行檔案 ✅

# 方法 2：使用 process substitution（進階）
bash <(gops "pull")  # 這樣也可以 ✅
```

---

## 🚀 最佳實踐建議

### 初次使用 Git-Ops

1. **立即設置 SSH key**（強烈推薦）
   ```bash
   ssh-keygen -t ed25519
   # 添加到 GitHub/GitLab
   ssh -T git@github.com  # 測試
   ```

2. **或改用 HTTPS + credential helper**
   ```bash
   git remote set-url origin https://...
   git config --global credential.helper store
   git pull  # 第一次輸入密碼
   ```

3. **設置好後，git-ops 完全可用**
   ```bash
   gops "pull" | bash              ✅
   gops "commit and push" | bash   ✅
   ```

---

### 日常使用

**已設置 SSH key/credential：**
```bash
# 所有操作都可以在 Claude Code 中用 git-ops
gops "pull" | bash
gops "commit 'update' and push" | bash
gops "log graph" | bash
```

**沒有設置的情況：**
```bash
# 本地操作：用 git-ops
gops "stash" | bash
gops "checkout main" | bash
gops "log graph" | bash

# 需要網路操作：直接用 git
git pull
git push
```

---

## ❓ 常見問題

### Q: 為什麼 git pull 可以輸入密碼，git-ops 不行？

A: 因為：
```bash
git pull          # 直接在終端執行 ✅
gops "pull" | bash # 通過管道，沒有 TTY ❌
```

### Q: 有沒有辦法讓 git-ops 在管道中也能輸入密碼？

A: 沒有簡單的方法。這是管道的本質限制。

**解決方案：**
- 設置 SSH key（推薦）
- 或儲存腳本後執行
- 或改用 HTTPS + credential helper

### Q: 我就是想用密碼，怎麼辦？

A: 使用這個 wrapper：

```bash
# 創建 wrapper 函數
gops-exec() {
    local script="/tmp/gops-$$.sh"
    gops "$1" > "$script"
    bash "$script"
    rm "$script"
}

# 使用
gops-exec "pull"
# 可以輸入密碼！
```

---

## 📝 總結

### 核心問題
**Claude Code 執行環境 + 管道 = 無法互動式輸入密碼**

### 最佳解決方案
**設置 SSH key** - 一勞永逸

### 臨時解決方案
1. 儲存腳本再執行
2. 直接用 git 指令
3. 改用 HTTPS + credential helper

### Git-Ops 的定位
- ✅ 本地操作完全可用
- ✅ 已設置 SSH key 後完全可用
- ⚠️ 需要密碼時有限制

---

*Updated: 2026-01-30*
*Issue: Interactive password input not possible in piped execution*
*Recommendation: Use SSH key authentication*
