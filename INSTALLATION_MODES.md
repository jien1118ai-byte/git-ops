# Git-Ops 安裝模式說明
# Installation Modes Explained

## 重要：兩種不同的使用方式

Git-Ops 可以用兩種完全不同的方式使用：

---

## 模式 1：Claude Code Skill 模式 🤖

### 什麼時候用這個？
- ✅ 你在使用 **Claude Code** (CLI 工具)
- ✅ 你想要 Claude AI **自動幫你執行** Git 操作
- ✅ 你想說 "幫我 stash 變更"，Claude 會自動調用 git-ops

### 安裝位置
```
~/.claude/skills/git-ops/
```

### 安裝方式
```bash
./install-as-skill.sh
```

### 使用方式
**在 Claude Code 對話中：**
```
你：幫我 stash 我的變更
Claude：[自動調用 git-ops skill] 好的，我會幫你 stash...
```

**Claude 會自動：**
1. 偵測到你要執行 Git 操作
2. 調用 git-ops skill
3. 生成並執行對應的 Git 指令

### 檔案結構
```
~/.claude/skills/git-ops/
├── SKILL.md              ← Claude Code 讀取這個
├── scripts/
│   └── git_ops.py
├── requirements.txt
└── ...
```

### 關鍵檔案
- **SKILL.md** - Claude Code 讀取這個來了解如何使用 skill
- **claude.md** - 在你的專案中放這個來告訴 Claude 何時調用

---

## 模式 2：獨立命令列工具模式 ⚡

### 什麼時候用這個？
- ✅ 你**不使用** Claude Code，或想要直接使用
- ✅ 你想要一個快速的 Git 自然語言介面
- ✅ 你想節省 AI tokens（零 token 消耗）
- ✅ 你想在 CI/CD 或腳本中使用

### 安裝位置
```
~/tools/git-ops/          # 或任何你想要的位置
```

### 安裝方式
```bash
./install.sh              # 全域安裝
# 或
./install-to-project.sh   # 專案內安裝
```

### 使用方式
**直接在命令列：**
```bash
gops "stash my changes" | bash
gops "checkout main" | bash
gops "commit 'fix' and push" | bash
```

**不需要 Claude AI**，直接執行！

### 檔案結構
```
~/tools/git-ops/
├── scripts/
│   └── git_ops.py
├── requirements.txt
└── ...

~/.bashrc 或 ~/.zshrc:
alias gops='python3 ~/tools/git-ops/scripts/git_ops.py --from-text'
```

---

## 對比表格

| 特性 | Skill 模式 🤖 | 獨立工具模式 ⚡ |
|------|--------------|----------------|
| **安裝位置** | `~/.claude/skills/git-ops/` | `~/tools/git-ops/` |
| **安裝腳本** | `./install-as-skill.sh` | `./install.sh` |
| **使用方式** | 對 Claude 說話 | 直接命令列 `gops` |
| **需要 Claude Code** | ✅ 是 | ❌ 否 |
| **AI 輔助** | ✅ Claude 自動調用 | ❌ 手動執行 |
| **Token 消耗** | 有（Claude 對話） | **0 tokens** |
| **速度** | 需要 AI 回應 | **即時** |
| **離線可用** | 需要網路（AI） | ✅ 完全離線 |
| **適合場景** | 日常對話式操作 | 快速操作、腳本、CI/CD |

---

## 我應該選哪一個？

### 選擇 Skill 模式，如果：
- ✅ 你正在使用 Claude Code
- ✅ 你想要對話式的 Git 操作
- ✅ 你想要 AI 幫你理解和執行指令

**安裝：**
```bash
./install-as-skill.sh
```

---

### 選擇獨立工具模式，如果：
- ✅ 你想要快速的命令列工具
- ✅ 你想節省 tokens
- ✅ 你想在腳本或 CI/CD 中使用
- ✅ 你不想每次都等 AI 回應

**安裝：**
```bash
./install.sh
```

---

### 最佳方案：兩個都裝！✨

你可以同時安裝兩種模式：

```bash
# 1. 安裝為 Claude Code Skill
./install-as-skill.sh

# 2. 也安裝獨立工具
./install.sh
```

**好處：**
- 💬 對 Claude 說話時，自動調用 skill
- ⚡ 想快速執行時，直接用 `gops`
- 🎯 兩種方式都能用！

---

## 詳細安裝說明

### A. 安裝為 Claude Code Skill

```bash
# 1. 執行 skill 安裝腳本
./install-as-skill.sh

# 2. 腳本會自動：
#    - 檢測 ~/.claude/skills/ 目錄
#    - 複製所有必要檔案
#    - 安裝依賴（PyYAML）
#    - 初始化配置

# 3. 在 Claude Code 中測試
#    打開 Claude Code，說：
#    "幫我顯示 git status"
#    Claude 會自動調用 git-ops skill
```

**安裝後的結構：**
```
~/.claude/skills/git-ops/
├── SKILL.md              # Skill 說明
├── scripts/
│   ├── git_ops.py
│   ├── config_manager.py
│   ├── usage_logger.py
│   └── pattern_analyzer.py
├── requirements.txt
├── git-ops.example.yml
└── QUICKSTART.txt
```

---

### B. 安裝為獨立工具

```bash
# 1. 執行全域安裝腳本
./install.sh

# 2. 選擇 "1) 全域安裝"

# 3. 重新載入 shell
source ~/.bashrc

# 4. 直接使用
gops "stash" | bash
```

**安裝後的結構：**
```
~/tools/git-ops/
├── scripts/
│   └── git_ops.py
└── requirements.txt

~/.bashrc:
alias gops='python3 ~/tools/git-ops/scripts/git_ops.py --from-text'
```

---

## 在專案中告訴 Claude 何時使用 Skill

如果你選擇了 **Skill 模式**，在你的專案根目錄創建 `claude.md`：

```markdown
# Project Name

## Skills

### Git-Ops

Use the git-ops skill when the user wants to perform Git operations.

**Trigger scenarios:**
- User mentions Git commands in natural language
- User wants to commit, push, pull, merge, etc.

**Examples:**
- "stash my changes"
- "commit and push"
- "show commit graph"

See: .claude/skills/git-ops/SKILL.md for details
```

這樣 Claude 就知道什麼時候該調用 git-ops skill！

---

## 配置檔（兩種模式共用）

不管你用哪種模式，配置檔都放在：
```
~/.git-ops.yml
```

**範例配置：**
```yaml
aliases:
  s: stash
  m: checkout main
  cp: commit and push

custom_patterns:
  save work: stash with message 'WIP'
  sync main: checkout main, pull, checkout -
```

兩種模式都會讀取這個配置！

---

## 常見問題

### Q: 我已經用 `install.sh` 安裝了，如何改為 Skill 模式？

A: 直接再執行 `install-as-skill.sh`，兩個可以共存：
```bash
./install-as-skill.sh
```

### Q: Skill 模式和獨立模式會互相衝突嗎？

A: 不會！它們完全獨立：
- Skill 模式：在 `~/.claude/skills/git-ops/`
- 獨立模式：在 `~/tools/git-ops/`
- 配置檔：共用 `~/.git-ops.yml`

### Q: 我只想要快速工具，不想要 AI，應該用哪個？

A: 用獨立工具模式：
```bash
./install.sh
source ~/.bashrc
gops "status" | bash
```

### Q: 我想讓 Claude 自動幫我執行 Git 操作，應該用哪個？

A: 用 Skill 模式：
```bash
./install-as-skill.sh
```

然後在 Claude Code 中說 "幫我 stash 變更"

---

## 總結

**Skill 模式 (`.claude/skills/git-ops/`)**
- 🤖 Claude Code 自動調用
- 💬 對話式操作
- 🎯 適合日常開發

**獨立工具模式 (`~/tools/git-ops/`)**
- ⚡ 直接命令列使用
- 🚀 零 tokens，即時執行
- 🔧 適合快速操作、腳本、CI/CD

**建議：兩個都裝**
- 對話時用 Skill 模式
- 快速操作用獨立模式
- 靈活運用，效率最高！

---

*Updated: 2026-01-30*
