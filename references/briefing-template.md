# briefing — <待填：任務名稱>（Orca <待填：single／collab>）

> 發起：<待填：operator agent／model／session>
> 指揮鏈：<待填：manager> → operator → <待填：single worker／orchestrator → implementer＋verifier>
> 共用工作目錄：`<待填：絕對路徑>`
> 目標 repo：`<待填：絕對路徑與 branch／base>`

## 你是誰

<待填：本席角色、誰持有技術判斷、誰只守意圖 gate。collab 時明寫 operator 不做技術拆解、不派第二層；verifier 可判定任務本身問錯。>

## 任務

<待填：一段話說清楚問題、可觀察結果、基線數字>

## 角色與席位

| 席 | 誰 | 啟動方式 | 職責 |
|---|---|---|---|
| operator | <待填> | 已在跑 | 意圖 gate、獨立驗收、生命週期收尾 |
| orchestrator／single worker | <待填> | `orca orchestration worker-start ...` | <待填> |
| implementer（collab） | pi `<待填 model>` | 兩步：`orca terminal create --worktree current --command "pi --model <待填> --thinking <待填>" --json`，TUI 就緒後以 `worker-start --terminal <handle>` 收編；巢狀關閉時改 B 路線 | 實作與 findings |
| adversarial-verifier（collab） | Claude Fable | `worker-start --agent claude --model <待填 Fable model> ...`；B 路線則 terminal create＋send | 換口徑複驗、挑錯 |

## 硬約束

- <待填：不可動路徑、API／額度、時間與 runtime 限制>
- <待填：git add／commit／push／merge 權限>
- 測試安裝器只用暫存 HOME／輸出目錄；不碰真使用者狀態。
- 不以 timeout 或 `unverifiable` 當成退出證據。
- 長內容落 findings／review；訊息只帶結論與路徑。

## 檔案所有權

| 檔案／repo | 誰改 |
|---|---|
| <待填> | <待填> |
| `<workdir>/findings-worker-*.md` | <待填> |
| `<workdir>/review-*.md` | verifier |
| git commit／push／merge | <待填：逐項寫 owner 或沒有人> |

## 驗收

### 實作產物（可重跑）

1. <待填：真實測試指令＋基線／預期數字>
2. <待填：紅綠變異、diff 範圍、狀態清單>
3. <待填：每項如何證明沒有碰真 HOME／runtime>

### 複驗產物（換口徑，不得只重跑實作者指令）

1. <待填：獨立 fixture／邊界案例／實機限制>
2. <待填：逐句越界掃描或失效模式>
3. <待填：任務與 briefing 本身的反例>

## 回報格式

每席回三樣：結論一句、證據路徑或原始輸出、對方／任務書哪裡錯。明示 `succeeded` 或 `failed`；問題用 typed `question`，不用互動式提問工具。

## 意圖 gate

命中任一項，operator 取得使用者裁決後才繼續：

- 改變日常預設、模型、routing 或排程
- 刪除／覆蓋非本次產物
- push、PR、通知、邀請等對外動作
- 合併 main 或未授權 worktree 處置
- <待填：任務特有 gate>

## 收尾

- 處理整批訊息後 ack。
- 每個 dispatch release／retain／reuse 三選一；retain 寫理由與期限。
- `worker-list --terminal-state reclaimable` 回 0。
- <待填：主管殼與 worktree 處置權限>。
- 知識沉澱由 operator 做。
