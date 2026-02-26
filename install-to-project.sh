#!/bin/bash
# Git-Ops 專案內安裝腳本
# Install Git-Ops into a specific project

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 獲取腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                      ║${NC}"
echo -e "${BLUE}║   Git-Ops Project Installation Script               ║${NC}"
echo -e "${BLUE}║   Git-Ops 專案內安裝腳本                             ║${NC}"
echo -e "${BLUE}║                                                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 詢問目標專案目錄
if [ -n "$1" ]; then
    PROJECT_DIR="$1"
else
    read -p "請輸入專案根目錄 (按 Enter 使用當前目錄): " PROJECT_DIR
    if [ -z "$PROJECT_DIR" ]; then
        PROJECT_DIR="$(pwd)"
    fi
fi

# 轉換為絕對路徑
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

echo -e "${GREEN}目標專案: $PROJECT_DIR${NC}"
echo ""

# 確認是否為 Git 倉庫
if [ -d "$PROJECT_DIR/.git" ]; then
    echo -e "${GREEN}✓ 檢測到 Git 倉庫${NC}"
else
    echo -e "${YELLOW}⚠ 這不是一個 Git 倉庫${NC}"
    read -p "是否繼續安裝? (y/n): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "安裝已取消"
        exit 0
    fi
fi

echo ""

# 選擇安裝位置
echo -e "${YELLOW}選擇安裝位置:${NC}"
echo "  1) tools/git-ops/      (推薦)"
echo "  2) .git-ops/           (隱藏目錄)"
echo "  3) scripts/git-ops/"
echo "  4) 自訂位置"
echo ""

read -p "請選擇 (1-4): " LOCATION

case $LOCATION in
    1) TARGET_DIR="$PROJECT_DIR/tools/git-ops" ;;
    2) TARGET_DIR="$PROJECT_DIR/.git-ops" ;;
    3) TARGET_DIR="$PROJECT_DIR/scripts/git-ops" ;;
    4)
        read -p "請輸入相對於專案根目錄的路徑: " CUSTOM_PATH
        TARGET_DIR="$PROJECT_DIR/$CUSTOM_PATH"
        ;;
    *)
        echo -e "${RED}無效選擇${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}安裝到: $TARGET_DIR${NC}"
echo ""

# 創建目錄並複製檔案
echo -e "${YELLOW}[1/4] 複製檔案...${NC}"

mkdir -p "$TARGET_DIR"

# 複製核心檔案
echo "  - 複製 scripts/"
cp -r "$SCRIPT_DIR/scripts" "$TARGET_DIR/"

echo "  - 複製 requirements.txt"
cp "$SCRIPT_DIR/requirements.txt" "$TARGET_DIR/"

echo "  - 複製 git-ops.example.yml"
cp "$SCRIPT_DIR/git-ops.example.yml" "$TARGET_DIR/"

# 複製快速參考（可選）
if [ -f "$SCRIPT_DIR/QUICKSTART.txt" ]; then
    echo "  - 複製 QUICKSTART.txt"
    cp "$SCRIPT_DIR/QUICKSTART.txt" "$TARGET_DIR/"
fi

echo -e "${GREEN}✓ 檔案複製完成${NC}"
echo ""

# 創建包裝腳本
echo -e "${YELLOW}[2/4] 創建包裝腳本...${NC}"

# 計算相對路徑
REL_PATH=$(realpath --relative-to="$PROJECT_DIR" "$TARGET_DIR")

cat > "$PROJECT_DIR/gops.sh" << EOF
#!/bin/bash
# Git-Ops wrapper script for this project
# 自動生成於 $(date)

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
python3 "\$SCRIPT_DIR/$REL_PATH/scripts/git_ops.py" --from-text "\$@"
EOF

chmod +x "$PROJECT_DIR/gops.sh"

echo -e "${GREEN}✓ 包裝腳本已創建: $PROJECT_DIR/gops.sh${NC}"
echo ""

# 創建團隊配置範本
echo -e "${YELLOW}[3/4] 創建團隊配置...${NC}"

read -p "是否創建團隊共用配置檔? (y/n): " CREATE_CONFIG

if [[ "$CREATE_CONFIG" =~ ^[Yy]$ ]]; then
    if [ ! -f "$PROJECT_DIR/git-ops.yml" ]; then
        cp "$TARGET_DIR/git-ops.example.yml" "$PROJECT_DIR/git-ops.yml"
        echo -e "${GREEN}✓ 團隊配置已創建: $PROJECT_DIR/git-ops.yml${NC}"
        echo "  請編輯此檔案以自訂團隊設定"
    else
        echo -e "${YELLOW}⚠ git-ops.yml 已存在，跳過${NC}"
    fi
fi

echo ""

# 更新 .gitignore
echo -e "${YELLOW}[4/4] 更新 .gitignore...${NC}"

GITIGNORE="$PROJECT_DIR/.gitignore"

if [ -f "$GITIGNORE" ]; then
    if ! grep -q ".git-ops.yml" "$GITIGNORE" 2>/dev/null; then
        echo "" >> "$GITIGNORE"
        echo "# Git-Ops personal config (do not commit)" >> "$GITIGNORE"
        echo ".git-ops.yml" >> "$GITIGNORE"
        echo -e "${GREEN}✓ .gitignore 已更新${NC}"
    else
        echo "  .gitignore 已包含 git-ops 規則"
    fi
else
    echo -e "${YELLOW}⚠ 找不到 .gitignore${NC}"
    read -p "是否創建 .gitignore? (y/n): " CREATE_GITIGNORE
    if [[ "$CREATE_GITIGNORE" =~ ^[Yy]$ ]]; then
        cat > "$GITIGNORE" << EOF
# Git-Ops personal config (do not commit)
.git-ops.yml

# Git-Ops usage logs
.git-ops/
EOF
        echo -e "${GREEN}✓ .gitignore 已創建${NC}"
    fi
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Git-Ops 已安裝到專案！${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# 顯示專案結構
echo -e "${YELLOW}專案結構 / Project Structure:${NC}"
echo ""
echo "  $PROJECT_DIR/"
echo "  ├── $REL_PATH/              # Git-Ops 工具"
echo "  │   ├── scripts/"
echo "  │   └── requirements.txt"
echo "  ├── gops.sh                        # 包裝腳本"
echo "  ├── git-ops.yml                    # 團隊配置 (可提交)"
echo "  ├── .git-ops.yml                   # 個人配置 (不提交)"
echo "  └── .gitignore                     # 已更新"
echo ""

# 顯示使用方式
echo -e "${YELLOW}使用方式 / Usage:${NC}"
echo ""
echo "方法 1: 使用包裝腳本（推薦）"
echo -e "  ${BLUE}./gops.sh \"stash\" | bash${NC}"
echo -e "  ${BLUE}./gops.sh \"commit 'fix' and push\" | bash${NC}"
echo ""

echo "方法 2: 直接調用"
echo -e "  ${BLUE}python3 $REL_PATH/scripts/git_ops.py --from-text \"stash\" | bash${NC}"
echo ""

echo "方法 3: 創建 alias（可選）"
echo -e "  ${BLUE}alias pgops='./gops.sh'${NC}"
echo -e "  ${BLUE}pgops \"status\" | bash${NC}"
echo ""

# 顯示團隊設定建議
echo -e "${YELLOW}團隊協作建議 / Team Collaboration:${NC}"
echo ""
echo "1. 提交 git-ops 工具到版本控制:"
echo -e "   ${BLUE}git add $REL_PATH/${NC}"
echo -e "   ${BLUE}git add gops.sh${NC}"
echo -e "   ${BLUE}git add git-ops.yml${NC}"
echo -e "   ${BLUE}git commit -m \"Add git-ops tool\"${NC}"
echo ""

echo "2. 在 README 中添加使用說明"
echo ""

echo "3. 團隊成員安裝依賴:"
echo -e "   ${BLUE}pip install -r $REL_PATH/requirements.txt${NC}"
echo ""

# 創建 README 片段
README_SNIPPET="$PROJECT_DIR/GIT-OPS-README.md"
cat > "$README_SNIPPET" << 'EOF'
## Git-Ops 使用指南

本專案使用 Git-Ops 工具簡化 Git 操作。

### 快速開始

```bash
# 安裝依賴（首次使用）
pip install -r tools/git-ops/requirements.txt

# 使用自然語言執行 Git 操作
./gops.sh "stash my changes" | bash
./gops.sh "checkout main" | bash
./gops.sh "commit 'fix bug' and push" | bash
```

### 常用指令

```bash
./gops.sh "stash" | bash
./gops.sh "checkout develop" | bash
./gops.sh "pull with rebase" | bash
./gops.sh "log graph all" | bash
```

### 配置

團隊配置: `git-ops.yml`（已提交到版本控制）
個人配置: `.git-ops.yml`（不提交，可自訂個人別名）

詳細文檔: `tools/git-ops/QUICKSTART.txt`
EOF

echo -e "${GREEN}✓ README 片段已創建: $README_SNIPPET${NC}"
echo "  請將內容複製到專案 README.md"
echo ""

echo -e "${GREEN}安裝完成！Happy Git Operations! 🚀${NC}"
echo ""
