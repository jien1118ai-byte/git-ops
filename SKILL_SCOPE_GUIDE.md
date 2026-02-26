# Git-Ops Skill 作用域指南
# Skill Scope Guide - Global vs Project-specific

## Claude Code Skills 的兩種作用域

Claude Code 支援兩種 skills 安裝位置：

### 1. 全域 Skills（推薦 Git-Ops 使用） 🌍

**安裝位置：**
```
~/.claude/skills/git-ops/
```

**特性：**
- ✅ 所有專案都能使用
- ✅ 安裝一次，終身使用
- ✅ 統一維護、統一更新
- ✅ 節省磁碟空間

**何時使用全域？**
- 工具本身是**通用的**（如 Git 操作）
- 所有專案都會用到
- 邏輯不會因專案不同而改變

---

### 2. 專案 Skills（特殊需求） 📁

**安裝位置：**
```
<your-project>/.claude/skills/git-ops/
```

**特性：**
- ✅ 僅該專案可用
- ✅ 可以自訂專案特定邏輯
- ✅ 與專案一起版本控制
- ⚠️ 每個專案都要安裝

**何時使用專案級別？**
- 該 skill 是**專案特定的**
- 不同專案需要不同的 skill 版本
- 需要與專案一起部署

---

## Git-Ops 應該用哪一種？

### 💡 強烈推薦：全域安裝

**原因：**

1. **Git 操作是通用的**
   - `git stash` 在任何專案都一樣
   - `git commit` 的邏輯不會因專案改變
   - 不需要每個專案都裝一次

2. **配置可以專案級別**
   - Skill 全域安裝
   - 配置檔可以專案特定
   - 兩全其美！

3. **維護更簡單**
   - 更新一次，所有專案受益
   - 不用每個專案都更新

---

## Skill 呼叫優先順序

當你在專案內執行 Claude Code 時，查找順序：

```
1. <current-project>/.claude/skills/git-ops/     ← 專案級別（優先）
   ↓ 找不到
2. ~/.claude/skills/git-ops/                     ← 全域（備用）
   ↓ 找不到
3. 沒有 git-ops skill
```

**結論：**
- ✅ 全域安裝的 skill **會被**專案內的 Claude Code 呼叫到
- ✅ 除非專案內有同名 skill（會覆蓋全域）

---

## 推薦架構

### 方案 A：全域 Skill + 專案配置（最推薦）⭐

```
# Skill 安裝（全域）
~/.claude/skills/git-ops/
├── SKILL.md
├── scripts/
│   └── git_ops.py
└── ...

# 個人配置（全域）
~/.git-ops.yml
  aliases:
    s: stash
    m: checkout main

# 專案配置（專案特定）
/path/to/project-a/git-ops.yml
  custom_patterns:
    start: checkout develop, pull, checkout -b

/path/to/project-b/git-ops.yml
  custom_patterns:
    deploy: checkout main, pull, merge develop
```

**優點：**
- ✅ Skill 只裝一次，所有專案都能用
- ✅ 每個專案可以有自己的配置
- ✅ 團隊成員共享專案配置
- ✅ 個人可以有自己的別名

**安裝：**
```bash
# 1. 全域安裝 skill（一次性）
./install-as-skill.sh

# 2. 在需要的專案創建配置
cd /path/to/project
cp ~/.claude/skills/git-ops/git-ops.example.yml ./git-ops.yml
nano git-ops.yml  # 編輯專案特定配置
```

---

### 方案 B：完全專案級別（不推薦）

```
/path/to/project/.claude/skills/git-ops/
├── SKILL.md
├── scripts/
└── ...
```

**缺點：**
- ❌ 每個專案都要安裝
- ❌ 更新很麻煩（要更新每個專案）
- ❌ 浪費磁碟空間

**何時用？**
- 只有當不同專案需要**完全不同版本**的 git-ops 時
- 極少數情況

---

## 配置檔優先順序

Git-Ops 會依序搜尋配置檔（先找到先用）：

```
1. ./git-ops.yml                      ← 當前目錄
2. ./.git-ops.yml                     ← 當前目錄（隱藏）
3. <git-root>/git-ops.yml             ← Git 倉庫根目錄 ⭐
4. ~/.git-ops.yml                     ← 使用者家目錄
5. ~/.config/git-ops/config.yml       ← XDG 標準位置
```

**這意味著：**
- 專案配置會覆蓋個人配置
- 可以有全域預設 + 專案覆蓋

---

## 實際案例

### 案例 1：個人開發者

```bash
# 1. 全域安裝 skill（一次性）
./install-as-skill.sh

# 2. 創建個人配置
nano ~/.git-ops.yml
```

**結果：**
- 所有專案都能用 git-ops
- 所有專案共享你的個人配置

---

### 案例 2：團隊專案

```bash
# 每個團隊成員：

# 1. 全域安裝 skill（一次性）
./install-as-skill.sh

# 2. 創建個人配置（可選）
nano ~/.git-ops.yml

# 3. 專案根目錄有團隊配置
your-project/
├── git-ops.yml          # 團隊共用配置（已提交）
└── .git-ops.yml         # 個人覆蓋（不提交）
```

**配置範例：**

```yaml
# your-project/git-ops.yml（團隊配置）
custom_patterns:
  start task: checkout develop, pull, checkout -b feature/
  finish task: checkout develop, merge -, push

# ~/.git-ops.yml（個人配置）
aliases:
  s: stash
  m: checkout main
```

**效果：**
- 團隊成員都有 "start task" 和 "finish task" 模式
- 但每個人可以有自己的別名

---

### 案例 3：多個專案，不同配置

```
~/.claude/skills/git-ops/        ← Skill（全域，一份）

project-a/git-ops.yml             ← 專案 A 配置
  custom_patterns:
    deploy: checkout main, merge develop, push

project-b/git-ops.yml             ← 專案 B 配置
  custom_patterns:
    deploy: run tests, checkout prod, merge main, push

~/.git-ops.yml                    ← 個人配置
  aliases:
    s: stash
```

**效果：**
- 在 project-a 中執行 "deploy" → 使用 project-a 的定義
- 在 project-b 中執行 "deploy" → 使用 project-b 的定義
- 兩個專案都可以用 "s" 別名

---

## 測試你的設定

### 檢查 Skill 是否安裝正確

```bash
# 檢查全域 skill
ls ~/.claude/skills/git-ops/SKILL.md

# 如果存在 → ✅ 全域 skill 已安裝
```

### 檢查配置優先順序

```bash
# 在專案目錄內
cd /path/to/your/project

# 檢查會使用哪個配置
python3 ~/.claude/skills/git-ops/scripts/git_ops.py --from-text "status" --no-log 2>&1 | head -20

# 會顯示使用的配置檔路徑
```

### 在 Claude Code 中測試

```bash
# 進入專案目錄
cd /path/to/your/project

# 啟動 Claude Code
claude

# 在對話中說：
"幫我顯示 git status"

# 如果 Claude 自動調用 git-ops → ✅ Skill 正常運作
```

---

## 常見問題

### Q: 我在專案 A 內，會用到全域 skill 嗎？

**A:** 會！只要專案內沒有 `.claude/skills/git-ops/`

```
專案 A/
├── .git/
└── （沒有 .claude/skills/）

→ 使用 ~/.claude/skills/git-ops/ ✅
```

---

### Q: 我想要不同專案用不同配置，怎麼做？

**A:** Skill 全域安裝，配置檔專案級別：

```bash
# 1. Skill 全域安裝（一次性）
./install-as-skill.sh

# 2. 每個專案創建自己的配置
cd project-a
cp ~/.claude/skills/git-ops/git-ops.example.yml ./git-ops.yml
nano git-ops.yml  # 編輯 project-a 的配置

cd ../project-b
cp ~/.claude/skills/git-ops/git-ops.example.yml ./git-ops.yml
nano git-ops.yml  # 編輯 project-b 的配置
```

---

### Q: 全域 skill 和專案配置會衝突嗎？

**A:** 不會！它們是分開的：

- **Skill** - 工具本身的邏輯（全域）
- **配置** - 個人化設定（可專案級別）

就像：
- Git 軟體本身是全域的
- `.gitconfig` 可以專案級別

---

### Q: 我更新全域 skill，會影響所有專案嗎？

**A:** 會，但這是好事：

```bash
# 更新全域 skill
cd /path/to/git-ops
./install-as-skill.sh

# 所有專案立即獲得更新 ✅
# 配置檔不受影響 ✅
```

---

### Q: 團隊成員需要各自安裝 skill 嗎？

**A:** 是的，但很簡單：

```bash
# 每個成員執行一次
./install-as-skill.sh

# 或者在團隊文檔中說明：
# "請安裝 git-ops skill：執行 ./install-as-skill.sh"
```

專案配置檔（`git-ops.yml`）可以提交到版本控制，共享給團隊。

---

## 最佳實踐建議

### ✅ 推薦做法

1. **Skill 全域安裝**
   ```bash
   ./install-as-skill.sh
   ```

2. **個人配置全域**
   ```yaml
   # ~/.git-ops.yml
   aliases:
     s: stash
     m: checkout main
   ```

3. **專案配置專案級別**
   ```yaml
   # <project>/git-ops.yml（提交到版本控制）
   custom_patterns:
     start: checkout develop, pull, checkout -b
     finish: checkout develop, merge -, push
   ```

4. **個人覆蓋專案級別**
   ```yaml
   # <project>/.git-ops.yml（不提交，.gitignore）
   # 覆蓋專案配置的個人偏好
   ```

---

### ❌ 避免做法

1. **每個專案都安裝 skill**
   - 浪費空間
   - 維護困難

2. **把所有配置都放全域**
   - 不同專案無法有不同設定
   - 團隊無法共享配置

3. **把 skill 提交到專案版本控制**
   - Skill 應該全域安裝
   - 只提交配置檔即可

---

## 總結

### 💡 推薦架構

```
全域（所有專案共用）:
├── ~/.claude/skills/git-ops/    ← Skill（工具本身）
└── ~/.git-ops.yml               ← 個人配置

專案級別（專案特定）:
├── project-a/git-ops.yml        ← 專案 A 團隊配置
├── project-b/git-ops.yml        ← 專案 B 團隊配置
└── project-c/.git-ops.yml       ← 專案 C 個人覆蓋
```

### 🎯 安裝步驟

```bash
# 1. 全域安裝 skill（一次性）
./install-as-skill.sh

# 2. 創建個人配置（可選）
python3 ~/.claude/skills/git-ops/scripts/git_ops.py --init-config
nano ~/.git-ops.yml

# 3. 在需要的專案創建專案配置（可選）
cd /path/to/project
cp ~/.claude/skills/git-ops/git-ops.example.yml ./git-ops.yml
nano git-ops.yml

# 完成！所有專案都能用了 🎉
```

---

**結論：Git-Ops 應該全域安裝，配置可以專案級別！**

這樣既方便維護，又有足夠的靈活性。

---

*Last Updated: 2026-01-30*
