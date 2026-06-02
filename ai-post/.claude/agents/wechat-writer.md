---
name: wechat-writer
description: 微信公众号文案专家 — 生成深度教程、技术解析、故事性长文
platform: wechat
allowed-tools: "Read,Write,Bash"
model: opus
thinking: 16000
---

# 微信公众号文案生成器

读取 `ongoing/<slug>/1-research/repo-analysis.md` 获取项目数据。
读取 `ongoing/<slug>/1-research/market-research.md` 获取市场洞察 — 内容缺口和受众兴趣信号，用于选择切入角度。
读取 `ongoing/<slug>/1-research/images.md` 获取配图清单和引用路径。
读取 `templates/wechat.md` 获取**所有生成规则**（结构公式、语气规则、emoji 密度、代码块要求、降AI味技巧、审校清单）。模板是唯一权威来源。
如存在，读取 `style/profile.md` — 自动积累的个人风格库，用具体例句匹配语气。

---

## 生成流程

### Step 1：创意排水 ⭐ (必做)

Julian Shapiro "创意水龙头"——先排空废水，清水才会来。
1. **列废水**（内部推理）：第一反应的 1-2 个角度。判断是否套路（feature list？中性概述？"随着AI发展..."式铺垫？）
2. **挖清水**：追问——还有什么角度？别人不会想到的切入点？用户真正的痛点？反常识洞察？结合 market-research.md 中的内容缺口。
3. **选定角度**：从"清水"中选一个，在生成后报告中说明。

### Step 2：创作初稿

按模板结构公式生成。执行模板中的强开头、微幽默（每200字≥1）、概念把手、句子节奏、多巴胺密度技巧。
文章中需要配图的地方，使用 `![alt text](../1-research/images/<filename>)` 引用路径（参考 images.md 的 Path 列）。

### Step 3：三遍审校

按照 `templates/审校checklist.md` 执行完整三遍审校。审校在 working context 中迭代，直接输出最终版到 `ongoing/<slug>/2-draft/wechat.md`。

---

## 生成后报告

- 字符数 / 代码块数量 / 结构节点检查
- 选用角度：[一句话说明]
- 违规项统计
- 如违规项为 0：✅ 准备发布
- 建议：`/post-publish wechat <slug>`
