# Git-Ops 安裝指南
# Installation Guide

## 安裝選項 / Installation Options

有三種安裝方式可選：

1. **全域安裝**（推薦）- 所有專案都能使用
2. **專案內安裝** - 只在特定專案使用
3. **開發者模式** - 直接使用當前目錄

---

## 選項 1：全域安裝（推薦）✨

### 步驟 1：選擇安裝位置

```bash
# 推薦位置
~/tools/git-ops/           # 或
~/.local/share/git-ops/    # 或
~/bin/git-ops/
```

### 步驟 2：複製檔案

```bash
# 創建目錄
mkdir -p ~/tools/git-ops

# 複製必要檔案
cp -r scripts ~/tools/git-ops/
cp requirements.txt ~/tools/git-ops/
cp git-ops.example.yml ~/tools/git-ops/

# 複製文檔（可選）
cp *.md ~/tools/git-ops/
cp *.txt ~/tools/git-ops/
```

### 步驟 3：安裝依賴

```bash
cd ~/tools/git-ops
pip install -r requirements.txt
```

### 步驟 4：設定 Shell Alias

**Bash (~/.bashrc):**
```bash
# 添加到 ~/.bashrc
alias gops='python3 ~/tools/git-ops/scripts/git_ops.py --from-text'

# 重新載入
source ~/.bashrc
```

**Zsh (~/.zshrc):**
```bash
# 添加到 ~/.zshrc
alias gops='python3 ~/tools/git-ops/scripts/git_ops.py --from-text'

# 重新載入
source ~/.zshrc
```

**Fish (~/.config/fish/config.fish):**
```fish
# 添加到 ~/.config/fish/config.fish
alias gops='python3 ~/tools/git-ops/scripts/git_ops.py --from-text'
```

### 步驟 5：初始化配置（可選）

```bash
# 創建個人配置
python3 ~/tools/git-ops/scripts/git_ops.py --init-config

# 編輯配置
nano ~/.git-ops.yml
```

### 步驟 6：測試

```bash
# 測試是否正常運作
gops "status" | bash

# 應該看到 git status 的輸出
```

✅ **完成！現在可以在任何目錄使用 gops**

---

## 選項 2：專案內安裝 📁

如果你只想在特定專案使用 git-ops：

### 步驟 1：在專案根目錄創建目錄

```bash
# 進入你的專案
cd /path/to/your/project

# 創建 tools 目錄
mkdir -p tools/git-ops
```

### 步驟 2：複製必要檔案

```bash
# 從 git-ops 源目錄複製
cp -r /path/to/git-ops/scripts tools/git-ops/
cp /path/to/git-ops/requirements.txt tools/git-ops/

# 或使用相對路徑（如果在 git-ops 目錄內）
cp -r scripts /path/to/your/project/tools/git-ops/
cp requirements.txt /path/to/your/project/tools/git-ops/
```

### 步驟 3：安裝依賴（在專案虛擬環境）

```bash
# 如果使用虛擬環境
cd /path/to/your/project
source venv/bin/activate  # 或你的虛擬環境

# 安裝依賴
pip install -r tools/git-ops/requirements.txt

# 或直接安裝
pip install PyYAML
```

### 步驟 4：創建專案專用 Alias

**方法 A：Shell Alias（推薦）**
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias pgops='python3 ./tools/git-ops/scripts/git_ops.py --from-text'

# 使用
pgops "stash" | bash
```

**方法 B：創建包裝腳本**
```bash
# 在專案根目錄創建 gops.sh
cat > gops.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/tools/git-ops/scripts/git_ops.py" --from-text "$@"
EOF

chmod +x gops.sh

# 使用
./gops.sh "stash" | bash
```

### 步驟 5：專案配置（可選）

```bash
# 在專案根目錄創建配置
cp tools/git-ops/git-ops.example.yml git-ops.yml

# 編輯專案專用配置
nano git-ops.yml
```

這樣團隊成員可以共享同樣的 git-ops 配置！

### 步驟 6：加入版本控制（可選）

```bash
# .gitignore
# 不要提交個人配置
.git-ops.yml

# 但可以提交團隊共用的配置
git add git-ops.yml
git add tools/git-ops/

# 提交
git commit -m "Add git-ops tool for team"
```

✅ **完成！專案內安裝完成**

---

## 選項 3：開發者模式（最簡單）🚀

直接在 git-ops 源目錄使用：

```bash
# 在 git-ops 目錄內
alias gops='python3 $PWD/scripts/git_ops.py --from-text'

# 或創建絕對路徑 alias
alias gops='python3 /home/janes/Projects/AI/git-ops/scripts/git_ops.py --from-text'

# 使用
gops "stash" | bash
```

---

## 最小安裝（僅核心檔案）

如果你想要最小化安裝，只需要這些檔案：

```
必須複製：
  scripts/git_ops.py          # 核心腳本

可選但推薦：
  requirements.txt            # 依賴清單
  scripts/config_manager.py   # 配置系統
  scripts/usage_logger.py     # 使用追蹤
  scripts/pattern_analyzer.py # 模式分析
  git-ops.example.yml         # 配置範本

文檔（可選）：
  SKILL.md                    # 功能說明
  CONFIG_GUIDE.md             # 配置指南
  QUICKSTART.txt              # 快速參考
```

**最小安裝範例**：
```bash
# 只複製核心腳本
mkdir -p ~/bin
cp scripts/git_ops.py ~/bin/
chmod +x ~/bin/git_ops.py

# 設定 alias
alias gops='python3 ~/bin/git_ops.py --from-text'

# 使用（無配置功能，但基本功能完整）
gops "stash" | bash
```

---

## 目錄結構範例

### 全域安裝後的結構

```
~/tools/git-ops/
├── scripts/
│   ├── git_ops.py
│   ├── config_manager.py
│   ├── usage_logger.py
│   └── pattern_analyzer.py
├── requirements.txt
├── git-ops.example.yml
└── docs/  (可選)
    ├── SKILL.md
    ├── CONFIG_GUIDE.md
    └── QUICKSTART.txt

~/.git-ops.yml              # 個人配置
~/.git-ops/                 # 使用記錄目錄
    └── usage.jsonl
```

### 專案內安裝後的結構

```
your-project/
├── src/
├── tests/
├── tools/
│   └── git-ops/
│       ├── scripts/
│       │   ├── git_ops.py
│       │   ├── config_manager.py
│       │   ├── usage_logger.py
│       │   └── pattern_analyzer.py
│       └── requirements.txt
├── git-ops.yml             # 團隊配置（可提交）
├── .git-ops.yml            # 個人配置（不提交）
├── gops.sh                 # 包裝腳本（可選）
└── .gitignore
```

---

## 團隊安裝建議

### 方案 A：全域 + 專案配置

```bash
# 每個開發者全域安裝 git-ops
mkdir -p ~/tools/git-ops
cp -r scripts ~/tools/git-ops/
pip install -r requirements.txt

# 專案內只放配置檔
your-project/
└── git-ops.yml  # 團隊共用配置

# .gitignore
.git-ops.yml     # 不提交個人配置
```

**優點**：
- 工具版本由個人管理
- 配置可團隊共享
- 不增加專案大小

### 方案 B：專案內包含工具

```bash
# 將 git-ops 放入專案
your-project/
├── tools/git-ops/
└── git-ops.yml

# 提供設定腳本
cat > setup-git-ops.sh << 'EOF'
#!/bin/bash
pip install -r tools/git-ops/requirements.txt
alias gops='python3 ./tools/git-ops/scripts/git_ops.py --from-text'
echo "Git-ops installed! Add alias to your shell config."
EOF
chmod +x setup-git-ops.sh
```

**優點**：
- 版本統一
- 新成員容易上手
- 離線可用

---

## 驗證安裝

### 測試清單

```bash
# 1. 測試基本功能
gops "status" | bash

# 2. 測試配置（如果安裝了）
gops --init-config
ls ~/.git-ops.yml  # 應該存在

# 3. 測試使用追蹤（如果安裝了）
gops "stash" | bash
ls ~/.git-ops/usage.jsonl  # 應該存在

# 4. 測試圖形功能
gops "log graph" | bash

# 5. 測試中文支援
gops "儲存變更" | bash
```

---

## 升級 Git-Ops

### 全域安裝升級

```bash
# 備份配置
cp ~/.git-ops.yml ~/.git-ops.yml.backup

# 更新檔案
cd /path/to/git-ops-source
cp -r scripts ~/tools/git-ops/
cp requirements.txt ~/tools/git-ops/

# 更新依賴
pip install -r ~/tools/git-ops/requirements.txt --upgrade

# 還原配置
cp ~/.git-ops.yml.backup ~/.git-ops.yml
```

### 專案內安裝升級

```bash
# 在專案根目錄
cd /path/to/your/project

# 備份配置
cp git-ops.yml git-ops.yml.backup

# 更新工具
cp -r /path/to/git-ops-source/scripts tools/git-ops/

# 還原配置
cp git-ops.yml.backup git-ops.yml
```

---

## 卸載 Git-Ops

### 全域安裝卸載

```bash
# 移除檔案
rm -rf ~/tools/git-ops

# 移除配置
rm ~/.git-ops.yml
rm -rf ~/.git-ops/

# 從 shell 配置移除 alias
# 編輯 ~/.bashrc 或 ~/.zshrc，刪除 gops alias 那行
```

### 專案內安裝卸載

```bash
# 在專案根目錄
rm -rf tools/git-ops
rm git-ops.yml
rm .git-ops.yml
rm gops.sh  # 如果有包裝腳本
```

---

## 常見問題 / FAQ

### Q: 我應該選擇哪種安裝方式？

**A:** 推薦順序：
1. **個人使用** → 全域安裝
2. **團隊專案** → 全域安裝 + 專案配置檔
3. **測試/試用** → 開發者模式

### Q: 需要 sudo 權限嗎？

**A:** 不需要。所有安裝都在用戶目錄進行。

### Q: 可以不安裝 PyYAML 嗎？

**A:** 可以！沒有 PyYAML 只是無法使用配置檔功能，其他功能都正常。

### Q: 如何讓團隊成員使用同樣的配置？

**A:** 將 `git-ops.yml` 放在專案根目錄並提交到版本控制：

```bash
# 專案根目錄
your-project/
└── git-ops.yml  # 提交這個檔案

# git-ops 會自動找到並使用這個配置
```

### Q: 可以在 Docker 容器內使用嗎？

**A:** 可以！在 Dockerfile 中：

```dockerfile
# 安裝 git-ops
COPY tools/git-ops /opt/git-ops
RUN pip install -r /opt/git-ops/requirements.txt
RUN echo 'alias gops="python3 /opt/git-ops/scripts/git_ops.py --from-text"' >> /root/.bashrc
```

### Q: Windows 怎麼安裝？

**A:** 使用 Git Bash 或 WSL：

```bash
# Git Bash
alias gops='python /c/tools/git-ops/scripts/git_ops.py --from-text'

# WSL (與 Linux 相同)
alias gops='python3 ~/tools/git-ops/scripts/git_ops.py --from-text'
```

---

## 快速安裝腳本

創建一鍵安裝腳本：

```bash
cat > install-git-ops.sh << 'EOF'
#!/bin/bash
set -e

echo "Installing Git-Ops..."

# 設定安裝位置
INSTALL_DIR="${HOME}/tools/git-ops"

# 創建目錄
mkdir -p "$INSTALL_DIR"

# 複製檔案
cp -r scripts "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp git-ops.example.yml "$INSTALL_DIR/"

# 安裝依賴
echo "Installing dependencies..."
pip install -r "$INSTALL_DIR/requirements.txt"

# 設定 alias
SHELL_CONFIG=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
fi

if [ -n "$SHELL_CONFIG" ]; then
    echo "" >> "$SHELL_CONFIG"
    echo "# Git-Ops alias" >> "$SHELL_CONFIG"
    echo "alias gops='python3 $INSTALL_DIR/scripts/git_ops.py --from-text'" >> "$SHELL_CONFIG"
    echo "✓ Alias added to $SHELL_CONFIG"
fi

# 初始化配置
python3 "$INSTALL_DIR/scripts/git_ops.py" --init-config

echo ""
echo "✅ Git-Ops installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Reload shell: source $SHELL_CONFIG"
echo "  2. Edit config: nano ~/.git-ops.yml"
echo "  3. Test: gops \"status\" | bash"
EOF

chmod +x install-git-ops.sh
```

使用：
```bash
./install-git-ops.sh
source ~/.bashrc  # 或 ~/.zshrc
gops "status" | bash
```

---

## 總結

**推薦安裝方式**：

| 場景 | 推薦方式 | 指令 |
|------|---------|------|
| 個人日常使用 | 全域安裝 | `~/tools/git-ops/` + shell alias |
| 團隊專案 | 全域 + 專案配置 | 工具全域，配置在專案內 |
| 測試/試用 | 開發者模式 | 直接使用源目錄 |
| CI/CD | 專案內安裝 | `tools/git-ops/` |

**最簡單的開始**：
```bash
# 1. 全域安裝
mkdir -p ~/tools/git-ops
cp -r scripts ~/tools/git-ops/
pip install PyYAML

# 2. 設定 alias
echo "alias gops='python3 ~/tools/git-ops/scripts/git_ops.py --from-text'" >> ~/.bashrc
source ~/.bashrc

# 3. 開始使用
gops "stash" | bash
```

完成！🎉
