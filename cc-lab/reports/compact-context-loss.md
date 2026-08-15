# [project] [subsystem] session — 30 个 compact 后的上下文损失与"反复大转"核查

- 日期: 2026-08-15
- 会话: `[session]`（`D--[user]-[project]`，worktree `[lane]`）
- 数据源: `~/.claude/projects/D--[user]-[project]/[session]-….jsonl`（75,809 条 entry）
- 问题: 该会话迭代了 **30 个 compact 轮次**，怀疑多次 compact 后丢失背景信息导致反复大转（重复重做已完成的工作）。

## 结论（一句话）

**部分证实，但机制比"丢了背景导致重做"更精确：compact 确实逐次丢弃了源码上下文，agent 每次都把正在改的整份源码文件从磁盘重读一遍来重新定位（这是实打实的上下文税），但它并没有"重做已完成的大块工作"——08-12 一天 463 次编辑是拆分 800+ 行 `[src].py` 的**成功硬重构**，最终把主文件压到 180 行、拆成 5 个模块，是前进不是回归。**

## 30 个 compact 的轮廓

30 个"session is being continued"（compact 摘要插入点）跨度 **08-07 15:13 → 08-15 01:43，共 8 天**，每窗口约 1.1k–4.0k 条 entry。与会话 6 天 27,095 轮、cache_read 前缀涨到 800k 的既有结论吻合——DeepSeek 约 1M 上下文几乎不自动压缩，这 30 次大多靠手动 `/compact` 触发。

## 三个实测发现

### 1. compact 后 agent 不是靠读 .md/计划/记忆来重定向，而是重读"正在改的源码文件"

- 全会话 tool_use 14,393，Read 占 14%；其中 .md/plan/memory/note 等"上下文文件"的读取只占 Read 的 **4%**，多数窗口 compact 后前 80 个工具调用里上下文读取为 0–2。
- 但这个项目把状态放在**代码里而不是 .md 计划里**。真正被反复重读的是**源码本身**：对 `[src].py`，**每一个碰过它的窗口都以 `Read` 该文件开头**（w14–w30 共 13 个窗口全是 Read-first，仅 w13 是 Write-first=文件刚被拆分创建）。

  | 窗口 | 首次动作 | 时间 |
  |------|---------|------|
  | w13 | Write | 08-12T00:54（拆分开始） |
  | w14 | **Read** | 08-12T08:31 |
  | w15 | **Read** | 08-12T11:28 |
  | w16 | **Read** | 08-12T15:20 |
  | w17 | **Read** | 08-12T18:06 |
  | … | Read | …直到 w30 |

  08-12 一天 5 次 compact，每次窗口一开就整份重读该文件。单次不压缩的会话你只会读一次、之后靠内存改；这里 13 个窗口各读一次，正是 compact 把文件内容逐出上下文、被迫从磁盘重购的迹象。

### 2. 编辑量大 ≠ 重做。每窗口 distinct 区域数很高，是前进式展开

- `[src].py` 全会话 517 次 Edit，**463 次集中在 08-12 单日（w13–w17，00:54→20:01）**。
- 但每窗口 distinct 区域数很高：w14 `128 edits → 104 distinct`、w15 `119 → 90`、w13 `87 → 62`。即窗口内改的是大量**不同**代码区，不是反复改同一两行。
- 大量"被重复替换的 old_string"（`@pytest.mark.matlab` ×11、`if ctype=='switch':` ×10、`def _transformer_blocks` → `def _pwm_source_blocks` …）是**块级重构的锚点**——agent 用同样的起始行反复调整一大块内容（拆分、改名、扩参），不是把同一改动撤销重做。

### 3. 拆分收敛了，晚窗口是在加新测试而非重做旧的

- git 历史 08-12 正是 `refactor([subsystem]): split the Simscape circuit exporter`（`[commit]`）。实测主文件从 800+ 行降到 **180 行**，拆成 `[src]{,_blocks,_case,_job,_wiring}.py` 5 个模块。**大转收敛成了更好的结构。**
- 晚窗口 w27–w30（08-14→08-15）的编辑是**新增测试**：`test_builder_emits_a_[feature]`、`test_builder_emits_a_[feature]`、`test_builder_emits_a_[feature]`、`test_builder_emits_a_[feature]`。同一段 `def test_builder_emits_the_solver_and_measurement_chain()` 被替换 ×4 是因为它被当模板复制改名成新测试。

## 唯一真实的"反复"：w29 的 test-tier 抉择抖动（与 compact 无关）

w29（08-14T22:14→22:50，36 分钟内）agent 把 live-MATLAB 测试的 `parametrize('case_dir', [...])` 列表连续增删 6+ 次（`case_a` / `case_b` / `case_c` 加进来又撤掉）。这是**工作流级**抖动——live MATLAB 测试有的跑不通/超时，agent 在编排哪些 case 能进这一档——不是 compact 造成的上下文丢失。

## 判定

- **上下文损失是真实且可测量的**：每 compact 后重读整份源码文件来重定位（13 个窗口各 Read 一次大文件），这是压不住的"重购上下文"成本，与兄弟会话 §3b 的"重读同一区域"同源。
- **但"反复大转=重做已完成的工作"不成立**：没有把已完成子系统推倒重来，而是硬重构 + 增量加测试，且最终收敛。
- 真正让这里烧钱的是 token 报告那套放大器：DeepSeek 大上下文不自动压缩 → 手动 compact → 又在 600–800k 前缀上重读整份文件。compact 没能让"重购"变便宜，只是换了个名义。

## 建议

1. **一个逻辑任务开一个新 session / `/clear`，而不是在同一条巨型会话里压 30 次 compact**。跨逻辑阶段的上下文靠代码 + git 留存，不靠把一条会话续 8 天。
2. **把稳定状态写进一个小 state/scratchpad 文件**，agent 写一次、每次重定向只读它（一个小文件），而不是重读整棵源码树。项目已有的 `recall.py` pin（`output/recall/`）只针对指定文件/行区，可扩成"每窗口首动作"的状态恢复入口。
3. token 报告的护栏仍适用：自主循环设 `maxTurns`/`timeoutMs`，别让一条会话无监督跑 8 天。

## 复现

```text
.scratch/{story,analysis,rework,edits,late}.mjs   ← 一次性分析脚本（gitignored）
node scripts/analyze-session.mjs --dir <projectsDir> --session [session]
```

## 附注

`recall.py`（`scripts/repo/recall.py`）只是把本仓库的 pin store 绑定到 `agent_swarm.pins`（`output/recall/` 是带失效键的缓存），是 PostCompact 的轻量钩子，不是完整状态恢复——所以别指望它抵消上面的整文件重读。
