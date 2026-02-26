# Git-Ops Configuration Guide

## 概述

Git-ops 現在支援 YAML 配置檔，讓你可以：
- 🎛️ 自訂預設行為
- ⚡ 建立個人化別名
- 🔧 定義自訂自然語言模式
- 🛡️ 調整安全設定
- 📊 控制使用記錄

---

## 快速開始

### 1. 安裝依賴

配置檔功能需要 PyYAML：

```bash
pip install -r requirements.txt
# 或
pip install PyYAML
```

### 2. 初始化配置檔

```bash
# 自動生成配置範本
python3 scripts/git_ops.py --init-config

# 或手動複製範例檔案
cp git-ops.example.yml ~/.git-ops.yml
```

### 3. 編輯配置

```bash
# 編輯配置檔
nano ~/.git-ops.yml
# 或
vim ~/.git-ops.yml
```

### 4. 使用配置

```bash
# 自動載入（從標準位置）
gops "stash" | bash

# 指定配置檔
gops "stash" --config /path/to/config.yml | bash
```

---

## 配置檔位置

Git-ops 會依序搜尋以下位置（先找到先使用）：

1. `./git-ops.yml` - 當前目錄
2. `./.git-ops.yml` - 當前目錄（隱藏檔）
3. `<git-root>/git-ops.yml` - Git 儲存庫根目錄
4. `~/.git-ops.yml` - 使用者家目錄
5. `~/.config/git-ops/config.yml` - XDG 標準位置

### 建議位置

- **個人專案**：`~/.git-ops.yml`（全域設定）
- **團隊專案**：`<git-root>/git-ops.yml`（專案特定設定）
- **臨時設定**：`--config` 參數指定

---

## 配置項目說明

### Git 預設設定

```yaml
git:
  remote: origin          # 預設遠端儲存庫名稱
  sync_mode: rebase       # 同步策略：rebase|merge|none
  push_mode: push         # 推送行為：push|nopush|lease
  branch: null            # 預設分支（null = 使用當前分支）
```

**範例**：
```yaml
# 總是使用 merge 而非 rebase
git:
  sync_mode: merge

# 預設使用 upstream 作為遠端
git:
  remote: upstream
```

---

### 安全與確認設定

```yaml
safety:
  confirm_destructive: true      # 危險操作需確認
  confirm_hard_reset: true       # hard reset 需確認
  confirm_force_push: true       # force push 需確認
  confirm_branch_delete: true    # 刪除分支需確認
```

**範例**：
```yaml
# 關閉所有確認（危險！）
safety:
  confirm_destructive: false
  confirm_hard_reset: false
  confirm_force_push: false
  confirm_branch_delete: false
```

⚠️ **警告**：停用確認可能導致意外的資料遺失！

---

### 別名（Aliases）

別名讓你用超短指令執行常用操作。

```yaml
aliases:
  s: stash                    # gops "s" → gops "stash"
  sp: stash pop               # gops "sp" → gops "stash pop"
  cm: checkout main           # gops "cm" → gops "checkout main"
  cap: commit and push        # gops "cap" → gops "commit and push"
```

**使用方式**：
```bash
# 原本
gops "stash" | bash

# 使用別名後
gops "s" | bash

# 原本
gops "checkout main" | bash

# 使用別名後
gops "cm" | bash
```

**實用別名範例**：
```yaml
aliases:
  # 超短 stash 操作
  s: stash
  sp: stash pop
  sl: stash list

  # 快速切換分支
  cm: checkout main
  cd: checkout develop
  cb: checkout -

  # 快速提交
  c: commit
  cp: commit and push
  ca: commit --amend

  # 快速撤銷
  undo: reset --soft HEAD~1
  unstage: reset HEAD

  # 搜尋相關
  find: search for
  grep: search for
```

---

### 自訂模式（Custom Patterns）

自訂模式讓你建立完全客製化的自然語言指令。

```yaml
custom_patterns:
  save: stash with message 'WIP'
  quick commit: commit 'wip' and push
  sync: pull with rebase
```

**使用方式**：
```bash
# 使用自訂模式
gops "save" | bash
# 實際執行：gops "stash with message 'WIP'" | bash

gops "quick commit" | bash
# 實際執行：gops "commit 'wip' and push" | bash
```

**進階範例 - 工作流程**：
```yaml
custom_patterns:
  # 儲存工作狀態
  save: stash with message 'WIP'
  save work: stash with message 'work in progress'

  # 快速提交
  qc: commit 'wip'
  quick commit: commit 'wip' and push

  # 同步流程
  sync: pull with rebase
  sync main: checkout main, pull, checkout -
  update: pull with rebase

  # 清理流程
  clean up: stash, checkout main, pull
  fresh start: stash, checkout main, pull, checkout -b

  # 完成功能流程
  done: merge main, push, delete branch
```

---

### 記錄設定

```yaml
logging:
  enabled: true                  # 啟用使用追蹤
  log_file: ~/.git-ops/usage.jsonl
  log_errors: true               # 記錄失敗的操作
```

**停用記錄**：
```yaml
logging:
  enabled: false
```

---

### 行為自訂

```yaml
behavior:
  auto_fetch: true              # 操作前自動 fetch
  use_force_with_lease: true    # 使用 --force-with-lease
  interactive_mode: false       # 互動模式
  verbose: false                # 詳細輸出
```

---

## 實用配置範例

### 範例 1：個人快捷設定

```yaml
# ~/.git-ops.yml

git:
  remote: origin
  sync_mode: rebase

aliases:
  # 超短別名
  s: stash
  sp: stash pop
  m: checkout main
  d: checkout develop
  c: commit
  p: push

  # 組合操作
  save: stash
  load: stash pop
  sync: pull
  done: commit and push

custom_patterns:
  quick save: stash with message 'WIP'
  quick commit: commit 'wip' and push
```

**使用**：
```bash
gops "s" | bash              # stash
gops "m" | bash              # checkout main
gops "sync" | bash           # pull
gops "done 'fix bug'" | bash # commit and push
```

---

### 範例 2：團隊標準設定

```yaml
# <project-root>/git-ops.yml

git:
  remote: origin
  sync_mode: rebase
  push_mode: push

safety:
  confirm_destructive: true
  confirm_force_push: true

aliases:
  # 團隊標準縮寫
  main: checkout main
  dev: checkout develop
  new: checkout -b
  done: merge main and push

custom_patterns:
  # 標準工作流程
  start feature: checkout develop, pull, checkout -b
  finish feature: checkout develop, pull, merge -, push
  hotfix: checkout main, pull, checkout -b hotfix/

logging:
  enabled: true
```

---

### 範例 3：安全優先設定

```yaml
# ~/.git-ops.yml

git:
  sync_mode: merge    # 使用 merge 避免 rebase 風險

safety:
  # 所有確認都啟用
  confirm_destructive: true
  confirm_hard_reset: true
  confirm_force_push: true
  confirm_branch_delete: true

behavior:
  auto_fetch: true
  use_force_with_lease: true
  verbose: true       # 顯示詳細資訊

# 不定義危險的別名
aliases:
  # 只有安全的操作
  status: status
  log: log
  show: show
```

---

### 範例 4：效率最大化設定

```yaml
# ~/.git-ops.yml

safety:
  # 停用所有確認（自己承擔風險！）
  confirm_destructive: false
  confirm_hard_reset: false
  confirm_force_push: false
  confirm_branch_delete: false

aliases:
  # 超短單字母別名
  s: stash
  p: stash pop
  c: commit and push
  m: checkout main
  u: pull

custom_patterns:
  # 一鍵操作
  1: stash
  2: stash pop
  3: commit and push
  go: checkout main, pull

logging:
  enabled: false  # 停用記錄以獲得最快速度
```

⚠️ **警告**：此設定會犧牲安全性以換取速度！

---

## 配置管理指令

### 查看當前配置

```bash
# 查看完整配置
python3 scripts/config_manager.py --show

# 查看特定值
python3 scripts/config_manager.py --get git.remote
python3 scripts/config_manager.py --get aliases.s
```

### 修改配置

```bash
# 設定單一值
python3 scripts/config_manager.py --set git.remote upstream
python3 scripts/config_manager.py --set logging.enabled false

# 設定別名
python3 scripts/config_manager.py --set aliases.s stash
```

### 初始化配置

```bash
# 生成範本
python3 scripts/config_manager.py --init

# 或使用 git_ops.py
python3 scripts/git_ops.py --init-config
```

---

## 配置優先順序

配置的載入順序（後面會覆蓋前面）：

1. **內建預設值** - git_ops.py 的預設設定
2. **配置檔** - YAML 檔案的設定
3. **命令列參數** - --config, --no-log 等

**範例**：
```yaml
# ~/.git-ops.yml
git:
  remote: origin
```

```bash
# 使用配置檔的設定
gops "push" | bash  # 推送到 origin

# 命令列參數覆蓋配置
REMOTE=upstream gops "push" | bash  # 推送到 upstream
```

---

## 團隊協作

### 分享配置

```bash
# 將配置加入版本控制
cp ~/.git-ops.yml project/git-ops.yml
cd project
git add git-ops.yml
git commit -m "Add git-ops team configuration"
```

### 個人化團隊配置

```yaml
# project/git-ops.yml（團隊共用）
git:
  remote: origin
  sync_mode: rebase

# ~/.git-ops.yml（個人覆蓋）
aliases:
  # 個人偏好的別名
  s: stash
  m: checkout main
```

Git-ops 會先載入團隊配置，再載入個人配置。

---

## 故障排除

### 配置檔無效

```bash
# 檢查 YAML 語法
python3 -c "import yaml; yaml.safe_load(open('~/.git-ops.yml'.replace('~', '$HOME')))"

# 查看當前使用的配置
python3 scripts/config_manager.py --show
```

### 別名不生效

```bash
# 檢查別名定義
python3 scripts/config_manager.py --get aliases

# 測試別名解析
python3 -c "
from scripts.config_manager import ConfigManager
config = ConfigManager()
print(config.resolve_alias('s'))
"
```

### PyYAML 未安裝

```bash
# 安裝依賴
pip install PyYAML

# 或使用 requirements.txt
pip install -r requirements.txt
```

如果無法安裝 PyYAML，git-ops 仍然可以正常運作，只是無法使用配置檔功能。

---

## 最佳實踐

### 1. 從範例開始

```bash
cp git-ops.example.yml ~/.git-ops.yml
# 然後逐步調整
```

### 2. 漸進式添加別名

```bash
# 先用一段時間，找出常用指令
python3 scripts/pattern_analyzer.py --suggest-aliases

# 再將建議加入配置檔
```

### 3. 備份配置

```bash
# 定期備份
cp ~/.git-ops.yml ~/.git-ops.yml.backup

# 或加入 dotfiles 版本控制
```

### 4. 測試配置

```bash
# 修改配置後先測試
gops "s" | bash  # 不要直接執行，先檢查生成的命令
```

### 5. 文件化團隊配置

```yaml
# project/git-ops.yml
# Team Git-Ops Configuration
# Updated: 2026-01-30
# Owner: DevOps Team
#
# Standard aliases:
#   main - checkout main
#   dev - checkout develop
#   ...
```

---

## 進階技巧

### 條件式配置（手動實作）

根據專案使用不同配置：

```bash
# ~/bin/gops-wrapper.sh
#!/bin/bash
if [ -f ".git-ops.yml" ]; then
    python3 ~/git-ops/scripts/git_ops.py --config .git-ops.yml "$@"
else
    python3 ~/git-ops/scripts/git_ops.py "$@"
fi
```

### 整合優先級分析

```bash
# 自動更新配置中的優先級
python3 scripts/pattern_analyzer.py --export
# 然後將 priority.json 的內容合併到配置檔
```

### 建立配置模板庫

```bash
# ~/.git-ops-templates/
├── personal.yml
├── team-standard.yml
├── safe.yml
└── fast.yml

# 快速切換
cp ~/.git-ops-templates/fast.yml ~/.git-ops.yml
```

---

## 總結

配置檔讓 git-ops 更：
- 🎯 **個人化** - 完全符合你的工作習慣
- ⚡ **高效** - 超短別名節省時間
- 🤝 **協作友善** - 團隊標準化工作流程
- 🔧 **可擴展** - 自訂模式無限可能

開始建立你的配置檔，讓 git-ops 完全屬於你！🚀
