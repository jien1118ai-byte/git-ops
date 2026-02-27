 📅 Git-Ops 專案強化與發展 Roadmap (2026-02-27)



 📊 現況審計摘要 (Status Audit)

  * 優點：零 Token 成本、Regex 高效解析、生產級安全預檢、雙語支援、自動學習別名系統。

  * 已解決：Regex 語意容錯低（LLM Fallback）、| bash 操作冗餘（內建執行器 -x）、複雜衝突處理薄弱（Decision Engine + Conflict Detector）。

  * 待改善：LLM commit message 生成、教練模式、CI/CD 整合。



 ---



 🚀 短期：用戶體驗與穩定性優化 (High Priority)

 > 目標：消除操作摩擦，提升解析容錯率。



  - [x] [UX] 實作內建執行器模式 (Built-in Executor) ✅ 2026-02-26

      - [x] 修改 gops 邏輯，支援直接執行而非僅輸出字串。

      - [x] 實作 [Y/n] 互動確認介面。

      - [x] 移除對 | bash 的強烈依賴，簡化指令為 gops "stash" -x。

  - [x] [NLP] 建立 Hybrid 解析架構 (Fallback Mechanism) ✅ 2026-02-27

      - [x] 在 git_ops.py 加入本地 LLM (Ollama qwen2.5:3b) 調用介面。

      - [x] 邏輯設定：當 Regex 全部未匹配時，自動觸發 LLM 解析意圖。

      - [x] 安全設計：op 白名單、參數白名單、shell 字元過濾。

  - [x] [Robustness] 強化衝突引導系統 (Conflict Recovery) ✅ 2026-02-12

      - [x] 整合 Decision Engine 偵測 Git 衝突狀態。

      - [x] 實作當指令失敗時，主動提供「下一步白話操作建議」。

  - [ ] [Command] 建立與新增至 CLAUDE 的 command "git-ops"



 ---



 💡 中期：功能擴展與 AI 協作 (Medium Term)

 > 目標：讓工具從「翻譯機」進化為「開發助手」。



  - [x] [AI] 自動化 Commit Message 生成（部分完成）

      - [x] 撰寫讀取 git diff 暫存區內容的模組（commit_log 功能）。

      - [x] 撰寫 log 大綱（auto_log stat 格式）。

      - [x] 如果是解 Bug 要有 root cause（root_cause 欄位）。

      - [ ] 串接 LLM 依照 Conventional Commits 格式自動撰寫訊息。

  - [x] [Team] 團隊工作流守門員 (Workflow Guardrails) ✅ 2026-02-25

      - [x] 擴充 git-ops.yml 支援強制的命名規範（如 feat/, fix/）。

      - [x] 實作「開始任務 (Start Task)」複合指令（workflow create-feature）。

  - [ ] [Education] 實作「教練模式 (--explain)」

      - [ ] 在執行指令時同步輸出該操作的白話原理說明。



 ---



 🏗️ 長期：企業級價值與自動化 (Long Term)

 > 目標：整合 CI/CD 與程式碼健康度。



  - [ ] [Safety] Pre-push 智能預檢

      - [ ] 在執行 push 指令前，自動執行本地 Linter 或 Unit Test。

  - [ ] [Scaling] 團隊「指令食譜 (Recipes)」分享系統

      - [ ] 支援從遠端 URL 加載團隊共用的 custom_patterns。

      - [ ] 實作 gops update-rules 同步團隊最新規範。



 ---



 📝 已完成任務記錄 (Completed)

  - [x] Task 1: 內建執行器 (-x/-y/--print) ✅ 2026-02-26
  - [x] Task 2: LLM Fallback (Ollama qwen2.5:3b) ✅ 2026-02-27
  - [x] Task 3: 更新 README.md v2.0 ✅ 2026-02-26
  - [x] 7 項 IMPROVEMENT_PLAN 功能全部完成 ✅ 2026-02-25
