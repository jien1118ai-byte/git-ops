# Git Commit Graph Visualization Guide
# Git 提交關係圖視覺化指南

## 新功能！Graph 視覺化支援

git-ops 現在支援像 QGit 一樣的 commit 關係圖顯示！

---

## 快速使用 / Quick Usage

### 基本圖形 / Basic Graph

```bash
# 顯示 commit 關係圖
gops "log graph" | bash
gops "show log as graph" | bash
gops "視覺化提交歷史" | bash

# 英文觸發詞
gops "log with graph" | bash
gops "show commit tree" | bash
gops "visual log" | bash

# 中文觸發詞
gops "顯示關係圖" | bash
gops "日誌圖形" | bash
```

### 顯示所有分支 / Show All Branches

```bash
# 顯示所有分支的圖形
gops "log graph all" | bash
gops "log graph all branches" | bash
gops "顯示所有分支的關係圖" | bash

# 更詳細的
gops "show commit graph for all branches" | bash
```

---

## 輸出範例 / Output Examples

### 範例 1：基本圖形

```bash
$ gops "log graph" | bash
```

輸出：
```
* 2f8a3b1 - (HEAD -> main) Add graph visualization support
*   1a2b3c4 - Merge branch 'feature/config'
|\
| * 4d5e6f7 - (feature/config) Add config file support
| * 8g9h0i1 - Update config manager
|/
* 2j3k4l5 - Add usage tracking
* 3k4l5m6 - Initial commit
```

### 範例 2：所有分支的圖形

```bash
$ gops "log graph all" | bash
```

輸出：
```
* 2f8a3b1 - (HEAD -> main, origin/main) Add graph visualization
| * 9a8b7c6 - (feature/new) Work in progress
|/
*   1a2b3c4 - Merge branch 'feature/config'
|\
| * 4d5e6f7 - (origin/feature/config) Add config support
| * 8g9h0i1 - Update config manager
|/
* 2j3k4l5 - Add usage tracking
| * 5m6n7o8 - (develop) Development branch
|/
* 3k4l5m6 - Initial commit
```

### 範例 3：限制數量

```bash
$ gops "show last 5 commits as graph" | bash
```

輸出前 5 個提交的圖形。

---

## 觸發關鍵字 / Trigger Keywords

### English Keywords:
- `graph`
- `tree`
- `visual`
- `visualize`

### Chinese Keywords (中文關鍵字):
- `視覺化`
- `關係圖`
- `圖形`

### 顯示所有分支 / All Branches:
- `all`
- `all branches`
- `所有`
- `所有分支`

---

## 實用範例 / Practical Examples

### 1. 查看最近的合併歷史

```bash
gops "show last 10 commits as graph" | bash
```

### 2. 視覺化整個項目歷史

```bash
gops "log graph all branches" | bash
```

### 3. 查看特定作者的提交圖

```bash
gops "show commits by john as graph" | bash
```

### 4. 查看特定檔案的歷史圖

```bash
gops "log graph for src/main.py" | bash
```

### 5. 中文範例

```bash
# 顯示最近 20 個提交的關係圖
gops "顯示最近 20 個提交的關係圖" | bash

# 視覺化所有分支
gops "視覺化所有分支的日誌" | bash
```

---

## 進階：自訂圖形格式

如果你想要更詳細的圖形（含作者、日期），可以直接使用 Git 指令：

```bash
# 超詳細的彩色圖形
git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --all

# 創建別名（加到 ~/.bashrc 或 ~/.zshrc）
alias gitgraph='git log --graph --pretty=format:"%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset" --abbrev-commit --all'

# 然後直接使用
gitgraph
```

---

## 配置檔整合 / Configuration Integration

你也可以在 `~/.git-ops.yml` 中創建別名：

```yaml
aliases:
  g: log graph all
  tree: log graph all
  viz: log graph

custom_patterns:
  show tree: log graph all branches
  commit map: log graph all branches
```

使用：
```bash
gops "g" | bash           # 顯示圖形（所有分支）
gops "tree" | bash        # 同上
gops "viz" | bash         # 顯示圖形（當前分支）
gops "show tree" | bash   # 使用自訂模式
```

---

## 與其他工具比較 / Comparison with Other Tools

| Tool | Type | Graph Support | Pros | Cons |
|------|------|---------------|------|------|
| **git-ops** | CLI | ✅ ASCII graph | Fast, zero dependencies | ASCII only |
| **QGit** | GUI | ✅ Visual graph | Beautiful GUI | Requires GUI |
| **gitk** | GUI | ✅ Visual graph | Built-in Git tool | Requires GUI |
| **GitKraken** | GUI | ✅ Visual graph | Modern UI | Commercial |
| **tig** | CLI | ✅ ASCII graph | Interactive | Requires install |
| **lazygit** | CLI | ✅ ASCII graph | Interactive TUI | Requires install |

---

## 圖形符號說明 / Graph Symbols Explained

```
*   - Commit (提交點)
|   - Branch line (分支線)
/   - Merge point (合併點)
\   - Branch point (分支點)
```

範例解讀：
```
*   1a2b3c4 - Merge branch 'feature'  ← 合併提交
|\                                     ← 分支分叉點
| * 4d5e6f7 - Add new feature         ← feature 分支的提交
| * 8g9h0i1 - Update tests            ← feature 分支的另一個提交
|/                                     ← 分支匯合點
* 2j3k4l5 - Initial commit            ← 主分支的提交
```

---

## 常見使用場景 / Common Use Cases

### 1. 檢查合併是否正確

```bash
gops "log graph all" | bash
# 查看分支合併的結構是否符合預期
```

### 2. 找出分支的分叉點

```bash
gops "show commit graph for all branches" | bash
# 視覺化找出兩個分支何時分開
```

### 3. 理解複雜的歷史

```bash
gops "log graph last 30" | bash
# 查看最近的提交結構
```

### 4. 檢查是否有未合併的分支

```bash
gops "log graph all branches" | bash
# 看看有沒有孤立的分支
```

---

## 技術實作細節 / Technical Details

### 生成的 Git 指令

當你使用 graph 功能時，git-ops 會生成：

```bash
# 基本 graph
git log --graph --oneline --decorate --color -n 20

# 包含所有分支
git log --graph --oneline --decorate --color -n 20 --all
```

### 參數說明

- `--graph`: 顯示 ASCII 圖形
- `--oneline`: 每個 commit 一行
- `--decorate`: 顯示分支和 tag 名稱
- `--color`: 彩色輸出
- `--all`: 顯示所有分支
- `-n 20`: 限制顯示數量

---

## 故障排除 / Troubleshooting

### 問題 1：圖形顯示亂碼

**可能原因**：終端機不支援 UTF-8

**解決方案**：
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### 問題 2：沒有顏色

**可能原因**：Git 顏色設定關閉

**解決方案**：
```bash
git config --global color.ui auto
```

### 問題 3：圖形太複雜看不清

**解決方案**：
```bash
# 限制顯示數量
gops "show last 10 commits as graph" | bash

# 或只顯示當前分支（不要用 all）
gops "log graph" | bash
```

---

## 最佳實踐 / Best Practices

### 1. 日常使用

```bash
# 創建便捷別名
alias gl='gops "log graph" | bash'
alias gla='gops "log graph all" | bash'

# 使用
gl    # 當前分支的圖形
gla   # 所有分支的圖形
```

### 2. 配置檔設定

```yaml
# ~/.git-ops.yml
aliases:
  g: log graph
  ga: log graph all
  tree: log graph all
```

### 3. 查看特定範圍

```bash
# 最近 10 個
gops "show last 10 commits as graph" | bash

# 最近 30 個（所有分支）
gops "show last 30 commits as graph all" | bash
```

---

## 總結 / Summary

現在 git-ops 支援 commit 關係圖視覺化！

✅ **觸發方式**：
- 加上 `graph`、`tree`、`visual` 等關鍵字
- 中文：`視覺化`、`關係圖`、`圖形`

✅ **顯示所有分支**：
- 加上 `all` 或 `所有分支`

✅ **完全整合**：
- 支援配置檔別名
- 支援使用追蹤
- 支援中英文混合

享受視覺化的 Git 歷史！🌳

---

*Feature added: 2026-01-30*
*Updated SKILL.md and git_ops.py to support graph visualization*
