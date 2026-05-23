# auto-evo 升级施工图 — 引入 claude-dispatch 的优点

> 这份文档同时是「架构设计」和「给 Claude Code 看的分 Phase 施工图」。
> 目标：把 claude-dispatch 里验证过的几个好设计，移植进 `auto-evo`（背后的 `claude-code-247` 自进化系统），且全程保持纯 GitHub 原生架构。
> 施工方必须严格按 Phase 顺序推进，每个 Phase 不过验收不进下一个。

## 0. Mission

claude-dispatch 是人触发、单任务、本地 tmux 编排的「调度器」；auto-evo 是机器自驱、24/7、GitHub 原生的「自进化引擎」。本次升级把 dispatch 的 4 个长板移植进 auto-evo：

1. **行为准则全局生效**：引入 Karpathy 四条（Think Before / Simplicity / Surgical / Goal-Driven）作为根目录 CLAUDE.md，外加针对自进化场景的纪律，让每个在 Actions 里运行的 Claude job 自动加载。
2. **多 Agent 协作 + 任务分解**：把 dispatch 的 Orchestrator → Code Worker / RW Worker 角色分工，映射到 GitHub 的 调度 workflow → worker job → 分支/PR 上。
3. **异源验证（核心长板）**：引入 Gemini 2.5 Pro 作为独立裁判，只看行为契约 + worker 自述 + 输出文件清单 + 测试结果，永不看源码，作为 PR 合并前的强制门禁。
4. **反馈闭环优化**：在不离开 GitHub Actions 的前提下，用快慢双车道把"这轮改动行不行"的判定从分钟级压到约 1 分钟。

外加安全要求：带护栏的安全 auto-merge（PASS + CI 绿自动合并，main 不 deploy，配一键回滚 + 每日摘要）。

## 1. 已锁定的设计决策（不可擅自更改）

- 编排载体：纯 GitHub Actions 驱动，schedule cron 当心跳，无常驻进程。
- 验证模型：Gemini 2.5 Pro，作为 Actions 里的 job，复用 google-genai，异源于生成方 Claude。
- 反馈速度：放弃秒级，CI 内压到约 1 分钟。
- 本地预验证：不允许，一切验证只在 Actions 里跑。
- 仓库可见性：保持 public，因此采用最严信任边界隔离（见 §3）。
- Claude 运行方式：在 Actions 里跑（官方 Claude Code Action / claude CLI headless）。
- 合并策略：带护栏的安全 auto-merge，靠 Git 可回滚 + main 不 deploy 兜底。
- CLAUDE.md：四条为核心 + 自进化纪律若干。

⚠️ 残余风险：public 仓库 + API key 放 Secrets + 会自己写代码的 agent，是中等偏高风险组合。用 §3 信任边界把风险降到工程可接受，但无法降到零。最关键不可消除项：持有 ANTHROPIC_API_KEY 的 worker job 会运行 Claude，理论上能读到同 job 的 key。靠"该 workflow 只能被受信任调度器触发 + key 定期轮换 + 最小权限"压住。

## 2. 目标架构（GitHub 原生控制平面）

dispatch 进程层 → auto-evo GitHub 层 的映射：

- dispatch "task" 启 Orchestrator → schedule cron 触发 orchestrator.yml（心跳）
- task.md → GitHub Issue（带 `agent:queue` 标签的任务队列）
- tmux window = 一个 worker → 一个 worker job（workflow_dispatch 触发）
- flock 写锁串行 → 同一 `shadow/issue-<n>` 分支天然串行；不同 issue 并行
- events.jsonl → Git 历史 + Issue/PR 评论 + workflow run 日志
- validator/validate.py（本地）→ validator.yml（Actions 里调 Gemini）
- verdict.md → PR 上的 commit status / check：`heterologous-validation`
- WebUI + 推送 → GitHub 原生 PR/Checks UI + 每日摘要 Issue + 可选 ntfy
- watchdog → schedule 巡检 workflow + 卡死告警

### 2.1 端到端时序

`[schedule cron 心跳]` → `orchestrator.yml`：
1. 先检查 kill-switch（仓库 variable `AGENT_FROZEN`），冻结则退出
2. 读 open issues（label=`agent:queue`）挑一个未在进行的（队列空则自进化：读 roadmap/telemetry → 开新 issue → 退出本轮）
3. 建分支 `shadow/issue-<n>`
4. 调 Claude（仅规划工具，无 Bash 执行）写 `plan.md` + `contract.md`，commit 到分支
5. 给 issue 打 `agent:in-progress`，评论 plan
6. 按 plan 顺序逐个 workflow_dispatch 派 worker：code worker(opus) 串行、rw worker(sonnet) 可并行

`worker.yml`（每个 worker 一次 run）：在 shadow 分支上跑 Claude Code，写代码/文档，写 `workers/<name>/done.md`（产出物 + 怎么测），commit & push 到 shadow 分支。

`shadow-ci.yml`（push 到 `shadow/**` 自动触发，无 secret）：快车道 lint + 变更路径单测(~1min)；慢车道 integration + coverage（并行，不阻塞快车道判定）。

orchestrator 检测 workers 全部 done → 开 PR(shadow→main) → 触发 `validator.yml`。

`validator.yml`（持 Gemini key，只读证据不跑代码）：收集 `contract.md` + `done.md` + 文件清单 + 测试结果 → 调 Gemini 2.5 Pro → 写 verdict 到 PR 评论 + 设 check `heterologous-validation`=PASS/FAIL。

`auto-merge.yml`（监听 check 完成）：`heterologous-validation==PASS` 且 shadow-ci 绿 → squash auto-merge 到 main，main 受保护永不 deploy，关闭 issue，移除 in-progress 标签。

`daily-digest.yml`（schedule 每日）：汇总当日合并/失败/队列 → 发到摘要 Issue。

## 3. 信任边界与安全模型（public 仓库的关键）

**铁律**：持有 secret 的 job，绝不执行 agent 写的（不可信）代码；执行不可信代码的 job，绝不持有任何 secret。

### 3.1 受信任控制面 workflow（持 secret）

`orchestrator.yml`、`worker.yml`、`validator.yml`、`auto-merge.yml`、`daily-digest.yml`。
触发只能是 schedule / workflow_dispatch / push 到受保护分支，绝不能是 fork 来的 pull_request。骨架代码（`orchestrator/`、调用脚本、`.github/workflows/**`）是人写的受保护代码。`.github/workflows/**`、`orchestrator/**`、`CLAUDE.md` 全部纳入 CODEOWNERS，分支保护要求人工 review。agent 被明令禁止改这些路径。

### 3.2 不可信构建/测试 workflow（无 secret）

`shadow-ci.yml`：跑 agent 写的代码（lint/pytest），permissions 收到最小（`contents: read`），env 里不放任何 secret。即使 agent 写出恶意/有 bug 测试也偷不到 key。

### 3.3 三个持密 job 的安全姿势

- **`validator.yml`（持 Gemini key）**：只读文本证据 + 调 Gemini API，从不 checkout 或执行 PR 代码。异源验证天然安全红利。
- **`worker.yml`（持 Anthropic key，最敏感）**：必须运行 Claude。缓解：
  1. 只能被 orchestrator 通过 workflow_dispatch 触发
  2. key 用 fine-grained、最小 scope、定期轮换
  3. CLAUDE.md 约束绝不外传环境变量/secret
  4. 跑完整测试套件交给无密的 shadow-ci.yml，worker job 里 Claude 只做最小本地自检
- **`orchestrator.yml`（规划阶段持 Anthropic key）**：调 Claude 写 plan/contract 时关闭 Bash/执行类工具，只允许写 `plan.md`、`contract.md`。

### 3.4 仓库一次性配置（Phase 0）

- Secrets：`ANTHROPIC_API_KEY`、`GEMINI_API_KEY`（建议放进 Environment 并设 required reviewers）
- 分支保护(main)：要求 PR、要求 `shadow-ci` 与 `heterologous-validation` 两个 check 通过、要求 `.github/`、`orchestrator/`、`CLAUDE.md` 改动经 CODEOWNERS
- 仓库 variable：`AGENT_FROZEN`（kill-switch，默认 false）
- 一个 fine-grained PAT (`AGENT_PAT`) 给 orchestrator 用来开 PR / 派 workflow

## 4. CLAUDE.md（放仓库根目录，全 job 自动加载）

内容（写进根目录 `CLAUDE.md`）：

```markdown
# Behavioral Contract — Recite on request. Apply before any non-trivial change.
## 1. Think Before Coding — State assumptions out loud before typing. If ambiguous or a path/library/API choice could go more than one way, name the choice and the alternative explicitly. Never silently pick.
## 2. Simplicity First — Write the minimum code that satisfies the requirement. No speculative features, no "while I'm in here" improvements, no premature abstractions.
## 3. Surgical Changes — Touch only what the task requires. Do not refactor neighboring code or reformat unrelated lines. Out-of-scope work belongs in a separate issue/PR.
## 4. Goal-Driven Execution — Before writing code, define what "done" looks like as a verifiable check. Then loop: implement → run the check → if it fails, diagnose and iterate. Never declare success without running the check.

# Self-Evolution Discipline（追加）
## 5. Stay on the Shadow Branch — 所有改动只能发生在 shadow/issue-<n> 分支。绝不直接 push main。
## 6. Never Touch the Control Plane — 绝不修改 .github/workflows/**、orchestrator/**、CLAUDE.md、CODEOWNERS、分支保护配置。发现问题只许在 PR 描述里 flag。
## 7. No Secret Exfiltration — 绝不读取/打印/外传任何环境变量或 secret。绝不写网络请求把环境变量发到外部。
## 8. One Issue, One PR, One Concern — 一个 issue 只解决一个关切，不夹带无关改动，contract 未 PASS 不算完成。
## 9. Contract Before Code — 写实现前先有 plan.md + contract.md，contract 只描述可观察行为，不含实现细节（库名/文件结构/算法）。
```

末尾：When asked "what behavioral rules are you operating under?", reply with the names of rules 1–4 plus a one-line gloss each.

## 5. 异源验证设计细节

复用 dispatch 的 `validator/validate.py` + `prompt.md` 思路，改造成 Actions job：

- **输入（证据，全是文本/清单，绝不含源码）**：
  - `contract.md`
  - `workers/*/done.md`
  - PR 文件改动清单（路径+字节数，不含内容）
  - shadow-ci 上传的测试结果产物（test-results、coverage 摘要）
- **裁判**：`gemini-2.5-pro`，prompt 开头声明 "You are an independent acceptance validator. You have NEVER seen the implementation source code and must not ask for it. Decide on behavioral evidence only."
- **输出**：第一行 `PASS` 或 `FAIL`；`---`；`Reasons:` 项目符号；FAIL 时附 `Remediation:`。写成 PR 评论，并通过 GitHub Checks API 设 `heterologous-validation` 状态。
- **红线**：永远不准把改动文件内容塞进 prompt。validator job 不 checkout PR head 代码。

## 6. 红线（不可做）

- 让任何持 secret 的 job 执行 agent 写的代码
- 在 `shadow-ci.yml` 里放任何 secret
- 让 agent 修改 `.github/workflows/**`、`orchestrator/**`、`CLAUDE.md`、`CODEOWNERS`
- 把改动源码内容喂给 Gemini validator
- 把 Gemini 换成 Claude/OpenAI
- 直接 push main 或绕过 PASS 门禁合并
- 把验证搬出 GitHub Actions
- 跳过 Phase 验收直接进下一 Phase

## 7. 施工 Phase（每个 Phase 节奏：① 复读 CLAUDE.md ② 说计划+假设 ③ 写最小代码 ④ 跑验收 ⑤ 通过则 commit（控制面改动走人工 review 的 PR） ⑥ 失败则 loop）

### Phase 0 — 仓库安全基线
- 建 Secrets（`ANTHROPIC_API_KEY`、`GEMINI_API_KEY`）
- 建 fine-grained `AGENT_PAT`
- 建仓库 variable `AGENT_FROZEN=false`
- 写 `CODEOWNERS`（保护 `.github/`、`orchestrator/`、`CLAUDE.md`）
- 配 main 分支保护

**验收**：以 agent 身份改 `.github/workflows/x.yml` 的 PR 会被分支保护挡下；普通 push 到 main 被拒。

### Phase 1 — 引入 CLAUDE.md
把 §4 完整内容写进根目录 `CLAUDE.md`，commit（经人工 review）。

**验收**：worker job 里问 Claude "what behavioral rules are you operating under?" 能复述四条 + 自进化纪律存在。

### Phase 2 — 任务队列协议（Issues）
- 定义标签 `agent:queue` / `agent:in-progress` / `agent:done` / `agent:blocked`
- 写 ISSUE_TEMPLATE，要求每个任务 issue 含"目标 + 可观察验收标准"

**验收**：手工开一个带 `agent:queue` 的 issue，字段齐全。

### Phase 3 — orchestrator.yml（心跳+规划）
写 `.github/workflows/orchestrator.yml`（schedule + workflow_dispatch）和 `orchestrator/tick.py`：
1. 查 `AGENT_FROZEN` true 则退出
2. 取一个 `agent:queue` issue
3. 建 `shadow/issue-<n>` 分支
4. 调 Claude（禁用 Bash，仅允许写文件）产出 `plan.md` + `contract.md`
5. 打 `agent:in-progress` 评论 plan

**验收**：workflow_dispatch 手动触发一次，目标 issue 出现 plan 评论、新分支里有 `plan.md` + `contract.md`，且 contract 不含实现细节。

### Phase 4 — worker.yml（多 agent 执行）
写 `.github/workflows/worker.yml`（workflow_dispatch，inputs：issue/kind/name/subtask/branch）：
- code worker 用 opus
- rw worker 用 sonnet
- 官方 Claude Code Action，加载根 CLAUDE.md
- Claude 在 shadow 分支写代码/文档 + `workers/<name>/done.md` + push

orchestrator 增加派发逻辑：code 串行（轮询上一 run 完成）、rw 并行。

**验收**：对一个"写函数 + 写 README"的 issue，派出 2 个 worker，shadow 分支出现对应文件 + 两个 done.md。

### Phase 5 — shadow-ci 快慢双车道
改造 `shadow-ci.yml`：
1. 加 `concurrency: cancel-in-progress`
2. 快车道 job（lint + 变更路径单测，目标 ≤1min，用 paths 过滤 + pip 缓存）
3. 慢车道 job（integration + coverage，与快车道并行，不阻塞快车道结论）
4. 测试结果 `upload-artifact` 供 validator 取用

保持无 secret。

**验收**：一次 shadow push，快车道约 1 分钟内出结论；artifact 里有 test-results。

### Phase 6 — validator.yml（异源 Gemini 门禁）
移植 dispatch 的 `validator/`，包成 `.github/workflows/validator.yml`（由 orchestrator 在开 PR 后 workflow_dispatch，持 `GEMINI_API_KEY`，不 checkout PR 代码）：
- 收集 §5 证据
- 调 Gemini
- 写 PR 评论 + 设 `heterologous-validation` check

**验收**：造一个 contract 要求"含 README"但 outputs 故意没 README 的 PR → check FAIL 且指出缺 README；满足的 → PASS。

### Phase 7 — auto-merge.yml（带护栏合并）
写 `.github/workflows/auto-merge.yml`（监听 check_suite/workflow_run 完成）：
- `heterologous-validation==PASS` 且 shadow-ci 绿 → squash auto-merge → 关 issue、打 `agent:done`
- 确认 main 分支保护已要求这两个 check
- 确认 main 无任何 deploy 步骤

**验收**：一个 PASS 的 PR 自动合并；一个 FAIL 的 PR 停在原地不合并。

### Phase 8 — kill-switch + 一键回滚 + 每日摘要
1. `revert.yml`（workflow_dispatch 输入 commit/PR 号，或标签 `agent:revert-last`）→ `git revert` 最近一次 auto-merge 并直接合并
2. orchestrator 每轮开头读 `AGENT_FROZEN`，true 即全停
3. `daily-digest.yml`（schedule 每日）→ 汇总当日合并 PR / 失败 / 队列长度 / 卡住的 in-progress issue → 发到固定"摘要 Issue"（可选 ntfy）

**验收**：`AGENT_FROZEN` 置 true，心跳一轮不派 worker；跑一次 revert 能干净回滚上次合并；每日摘要 Issue 有内容。

### Phase 9 — 巡检 watchdog + 端到端冒烟
1. `watchdog.yml`（schedule）→ 找超阈值仍 `agent:in-progress` 的 issue / 长时间没动的 shadow 分支 → 评论告警 + 打 `agent:blocked`
2. 端到端冒烟：手工开一个"实现 mathx 的 add/mul + pytest"的 queue issue，跑完整链路，断言最终 PR 被 validator PASS 并 auto-merge

**验收**：冒烟全程通；新人只读本文 + README 能看懂整条流水线。

## 注意

- Phase 0 里涉及 GitHub 仓库设置（Secrets / 分支保护 / variable / PAT）有些需要在 GitHub 网页或通过 `gh` CLI 操作。凡是需要真实 API key 或需要在 GitHub 控制台手动设置的步骤，遇到时停下来明确告诉用户「这一步需要你手动做什么」，给出精确的 `gh` 命令或网页操作清单，不要伪造/跳过。
- 全程产出真实可执行的 workflow，能 act/本地 dry-run 验证的就验证。
- 每完成一个 Phase 验收，停下来向用户汇报「做了什么 + 验收结果」，再继续下一个 Phase。
