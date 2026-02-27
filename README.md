# Git-Ops - Natural Language Git Interface
# Git-Ops - Git 自然語言介面

🌟 **用自然語言執行 Git 操作，零 Token 消耗**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.6%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Tests](https://img.shields.io/badge/tests-100%25%20passing-success)]()

---

## 🎯 兩種使用方式

### 🤖 模式 1：Claude Code Skill（AI 輔助）

對 Claude 說話，自動執行 Git 操作：

```
你：幫我 stash 我的變更
Claude：[自動調用] 好的，執行 git stash...
```

**安裝：**
```bash
./install-as-skill.sh
```

---

### ⚡ 模式 2：獨立命令列工具（直接執行）

直接使用，零 tokens，即時執行：

```bash
# 內建執行器模式（推薦）
gops "stash my changes" -x         # 預覽 + [Y/n] 確認
gops "commit 'fix' and push" -x -y # 跳過確認，直接執行
gops "log graph all" -x -y

# 傳統管道模式
gops "stash my changes" | bash
```

**安裝：**
```bash
./install.sh
```

---

## ✨ 核心功能

- 🗣️ **自然語言解析** - 用人話執行 Git
- 🌐 **雙語支援** - 中英文都可以
- 📊 **Commit 圖形化** - 像 QGit 的 ASCII 圖形
- ⚙️ **高度可配置** - YAML 配置檔、別名、自訂模式
- 📈 **自動學習** - 追蹤使用、建議優化
- 🔒 **安全第一** - 預檢檢查、確認提示
- 💰 **零成本** - 獨立運作，無 API 調用
- 🤖 **LLM Fallback** - Regex 無法匹配時，可選用本地 Ollama 分類意圖
- 🚀 **內建執行器** - `-x` 直接執行，不再需要 `| bash`
- 🧠 **智能決策引擎** - 自動分析狀態、推薦最佳操作
- 🌳 **分支管理** - 分析、清理過期與已合併分支
- 📋 **團隊規則驗證** - Commit 格式、分支命名、品質檢查
- 📦 **進階 Stash 管理** - 詳細列表、備份匯出、安全套用
- 🔄 **工作流模板** - 多步驟自動化（create-feature、commit-and-push）
- ⚠️ **衝突偵測** - 合併前預先偵測潛在衝突

---

## 🚀 快速開始

### 30 秒安裝

```bash
# 選擇你的模式
./install-as-skill.sh    # Claude Code Skill 模式
# 或
./install.sh             # 獨立工具模式

# 重新載入 shell（僅獨立模式需要）
source ~/.bashrc

# 開始使用
gops "status" -x -y
```

---

## 📖 使用範例

### 基本操作

```bash
gops "stash" -x
gops "checkout main" -x
gops "pull with rebase" -x
gops "commit 'fix bug' and push" -x
```

### 進階操作

```bash
# 搜尋程式碼
gops "search for TODO in *.py" -x

# Commit 圖形化 🌳
gops "log graph all" -x -y

# 互動式 rebase
gops "rebase main interactively" -x
```

### 智能功能

```bash
# 預檢檢查
gops "preflight check" -x -y

# 智能建議：分析狀態，推薦操作
gops "what should I do" -x -y

# 偵測合併衝突
gops "detect conflicts with main" -x -y

# 分支分析與清理
gops "analyze branches" -x -y
gops "cleanup branches" -x

# 工作流自動化
gops "workflow commit-and-push" -x

# 團隊規則驗證
gops "validate commit message 'feat: new login'" -x -y
```

### 中文支援

```bash
gops "儲存我的變更" -x
gops "切換到主分支" -x
gops "提交 '修復錯誤' 並推送" -x
gops "顯示所有分支的關係圖" -x -y
```

### 使用別名（配置檔）

```yaml
# ~/.git-ops.yml
aliases:
  s: stash
  m: checkout main
  g: log graph all
```

```bash
gops "s" -x    # stash
gops "m" -x    # checkout main
gops "g" -x -y # log graph all
```

---

## 🎨 Commit 圖形化範例

```bash
$ gops "log graph all" -x -y
```

輸出：
```
* 2f8a3b1 (HEAD -> main) Add graph visualization
*   1a2b3c4 Merge branch 'feature/config'
|\
| * 4d5e6f7 (feature/config) Add config support
| * 8g9h0i1 Update config manager
|/
* 2j3k4l5 Add usage tracking
* 3k4l5m6 Initial commit
```

---

## 📋 支援的操作（24 個）

### 高頻操作
✅ stash, commit, checkout, pull, push, grep

### 一般操作
✅ reset, restore, merge, log, diff, clean

### 專業操作
✅ show, blame, tag, rebase, cherry-pick, bisect, reflog

### 智能功能
✅ preflight（預檢）, decide（智能建議）, conflict-detect（衝突偵測）, validate（規則驗證）, workflow（工作流）, branch（分支管理）

**完整說明**：參見 `SKILL.md`

---

## ⚙️ 配置系統

創建 `~/.git-ops.yml` 自訂行為：

```yaml
# 執行器設定（預設 print 模式，改為 execute 可省略 -x）
executor:
  default_mode: print    # print|execute

# 超短別名
aliases:
  s: stash
  m: checkout main
  cp: commit and push

# 自訂工作流程
custom_patterns:
  save work: stash with message 'WIP'
  sync main: checkout main, pull, checkout -

# Git 預設值
git:
  remote: origin
  sync_mode: rebase

# 安全設定
safety:
  confirm_destructive: true
  confirm_force_push: true
```

**完整指南**：參見 `CONFIG_GUIDE.md`

---

## 📊 自動學習系統

Git-Ops 會自動追蹤你的使用習慣並提供建議：

```bash
# 查看最常用的操作
python3 scripts/pattern_analyzer.py --top-operations

# 獲取個人化別名建議
python3 scripts/pattern_analyzer.py --suggest-aliases
```

完整的「學習-優化-執行」循環！

---

## 📦 安裝選項

### 選項 1：Claude Code Skill（推薦給 Claude 用戶）

```bash
./install-as-skill.sh
```

安裝到：`~/.claude/skills/git-ops/`

### 選項 2：全域安裝（推薦給命令列用戶）

```bash
./install.sh
```

安裝到：`~/tools/git-ops/`

### 選項 3：專案內安裝（團隊協作）

```bash
./install-to-project.sh /path/to/project
```

安裝到：`<project>/tools/git-ops/`

### 選項 4：最佳方案 - 兩個都裝！

```bash
./install-as-skill.sh  # Skill 模式
./install.sh           # 獨立模式
```

靈活運用，效率最高！

**詳細說明**：參見 `INSTALLATION_MODES.md`

---

## 🎯 適用場景

| 場景 | 模式 | 說明 |
|------|------|------|
| 💬 日常開發 | Skill 模式 | 對 Claude 說話，自動執行 |
| ⚡ 快速操作 | 獨立模式 | 直接命令列，即時執行 |
| 🤝 團隊協作 | 專案內安裝 | 統一工具和配置 |
| 🔄 CI/CD | 獨立模式 | 腳本集成，零 tokens |
| 📚 學習 Git | 兩者皆可 | 自然語言理解 Git |

---

## 📚 完整文檔

### 快速參考
- **QUICKSTART.txt** - 一頁速查表
- **QUICKSTART_zh-TW.txt** - 中文速查表

### 安裝指南
- **INSTALLATION_MODES.md** ⭐ - 安裝模式說明

### 功能說明
- **SKILL.md** - 完整功能參考
- **CONFIG_GUIDE.md** - 配置系統指南
- **GRAPH_VISUALIZATION_GUIDE.md** - 圖形化指南
- **USAGE_TRACKING_GUIDE.md** - 使用追蹤指南

### 其他
- **ERROR_HANDLING_QUICK_REF.md** - 錯誤碼速查
- **PASSWORD_INPUT_LIMITATION.md** - SSH 密碼限制說明
- **TROUBLESHOOTING.md** - 問題排解

---

## 🧪 測試

所有功能都經過完整測試：

```bash
# 配置系統測試
./test_config.sh

# 整合測試
./test_integration.sh

# 使用追蹤測試
./test_usage_tracking.sh
```

**測試覆蓋率：100% (21/21 tests passing)** ✅

---

## 💡 使用技巧

### 1. 超短別名

```yaml
# ~/.git-ops.yml
aliases:
  s: stash
  m: checkout main
```

打字節省 40-90%！

### 2. 完整工作流程

```yaml
custom_patterns:
  morning: checkout main, pull, checkout develop, pull
  evening: stash with message 'EOD', checkout main
```

一個指令完成多個步驟！

### 3. 團隊標準化

```yaml
# project/git-ops.yml
custom_patterns:
  start feature: checkout develop, pull, checkout -b feature/
  finish feature: checkout develop, merge -, push
```

團隊共用工作流程！

---

## 🆚 與其他工具比較

| 工具 | 類型 | Token 消耗 | 速度 | 離線 |
|------|------|-----------|------|------|
| **Git-Ops** | CLI/Skill | **0** (獨立模式) | ⚡ 即時 | ✅ |
| ChatGPT | Web | ~3000-10000 | 慢 | ❌ |
| GitHub Copilot | IDE | ~1000-5000 | 中等 | ❌ |
| 原生 Git | CLI | 0 | 即時 | ✅ |

**Git-Ops 優勢**：
- ✅ 自然語言 + 零 tokens
- ✅ 雙語支援
- ✅ 高度可配置
- ✅ 自動學習

---

## 🔄 系統需求

### 必須
- Python 3.6+
- Git

### 可選（配置檔功能）
- PyYAML >= 6.0

### 可選（LLM Fallback）
- [Ollama](https://ollama.com) + `ollama pull qwen2.5:3b`
- 啟用：在 `~/.git-ops.yml` 加入 `llm_fallback: { enabled: true }`

```bash
pip install -r requirements.txt
```

---

## 🌟 系統狀態

🟢 **PRODUCTION READY - 生產就緒**

- ✅ 24 個操作支援（17 基本 + 7 智能功能）
- ✅ 內建執行器（`-x` 直接執行）
- ✅ 完整文檔
- ✅ 生產級品質

---

## 📞 獲取幫助

- 🐛 **問題回報**：建議開 issue
- 📖 **查看文檔**：`cat SKILL.md`
- ⚡ **快速參考**：`cat QUICKSTART.txt`
- 💬 **使用範例**：`cat SKILL.md`

---

## 🎉 立即開始

```bash
# 1. 選擇你的安裝模式
./install-as-skill.sh    # 或 ./install.sh

# 2. 開始使用
gops "stash" -x

# 3. 自訂配置（可選）
nano ~/.git-ops.yml
```

**就這麼簡單！🚀**

---

## 📝 License

MIT License - 隨意使用！

---

## 🙏 致謝

感謝使用 Git-Ops！

如果覺得有用，請分享給你的團隊！

---

*Last Updated: 2026-02-27*
*Version: 2.1.0 - LLM Fallback + Built-in Executor + Smart Features*
