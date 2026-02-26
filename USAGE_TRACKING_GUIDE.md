# Git-Ops 使用追蹤與優化指南

## 概述

Git-ops 現在包含自動使用追蹤功能，可以：
1. 📊 記錄你的自然語言指令模式
2. 📈 分析最常用的操作
3. 💡 建議個人化的別名
4. 🎯 根據使用頻率調整優先級

---

## 功能說明

### 1. 自動使用記錄 (UsageLogger)

每次使用自然語言指令時，會自動記錄：
- 輸入的指令文字
- 解析出的操作類型
- 時間戳記
- 成功/失敗狀態

**記錄位置**：`~/.git-ops/usage.jsonl`

---

### 2. 模式分析 (PatternAnalyzer)

分析你的使用記錄並提供：
- 操作優先級排名
- 最常用的關鍵字
- 未被識別的模式
- 個人化別名建議

---

## 使用方式

### 基本使用（自動記錄）

正常使用 git-ops，系統會自動記錄：

```bash
gops "stash my changes" | bash      # 自動記錄
gops "commit 'fix' and push" | bash # 自動記錄
gops "checkout main" | bash         # 自動記錄
```

### 停用記錄

如果不想記錄某次使用：

```bash
# 方法 1: 使用 --no-log 參數
gops "sensitive operation" --no-log | bash

# 方法 2: 設定環境變數
export GIT_OPS_NO_LOG=1
gops "operation" | bash
unset GIT_OPS_NO_LOG
```

### 查看使用統計

```bash
# 查看統計資訊
python3 scripts/usage_logger.py --stats

# 範例輸出：
# === Git-ops Usage Statistics ===
#
# Total uses: 245
# Error rate: 2.0%
#
# Operations by frequency:
#   stash                  78 ( 31.8%)
#   checkout               45 ( 18.4%)
#   commit                 42 ( 17.1%)
#   grep                   28 ( 11.4%)
#   ...
```

### 匯出使用模式

```bash
# 匯出所有成功的唯一模式
python3 scripts/usage_logger.py --export

# 輸出到: ~/.git-ops/patterns.txt
```

### 清除記錄

```bash
# 清除所有使用記錄
python3 scripts/usage_logger.py --clear
```

---

## 模式分析功能

### 查看完整分析報告

```bash
# 分析最近 30 天的使用
python3 scripts/pattern_analyzer.py

# 分析最近 7 天
python3 scripts/pattern_analyzer.py --days 7

# 分析最近 90 天
python3 scripts/pattern_analyzer.py --days 90
```

### 報告內容範例

```
======================================================================
Git-Ops Usage Analysis (Last 30 days)
======================================================================

### Operation Priority (by usage frequency)

 1. stash             78 uses ( 31.8%) ⭐⭐⭐
 2. checkout          45 uses ( 18.4%) ⭐
 3. commit            42 uses ( 17.1%) ⭐
 4. grep              28 uses ( 11.4%) ⭐
 5. reset             18 uses (  7.3%)
 ...

### Unrecognized or Failed Patterns

  None - all patterns parsed successfully!

### Suggested Aliases (for frequent patterns)

Add these to your ~/.bashrc or ~/.zshrc:

# Used 25 times
alias gops-smc='gops "stash my changes"'

# Used 18 times
alias gops-cm='gops "checkout main"'

# Used 15 times
alias gops-cap='gops "commit and push"'

### Most Common Keywords

Overall top keywords:
  stash              78 times
  checkout           65 times
  commit             42 times
  main               38 times
  ...
```

### 只查看別名建議

```bash
# 只顯示建議的別名
python3 scripts/pattern_analyzer.py --suggest-aliases

# 輸出：
# # Suggested aliases based on your usage:
# # Add to ~/.bashrc or ~/.zshrc
#
# # Used 25 times
# alias gops-smc='gops "stash my changes"'
#
# # Used 18 times
# alias gops-cm='gops "checkout main"'
```

### 匯出優先級配置

```bash
# 匯出為 JSON 配置檔
python3 scripts/pattern_analyzer.py --export

# 生成 priority.json：
# {
#   "generated_at": "2026-01-29T17:30:00",
#   "priorities": {
#     "stash": {"count": 78, "percentage": 31.8, "rank": 1},
#     "checkout": {"count": 45, "percentage": 18.4, "rank": 2},
#     ...
#   },
#   "recommendations": {
#     "stash": "high_priority",
#     "checkout": "medium_priority",
#     ...
#   }
# }
```

---

## 實際應用場景

### 場景 1：發現你的常用操作

使用一段時間後：

```bash
python3 scripts/pattern_analyzer.py --days 30
```

你可能發現：
- 80% 的時間在用 stash, checkout, commit
- 可以為這些建立快捷別名

### 場景 2：建立個人化別名

根據分析結果：

```bash
# 查看建議
python3 scripts/pattern_analyzer.py --suggest-aliases

# 複製建議的別名到 ~/.bashrc
cat >> ~/.bashrc << 'EOF'
# Git-ops personal aliases
alias gops-s='gops "stash"'
alias gops-sp='gops "stash pop"'
alias gops-cm='gops "checkout main"'
alias gops-cap='gops "commit and push"'
EOF

source ~/.bashrc
```

現在可以用超短指令：
```bash
gops-s | bash           # 暫存
gops-cm | bash          # 切換到 main
gops-cap "fix bug"      # commit 並 push
```

### 場景 3：優化解析器

如果分析顯示某些模式常常失敗或被誤判：

```bash
python3 scripts/pattern_analyzer.py --days 30
```

查看 "Unrecognized or Failed Patterns" 部分，然後可以：
1. 向開發者回報這些模式
2. 調整你的輸入方式
3. 自行修改 `git_ops.py` 的解析邏輯

---

## 進階使用

### 定期分析工作流程

建立 cron job 定期生成報告：

```bash
# 每週日生成報告
echo "0 0 * * 0 python3 ~/Projects/AI/git-ops/scripts/pattern_analyzer.py > ~/git-ops-weekly-report.txt" | crontab -
```

### 團隊使用模式分享

如果在團隊中使用：

```bash
# 匯出你的使用模式（不含隱私資訊）
python3 scripts/usage_logger.py --export

# 分享 ~/.git-ops/patterns.txt 給團隊
# 團隊可以分析共同的使用模式
```

### 與 Git Hooks 整合

在 commit 前自動記錄：

```bash
# .git/hooks/pre-commit
#!/bin/bash
# 記錄這次 commit
echo "commit hook triggered" >> ~/.git-ops/usage.jsonl
```

---

## 隱私與資料安全

### 記錄的內容

✅ **會記錄**：
- 你輸入的自然語言指令
- 操作類型
- 時間戳記
- 成功/失敗狀態

❌ **不會記錄**：
- 實際的 commit 內容
- 檔案內容
- 敏感資訊（除非你在指令中輸入）

### 資料位置

所有記錄儲存在本地：
- `~/.git-ops/usage.jsonl` - 使用記錄
- `~/.git-ops/patterns.txt` - 匯出的模式

### 停用追蹤

完全停用追蹤：

```bash
# 加入環境變數
echo 'export GIT_OPS_NO_LOG=1' >> ~/.bashrc
source ~/.bashrc
```

或刪除記錄檔：
```bash
rm -rf ~/.git-ops/
```

---

## 常見問題

### Q: 記錄會影響效能嗎？
A: 不會。記錄是非阻塞的，即使失敗也不會影響正常使用。

### Q: 可以分析其他人的使用模式嗎？
A: 可以。如果有權限讀取他們的 `~/.git-ops/usage.jsonl`。

### Q: 記錄檔會無限增長嗎？
A: 會逐漸增長。建議定期清理舊記錄：
```bash
# 只保留最近 90 天的記錄
find ~/.git-ops -name "usage.jsonl" -mtime +90 -delete
```

### Q: 可以匯出為其他格式嗎？
A: 記錄是 JSONL 格式（每行一個 JSON），可以輕鬆轉換：
```bash
# 轉為 CSV
python3 -c "
import json
with open('~/.git-ops/usage.jsonl'.replace('~', '$HOME')) as f:
    for line in f:
        entry = json.loads(line)
        print(f\"{entry['timestamp']},{entry['operation']},{entry['input']}\")
" > usage.csv
```

---

## 總結

使用追蹤和模式分析可以幫助你：

1. 📊 **了解使用習慣** - 看看你最常用哪些操作
2. ⚡ **提升效率** - 為常用操作建立快捷別名
3. 🎯 **優化工具** - 根據實際使用調整功能優先級
4. 💡 **發現問題** - 找出未被識別的模式並改進

開始使用，讓 git-ops 越用越聰明！🚀
