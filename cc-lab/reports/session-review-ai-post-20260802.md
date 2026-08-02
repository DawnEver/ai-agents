# ai-post session review — 2026-08-02 (two sessions, full history)

**Source.** Real user sessions under `~/.claude/projects/…/Sync-agents-ai-post/` — evidence
layer 2 (persisted jsonl), no tap/proxy on these runs. Deep-read of the *entire* transcript,
not just the struggle table.

| Session | Topic | entries | assistant turns | tool errors | struggles |
|---|---|---|---|---|---|
| `b2077a72` | agent-24x7-dev 文章（小红书/微信/知乎，双正文机制） | 1539 | 553 | 10 | 17 |
| `3189e129` | tone-chord-lab 文章（口琴校音工具，v1→v2→归档） | 2055 | 813 | 7 | 27 |

---

## Session 1 — agent-24x7-dev (`b2077a72`)

**Brief (open).** 写一篇「让 agent 7×24 迭代工作的方案」：主 Agent 维护动态 Plan
Dependency Tree（每个节点 Task_ID / Status / Context_Digest≤500 tokens / Follow_up_Ids），
goal 要求完成全部计划及 follow-up，为避免 main context 打满 → fan out subagents。

**User corrections along the way (the real arc):**
1. `[22]` 删虚构情节；「20× Claude Max 额度对一个大型项目开发（不提具体项目名）都不够用」；
   常态 1-3 个 subagent。
2. `[30]` 受额度限制只能用 1-3 个子 Agent，但**只要项目架构好、模块充分解耦、充分测试，
   完全能满足 scaling law** —— 这是文章的核心论点。
3. `[38→55]` 先写小红书；**别种草，要有活人感的经验分享，这篇要详细写**。
4. `[67]` **「使用已有工作流啊！」** —— 用户不满 Agent 没走 `/post-new`，直接点破。
5. `[260/292]` 更重经验与见解、不宣传、要真诚。
6. `[306]` 标题定为「Agent 时代，大型软件开发成为一个优化问题」。
7. `[362-396]` 并行 subagent 产出 Twitter / 小红书 / 微信公众号 / 知乎 v1。
8. `[529]` **核心批评**：「现在你被原来的模版整的过拟合了！连写一篇真诚的文章都不会了」——
   要求真诚表达原文 + 适当展开。这是整场最关键的转向。
9. `[618]` 用户给出**权威底本**（原则文档，非经验分享）要求以此为准则重写 —— 即 memory 里的
   `master-v4.md`（粘贴损坏片段按意图修复，修复处已标注核对）。
10. `[671]` **Twitter 砍掉**；小红书需包含细节：全文细节进最终图片卡，另放一版在正文，
   并**建立机制支持**（→ 双正文机制）。
11. `[835/845/909]` 三方会审；**「请仅仅使用 deepseek!」**（fabric 默认 Opus+DeepSeek+Codex
   被用户纠正为只用 deepseek）。
12. `[1155/1173/1229]` 发布阶段：保留 bullet row、用 markdown bullet——**「根本没有识别
   markdown bullet 换行！」**（gen_xhs_pages.py 分页 bug，用户强烈不满）。
13. `[1266]` 句号在行中央（对齐渲染问题）。
14. `[1347]` 标题改为「Agent时代，软件开发成了一个优化问题！」重生成 cover。
15. `[1369→1376]` 全部发布 → archive。

**Struggle 构成（17）**: edit-thrash 3（brief.md ×9、gen_xhs_pages.py ×3、v5/xiaohongshu.md ×5）、
repeated-command 2、long-stall 2、tool-error-repeat 1、bash-retry 3、permission-denial 6。
**fabric**：三方会审用 `fabric/call`，其中 2 次 >120s 被后台化 → `waits-on-fabric: 2`；
另 `tool-error-repeat`: *「deepseek-v4-flash[1m] is temporarily unavailable, so auto mode
cannot determine the safety of Bash right now」* —— 路由到的模型不可用会**连带卡住 auto
mode 的 Bash 权限判定**，这是 fabric 与 harness 交互的一个隐蔽坑。sharp-review 子代理一次被
`killed`（`[553]`）。

---

## Session 2 — tone-chord-lab (`3189e129`)

**Brief (open).** 用技能为 tone-chord-lab 写新文章：布鲁斯口琴校音工具。动机——新手练压音，
光靠耳朵判断不准音高是否落在目标音，需要校音；不想下 App，想做一个「在家开网页、路上手机
开」的轻量工具；一般校音只做单音、识别不了和弦，作为工科学生还想看实时频谱。

**User corrections along the way:**
1. `[218]` 加链接 `https://tone.mingyangbao.site/`。
2. `[236]` 重点讲用法：先点开麦克风再吹奏。
3. `[381]` 重点改为「不下载App，打开网页就给乐器校音」——口琴压音引入，但对所有乐器可用。
4. `[426]` 定标题：小红书「不下载App，打开网页就给口琴校音」；微信 WA1 去掉版；知乎 ZA2。
5. `[573/577]` 修正叙述逻辑与动机（补上走路用步伐当节拍器的细节）。
6. `[667]` **「小红书怎么全是短句子 不能长短句交错更有活人感吗?!」** —— 句子节奏/活人感批评。
7. `[696]` 用户手动加了桌面/手机截图，要求加进所有平台推文。
8. `[810/866]` 三方会审 + 加一两张原理图/架构图；**「仅仅使用 deepseek，不要另外两家」**。
9. `[913/932]` fabric fan_out 两个后台任务完成通知（`kieetrpq0`、`k1xgkcr9i`）——三方会审。
10. `[1018]` 标题改为「乐器校音」。
11. `[1046]` 更新图片描述、生成图；**codex 没额度了**，生成失败就用户手动生成。
12. `[1135]` 用户要详细 image 要求，自己生成。
13. `[1237]` `/post-publish`。
14. `[1412]` **小红书文字图片 emoji 渲染变大，全删并建立机制**（→ emoji 剥离进分页卡片）。
15. `[1490]` 所有 word 左对齐。
16. `[1526→1578]` archive，确认。
17. `[1760]` 处理 sharp-review 反馈，**再次强调真诚/活人感**。
18. `[2027]` commit。

**Struggle 构成（27）**: edit-thrash 12（brief ×9、各平台 v1/v2 ×多、templates/xiaohongshu.md ×6、
style/profile.md ×9）、repeated-command 2、long-stall 5、bash-retry 4、permission-denial 4。
**fabric**：三方会审 2 个 `fan_out` 均 >120s 后台化 → `waits-on-fabric: 2`。

---

## Cross-cutting patterns (both sessions)

1. **「真诚 / 活人感」是贯穿全场的主线，也是最耗用户的点。** 两个 session 各自都出现用户
   对 AI 腔/商业腔/短句堆砌的明确反感（agent-24x7 的「过拟合模版」、tone-chord 的「全是
   短句子」）。这与 memory `agent-24x7-dev-session.md` 的持久学习一致：先写真诚的第一人称
   复盘，再按平台落稿，不被模版公式牵着走。**Harness 含义**：若要做「写作风格」实验，这是
   唯一跨 session 可复现的干预变量（不是 fabric）。
2. **三方会审都用 deepseek-only，且都有 fabric 调用 >120s 后台化。** 用户主动把混合 provider
   默认（Opus+DeepSeek+Codex）纠正成只用 deepseek —— 说明 `post-review` 的默认 provider 配置
   与用户偏好不符。fabric `fan_out`/`call` 在 deepseek 上超过 120s 是常态（tone-chord 2/2、
   agent-24x7 2/若干 都后台化）。
3. **用户高频打断**（permission-denial 4+6）—— 用户是主动 co-pilot，边走边纠。这对 harness
   的 `waitIdle`/同步点设计有压力（被打断时不能当 idle）。
4. **发布/渲染环节是 bug 高发区**：markdown bullet 不换行、emoji 变大、句号居中对齐 ——
   都出在 `gen_xhs_pages.py` 的分页文字卡渲染。反复 edit 同一文件（edit-thrash）。
5. **sharp-review / rem 的 Stop-hook 频繁触发**，且 agent-24x7 有一次 sharp-review 子代理被
   killed。

---

## Fabric usage summary + harness changes (IMPLEMENTED this session)

见 `reports/fabric-fanout-async.md`。已落地到 `driver/`：

- **`driver/struggle.mjs`** 新增 `fabricToolWaits()` 检测器：fabric MCP 工具 >120s 后台化
  （`moved to the background as task X`）→ `fabric-wait` episode，按其 `<task-notification>`
  完成闭合；孤儿任务（完成通知永不出现）记为开区间 episode。默认从 struggles 排除
  （`opts.includeWaits` 保留），`summarize()` 新增 `waitsOnFabric` 计数。
- **`driver/driver.mjs`** 新增 `backgroundTaskPending()`，`waitIdle()` 用它：后台化 fabric 任务
  未完成前不判定 idle —— 避免在子代理等待 fabric 时提前发 send 造成丢/乱序。
- **`scripts/analyze-session.mjs`** 摘要行打印 `waits-on-fabric`。
- **`test/struggle.test.mjs`**（新增，`npm test`，5 用例全绿）：后台化→闭合、同步调用忽略、
  孤儿任务、非 fabric 忽略、backgroundTaskPending 语义。

**验证（真实数据）**：tone-chord 报 `waits-on-fabric: 2`、agent-24x7 报 2，均对应真实后台化
的 `fan_out`/`call`；`episodes` 计数不变（fabric-wait 已从 struggle 剔除）。

---

## Remaining observations (not yet harness work)

- `deepseek-v4-flash[1m] is temporarily unavailable` 卡住 auto-mode 的 Bash 权限判定 —— fabric
  路由模型可用性会连锁影响子代理的权限模式。可作为下一个探测点：child 在 fabric 后端抖动时
  auto 模式的行为。
- `post-review` 默认 provider 与用户偏好（deepseek-only）不符，导致每轮都被纠正。
- sharp-review 子代理 `File has not been read yet`（先 Write 后没 Read）—— 已知 edit-thrash
  签名。
