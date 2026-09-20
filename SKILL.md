---
name: orca-collab
version: 0.1.1
description: 用 Orca 編排可追蹤、可驗收的隔離工作。當用戶說「用 Orca 派」「用 Orca 開三席」「Orca 現況」「你當 operator」時使用。不適用於：herdr 內的對等協作（用 herdr-collab），以及不需要隔離 worktree 的小改動。
---

# orca-collab — Orca operator 流程

> 操作細節先讀 `references/playbook.md`。Orca 指令旗標細節以 `orca skills get orchestration` 為準，本 skill 只固定流程與紀律。本 skill 的使用者是 **operator**：持有最外層 Run、守意圖 gate、驗收與收尾；技術拆解由 worker 或 orchestrator 負責。

## 前置與模式選擇

先跑：

```bash
bash <本 skill 目錄>/scripts/preflight.sh --repo <目標 repo>
```

- **single**：一個範圍明確的 worker 足以完成；operator 直接派 worker。
- **collab**：需要實作、獨立複驗與技術整合；operator 只派一名 orchestrator，第二層席位由 orchestrator 管理。

可用 `scripts/bootstrap.py --topic <slug> --repo <path> --mode single|collab` 建立 briefing 骨架及列出下一步指令。operator 填的是原始需求、硬約束、所有權、可觀察驗收與意圖 gate，不替技術角色預寫答案。

## Single 模式

1. **Preflight**：確認 runtime ready、揭露目標 repo 狀態、必要 CLI 可用；dirty repo 會警告工人看不到未提交改動但不阻擋，額度工具不存在可 SKIP，額度 decision 不是 `allow` 就不開席。
2. **登錄 repo**：未登錄才執行 `orca repo add --path <abs-path> --json`。
3. **主管殼與 Run**：在目標 worktree 建 operator shell，再 `run-create`。
4. **派工**：用五欄任務書（Target／Change／Constraints／Ownership／Observable acceptance）啟動一名 worker；single 模式由 operator 兼寫 spec，collab 模式則由 orchestrator 寫 spec。首次卡信任框，依 playbook 處理。失敗後重派必使用原 task 與 `--retry-of`，不可另造重複工作。
5. **等回報**：用 `scripts/orca-wait.sh` 包裝 `check --wait`。只處理 question、escalation、worker_done；空回是 checkpoint，不代表 worker 已死。
6. **獨立驗收**：operator 自己看 diff、重跑真實驗收，不採信 worker_done 裡的數字。
7. **簽收與收尾**：處理整批訊息後 ack；每個 settled dispatch 明確 release 或 retain，再處置 worktree。

## Collab 模式

1. 跑 preflight，並用 bootstrap 建 briefing 骨架。
2. operator 填原始任務、硬約束、檔案所有權、實作產物與**換口徑**複驗產物、回報格式及意圖 gate；verifier 的實測題必須明寫進 briefing 的複驗產物。
3. 建主管殼與 Run，只派一名 orchestrator。operator 不自行派第二層。
4. orchestrator 決定技術拆解、派 implementer 與 adversarial verifier，並整合分歧。orchestrator 若遇到 Orca 禁止巢狀 worker，按 playbook 的 B 路線使用終端機直驅與 typed message。
5. operator 平時不介入，只在 question、escalation、worker_done 到達時處理；命中 gate 才代表使用者裁決。
6. operator 對 orchestrator 的最後產物做獨立驗收，而不是把三席回報互相加總當證據。

### 意圖 gate

以下任一項必須停下取得使用者裁決：

- 改變日常預設、工具選型、模型、routing 或排程
- 刪除或覆蓋非本次產物
- 發布、push、PR、通知、邀請等對外動作
- 合併 main 或處置未授權 worktree
- briefing 明列的任務特有 gate

## Operator 不做的事

- 不把自己的技術判斷寫進 briefing 當成前提。
- collab 模式不自己派第二層席位；那是 orchestrator 的責任。
- 不替 orchestrator 決定具體措辭、架構或測試方法。
- 不信 worker_done 的測試數字；必須自己重跑並檢查真實行為。
- 不以沒消息、逾時或 `unverifiable` 推論工人已退出。

## 收尾

1. 處理訊息後 ack delivery。
2. 每個 dispatch 明確 release 或 retain；retain 要寫理由與期限。
3. `worker-list --run <R> --terminal-state reclaimable --json` 必須回 0 個。
4. 關閉主管殼。
5. 依授權合併、保留或刪除 worktree；未授權不動。
6. wiki／handoff 等知識沉澱由 operator 做，不丟給 worker 或三席代寫。
