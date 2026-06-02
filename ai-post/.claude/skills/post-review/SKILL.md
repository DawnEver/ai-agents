---
name: post-review
description: 三方会审 — each reviewer identity is run independently by Claude Sonnet, DeepSeek (take-over), and Codex. Disagreements between models surface genuine issues.
argument-hint: <slug> [platform]
allowed-tools: "Read,Write,Glob,Grep,Agent,Skill"
---

# /post-review — 三方会审

## 核心设计

**每个审稿身份 = 三个模型独立跑同一角色**

```
身份A 读者代理人:  [Claude Sonnet] [DeepSeek V4 Pro] [Codex]
身份B 技术核查员:  [Claude Sonnet] [DeepSeek V4 Pro] [Codex]
```

三个模型用同一份审稿 prompt，独立给出判词。
**三者一致 → 结论可信；三者分歧 → 该处需要人工判断。**

---

## 参数解析

- `<slug>` — 文章目录名，对应 `ongoing/<slug>/`
- `[platform]` — 可选，指定单一平台；不填则审所有已生成平台

检查 `ongoing/<slug>/2-draft/` 下有哪些 `.md` 文件已存在（包括 `images.md`）。

---

## 两个审稿身份 & 对应 Prompt

### 身份 A：读者代理人

> 你是一名对 AI 生成内容极度敏感的挑剔读者。不懂平台规则，只在乎"这篇文章好不好看"。你每天被 AI 内容轰炸，能瞬间识别 AI 腔。

**检查项**：
- 开头前 3 句：是否抓住你？还是让你想划走？（1-5分）
- 逐段 AI 味打分：🟢 人味 / 🟡 轻微AI / 🔴 明显AI，每段说明原因
  - 🔴 标准：套话堆砌、无个人立场、像新闻稿
  - 🟢 标准：像真实的人在分享经历和观点
- 微幽默：哪里有让你嘴角微扬的细节？哪里完全没有？
- 最无聊的段落是哪段？为什么？
- 句子节奏：默读一遍，是否单调？
- 图片描述（alt text）：是否与文章主题/术语一致？是否过于通用像占位符？是否用了作者不会用的词？

**输出**：
```
[模型名] 身份A 读者代理人 — <platform>

开头钩子: <分>/5 — <理由>
AI味逐段:
  第1段: 🟢/🟡/🔴 — <原因>
  第2段: ...
微幽默: <有/无/稀少> — <位置或建议>
最无聊段: 第X段 — <原因>
节奏感: <流畅/单调/局部单调>

判决: PASS ✅ / FAIL ❌
问题列表: <每条问题一行>
```

---

### 身份 B：技术核查员

> 你是一名软件工程师，专门验证技术内容的准确性。不在乎文章好不好看，只在乎技术对不对。

**检查项**（对照 `ongoing/<slug>/1-research/repo-analysis.md`）：
- 每个代码块：语法正确？能实际运行？
- 安装步骤：命令准确？顺序正确？
- 技术术语：是否被正确使用（无误用/夸大）？
- 架构描述：与 repo-analysis 中实际代码发现一致？
- 性能声明、数据：有无编造或夸大？
- 依赖包名、版本：是否真实存在？

**输出**：
```
[模型名] 身份B 技术核查员 — <platform>

代码块 #1: ✅/⚠️/❌ — <说明>
代码块 #2: ...
安装步骤: ✅/⚠️/❌ — <说明>
技术术语: ✅/⚠️/❌ — <说明>
架构描述: ✅/⚠️/❌ — <说明>
数据声明: ✅/⚠️/❌ — <说明>

判决: PASS ✅ / FAIL ❌
问题列表: <每条问题一行，附正确内容>
```

---

## 执行流程

### Phase 1：并行分发 9 个子 agent

对每个目标平台，一次性并行启动 6 个子 agent：

```
身份A 读者代理人 × 3 模型:
  A1: Agent(fork, prompt=身份A prompt + 文章内容)          ← Claude Sonnet
  A2: Skill("take-over:continue", prompt=身份A prompt)     ← DeepSeek V4 Pro
  A3: Skill("codex:rescue", prompt=身份A prompt)           ← Codex

身份B 技术核查员 × 3 模型:
  B1: Agent(fork, prompt=身份B prompt + 文章内容 + repo-analysis.md)
  B2: Skill("take-over:continue", prompt=身份B prompt)
  B3: Skill("codex:rescue", prompt=身份B prompt)
```

> Twitter/X 为纯文字平台，跳过身份B（技术核查），只跑身份A 共 3 个 agent。

### Phase 2：收集 6 份判词

等待所有 agent 返回结果。如某个 agent 调用失败，记录原因并标注该格为 `⚠️ 未响应`，不影响其他评审。

### Phase 3：分身份合议

对每个身份的三份判词做对比分析：

```
═══ 身份A 读者代理人 合议 ═══

         Claude   DeepSeek   Codex
开头钩子   4/5      3/5        4/5   → 基本一致，尚可
第3段AI味  🟡       🔴         🟢   → 🔀 分歧：DeepSeek认为明显AI腔
微幽默     有        稀少       有    → 🟡 DeepSeek认为密度不足
...

身份A 合议判决: ⚠️ 有条件（存在分歧需人工判断）

═══ 身份B 技术核查员 合议 ═══
...
```

**合议规则**：
- 3/3 一致 → 结论可信，直接采纳
- 2/3 同意 → 多数判决，附少数意见
- 1/3（只有一个模型发现）→ 标注 `⚠️ 存疑`，列出但不强制修改
- 分歧点 → 高亮为 `🔀 模型分歧`，需用户人工判断

### Phase 4：综合裁决

```
╔═══════════════════════════════════════════════════╗
║  🏛️ 三方会审综合裁决 — <platform>                 ║
╠═══════════════════════════════════════════════════╣
║  身份A 读者代理人:  PASS ✅ / FAIL ❌             ║
║  身份B 技术核查员:  PASS ✅ / FAIL ❌             ║
╠═══════════════════════════════════════════════════╣
║  综合裁决:                                        ║
║  ✅ 可发布 — 两身份全部通过                       ║
║  ⚠️ 有条件 — <X身份>发现次要问题，修改后可发      ║
║  ❌ 不可发布 — <X身份>发现严重问题，需重写        ║
╚═══════════════════════════════════════════════════╝

📋 问题汇总（按优先级）

🔴 必须修改（2-3模型一致，阻断发布）：
  [身份A] 开头2/3 — 第1句是套话，换具体事件开头

🟡 建议修改（2模型一致或单模型高置信）：
  [身份B] 代码块#2 pip install 命令可能缺少版本锁定

🔀 模型分歧（需人工判断）：
  [身份A] 第3段 AI味：Claude🟡 / DeepSeek🔴 / Codex🟢
    → DeepSeek认为明显AI腔，Claude和Codex认为尚可，建议你自己判断

🟢 可选优化：
  [身份A] 微幽默密度可再提高
```

### Phase 5：全平台总览

```
📊 三方会审总览 — <slug>

| 平台    | A读者 | B技术 | 综合  | 分歧数 |
|---------|-------|-------|-------|--------|
| 小红书  |  ❌   |  —    |  ❌   |   1    |
| 微信    |  🟡  |  ✅   |  ⚠️   |   2    |
| 知乎    |  ✅   |  ⚠️  |  ⚠️   |   0    |
| Twitter |  ✅   |  —    |  ✅   |   0    |

建议操作：
- 小红书：`/post-regenerate <slug> xiaohongshu`
- 微信：手动处理分歧后 `/post-publish wechat <slug>`
- 知乎：确认技术问题后 `/post-publish zhihu <slug>`
- Twitter：`/post-publish twitter <slug>`
```

### Phase 6：图片提示词会审（Image Prompt Review）

文章正文审完后，对 `2-draft/images.md` 做独立审查，输出 `3-final/images.md`。

**审查依据**：对照 `3-final/<platform>.md` 终稿，检查 images.md 中的图片描述和 AI prompt 是否与终稿一致。

**检查项**：
- 术语一致性：图片 alt 文本中的概念名称是否与终稿一致？（如终稿用"奴隶主视角"，图片描述不应写"编排者视角"）
- 残留引用：是否提到已删除的概念？（如终稿去掉了 GPT，图片 prompt 不应再提 GPT）
- 封面标题匹配：封面图的 hook text / title 是否与终稿标题一致？
- 过时描述：图片的 Scene/描述是否反映终稿的实际内容？
- 比例正确：封面图 aspect ratio 是否匹配平台要求？

**输出**：修复后的 `ongoing/<slug>/3-final/images.md`，格式与 2-draft 版相同，但所有 prompt 经过终稿对齐。如有无法确定的项，标注 `⚠️ 需人工确认`。
