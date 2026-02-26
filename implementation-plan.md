# Git-Ops Skill 改進實施計畫

## 🎯 目標
改進 git-ops skill 的錯誤處理與記錄機制，使 AI 能夠：
1. 自動捕捉並理解操作失敗
2. 在 notes 中記錄所有操作（成功或失敗）
3. 快速診斷和恢復錯誤

---

## 📋 實施階段

### Phase 1: 錯誤日誌系統 (優先實施)
**時間: 立即**  
**內容:**
- [ ] 增強 `UsageLogger` 類支持詳細的錯誤信息
  - [ ] 添加 `log_error()` 方法記錄完整的錯誤上下文
  - [ ] 支持錯誤代碼、退出碼、建議恢復步驟
  - [ ] 生成錯誤摘要文件供 AI 查詢

- [ ] 修改 `render()` 函數在生成的 bash 腳本中添加：
  - [ ] `trap` 處理器捕捉錯誤
  - [ ] 自動記錄失敗的上下文信息
  - [ ] 常見 git 錯誤的識別與恢復建議

- [ ] 創建 `ErrorHandler` 類
  - [ ] 分類常見的 git 錯誤類型
  - [ ] 生成人類和 AI 可讀的錯誤報告
  - [ ] 建議恢復步驟

**文件變更:**
- `scripts/usage_logger.py` - 增強錯誤記錄
- `scripts/git_ops.py` - 修改 render() 函數
- `scripts/error_handler.py` - 新建

**預期輸出:**
```
~/.git-ops/
├── usage.jsonl
├── errors.jsonl         (新)
├── notes/              (新)
│   ├── 2026-02-12.md
│   └── 2026-02-11.md
└── error_summary.md    (新)
```

---

### Phase 2: 操作筆記系統
**時間: 之後實施**  
**內容:**
- [ ] 創建 `OperationNotes` 類
  - [ ] 每日自動創建筆記文件
  - [ ] 記錄操作摘要（時間、指令、結果、任何警告）
  - [ ] 支持標記為 AI 閱讀

- [ ] 修改生成的 bash 腳本在完成後記錄 notes
  - [ ] 操作開始時的 git status
  - [ ] 操作完成時的狀態
  - [ ] 任何警告或邊界情況

- [ ] 在 `git_ops.py` 中集成 notes 記錄

**文件變更:**
- `scripts/operation_notes.py` - 新建

---

### Phase 3: 文檔與 AI 指導
**時間: 最後完成**  
**內容:**
- [ ] 更新 `SKILL.md` 添加章節：
  - [ ] "故障排除" 章節
  - [ ] AI 如何處理錯誤的指導
  - [ ] 如何查詢和解讀筆記

- [ ] 創建 `TROUBLESHOOTING.md`
  - [ ] 常見錯誤及恢復步驟
  - [ ] 錯誤代碼參考

**文件變更:**
- `SKILL.md` - 更新
- `TROUBLESHOOTING.md` - 新建

---

## 🔧 實現細節

### 文件變更清單

#### 1. `scripts/usage_logger.py` (修改)
```python
# 添加 log_error() 方法
def log_error(self, input_text, operation, error_msg, exit_code, suggestion=None):
    """記錄操作失敗"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'input': input_text,
        'operation': operation,
        'success': False,
        'error': {
            'message': error_msg,
            'exit_code': exit_code,
            'suggestion': suggestion
        }
    }
    with open(self.error_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

# 添加 get_last_errors() 方法
def get_last_errors(self, limit=10):
    """返回最近的 N 個錯誤，供 AI 查詢"""
```

#### 2. `scripts/error_handler.py` (新建)
```python
# 定義常見的 git 錯誤類型
GIT_ERRORS = {
    'GIT_PUSH_REJECTED': {
        'pattern': 'Updates were rejected',
        'message': '遠端有更新，本地提交被拒',
        'recovery': ['git pull --rebase', 'git push']
    },
    'GIT_MERGE_CONFLICT': {
        'pattern': 'CONFLICT',
        'message': '合併衝突',
        'recovery': ['git status', '手動解決衝突', 'git add .', 'git commit']
    },
    # ... 更多錯誤類型
}

class ErrorHandler:
    def identify_error(self, error_output):
        """識別錯誤類型"""
    
    def get_recovery_steps(self, error_code):
        """返回恢復步驟"""
    
    def format_for_ai(self):
        """格式化供 AI 閱讀"""
```

#### 3. `scripts/operation_notes.py` (新建)
```python
class OperationNotes:
    def __init__(self):
        self.notes_dir = Path.home() / '.git-ops' / 'notes'
        self.notes_dir.mkdir(parents=True, exist_ok=True)
    
    def add_note(self, operation, input_text, result, details=None):
        """添加操作筆記"""
    
    def format_daily_notes(self):
        """生成每日筆記摘要"""
```

#### 4. `scripts/git_ops.py` (修改 render 函數)
在生成的 bash 腳本中添加錯誤處理:

```bash
# 生成的腳本應該包含:
set -euo pipefail

trap 'on_error $? $LINENO' ERR

on_error() {
    local exit_code=$1
    local line=$2
    echo "❌ Git operation failed at line $line with exit code $exit_code" >&2
    
    # 捕捉當前 git 狀態
    git status >> ~/.git-ops/error_context.log 2>&1 || true
    
    # 記錄錯誤到日誌
    # ... 錯誤日誌記錄邏輯
    
    exit $exit_code
}

# ... 實際的 git 操作
```

---

## 📊 成功指標

**Phase 1 完成後:**
- ✅ 所有操作錯誤都被記錄到 `~/.git-ops/errors.jsonl`
- ✅ AI 可以查詢 `~/.git-ops/error_summary.md` 快速了解失敗
- ✅ 常見的 git 錯誤都有恢復建議
- ✅ 錯誤率和恢復率可統計

**Phase 2 完成後:**
- ✅ 所有操作都在每日筆記中有記錄
- ✅ AI 可以查看 `~/.git-ops/notes/YYYY-MM-DD.md` 追蹤歷史
- ✅ 筆記包含操作前後的 git 狀態

**Phase 3 完成後:**
- ✅ SKILL.md 包含完整的故障排除指南
- ✅ AI 有清晰的使用指導

---

## 🎯 AI 使用工作流

實施完成後，AI 的工作流將是：

```
用戶要求: "幫我 push 代碼"
    ↓
AI 呼叫: python3 scripts/git_ops.py commit -m "..." --push
    ↓
git-ops 生成並執行 bash 腳本
    ├─ 如果成功 → 記錄到 notes 和 usage.jsonl
    └─ 如果失敗 → 記錄到 errors.jsonl，包含恢復建議
    ↓
AI 檢查結果:
    ├─ 檢查 ~/.git-ops/error_summary.md (如果失敗)
    ├─ 閱讀恢復建議
    └─ 自動執行恢復步驟或提示用戶
    ↓
操作記錄在 ~/.git-ops/notes/ 供審計和調試
```

---

## 📝 注意事項

1. **向後兼容性** - 所有改進都應該是附加的，不破壞現有的 API
2. **性能** - 錯誤日誌不應該減慢 git 操作
3. **隱私** - Notes 和錯誤日誌應該只保存在本地用戶目錄
4. **清理策略** - 考慮自動清理舊的日誌（例如超過 30 天）

