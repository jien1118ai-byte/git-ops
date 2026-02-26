# Git-Ops Skill 分析摘要

## 🎯 核心問題

AI 呼叫 git-ops 執行操作失敗時，目前**無法自動捕捉和記錄錯誤信息**。

### 現狀問題
```
用戶: "幫我 push"
↓
AI 呼叫 git-ops
↓
執行失敗 ❌ "Updates were rejected"
↓
AI 不知道發生了什麼 ❌
記錄系統沒有詳細信息 ❌
無法自動恢復 ❌
```

---

## 💡 三大改進方案

### 1️⃣ **結構化錯誤日誌** (最重要)
**當前:** `usage.jsonl` 只記錄 `success: true/false`  
**改進:** 創建 `errors.jsonl` 記錄完整錯誤信息
```json
{
  "timestamp": "2026-02-12T05:59:23Z",
  "operation": "push",
  "error": "Updates were rejected",
  "error_code": "GIT_PUSH_REJECTED",
  "exit_code": 1,
  "recovery": "git pull --rebase && git push",
  "context": {...}
}
```

### 2️⃣ **AI 可讀的 Notes 系統** (追蹤历史)
**文件位置:** `~/.git-ops/notes/YYYY-MM-DD.md`
```markdown
## 05:59:23 - commit 'fix' and push
Status: ✅ SUCCESS / ❌ FAILED
Error: (如果有)
Recovery: (如果有)
```

### 3️⃣ **Bash 腳本增強** (自動捕捉)
生成的腳本包含 error trap:
```bash
trap 'on_error $? $LINENO' ERR
on_error() {
  # 自動記錄錯誤到 ~/.git-ops/errors.jsonl
  # 提供恢復建議
}
```

---

## 📊 改進清單

| 優先級 | 項目 | 文件 | 說明 |
|--------|------|------|------|
| 🔴 高 | 增強 UsageLogger | `scripts/usage_logger.py` | 支持詳細錯誤記錄 |
| 🔴 高 | ErrorHandler 類 | `scripts/error_handler.py` (新) | 識別和建議恢復步驟 |
| 🔴 高 | 修改 render 函數 | `scripts/git_ops.py` | bash 腳本添加錯誤處理 |
| 🟡 中 | OperationNotes 類 | `scripts/operation_notes.py` (新) | 每日筆記記錄 |
| 🟢 低 | 更新文檔 | `SKILL.md`, `TROUBLESHOOTING.md` (新) | 故障排除指南 |

---

## 🔄 AI 呼叫流程（改進後）

```
用戶: "幫我 push"
↓
AI 呼叫: python3 scripts/git_ops.py push
↓
git-ops 生成 bash 腳本（含 error trap）
↓
執行腳本
  ├─ ✅ 成功 → 記錄到 usage.jsonl 和 notes
  └─ ❌ 失敗 → 記錄到 errors.jsonl + notes，包含恢復建議
↓
AI 檢查結果:
  - 查看 ~/.git-ops/error_summary.md
  - 閱讀恢復建議
  - 自動執行恢復或提示用戶
↓
所有操作都在 notes 中有記錄供審計 ✅
```

---

## 📁 新增的文件結構

```
~/.git-ops/
├── usage.jsonl           (現有) - 所有操作日誌
├── errors.jsonl          (新) - 詳細錯誤日誌
├── error_summary.md      (新) - 錯誤摘要（AI 可讀）
├── notes/                (新) - 每日操作筆記
│   ├── 2026-02-12.md
│   └── 2026-02-11.md
└── patterns.txt          (現有) - 使用模式
```

---

## ⏰ 實施時間表

**Phase 1 (立即):**  
✅ 錯誤日誌系統 - 2-3 天工作量

**Phase 2 (之後):**  
✅ Notes 系統 - 1-2 天工作量

**Phase 3 (最後):**  
✅ 文檔更新 - 1 天工作量

---

## 🎯 最終效果

實施完成後，git-ops skill 將能夠：

1. ✅ **自動記錄** - 所有操作（成功或失敗）都自動記錄
2. ✅ **智能診斷** - 識別常見的 git 錯誤並建議恢復
3. ✅ **AI 友好** - 生成結構化的錯誤報告供 AI 判斷
4. ✅ **可審計** - 完整的操作歷史在 notes 中
5. ✅ **自恢復** - 對常見錯誤可以自動執行恢復步驟

---

## 📌 用戶體驗改進

### 改進前
```
用戶: 幫我 push
Claude: ❌ 失敗了，但我不知道為什麼
用戶: 你再試一次？
Claude: ❌ 還是失敗
(陷入無限循環或需要用戶手動診斷)
```

### 改進後
```
用戶: 幫我 push
Claude: ⏳ 執行中...
        ❌ 失敗：遠端有更新，拒絕推送
        💡 建議：git pull --rebase 然後再推
        ↪️ 自動執行恢復... 
        ✅ 成功！已推送到 origin/main
用戶: (完全自動，無需手動干預)
```

---

## 📞 後續行動

1. **檢查分析:** 查看 `/home/janes/.copilot/session-state/.../analysis.md` 了解詳細問題
2. **查看計畫:** 查看 `/home/janes/.copilot/session-state/.../implementation-plan.md` 了解實施細節
3. **準備開始:** 當準備好時說 "開始實施" 或 "從 Phase 1 開始"

