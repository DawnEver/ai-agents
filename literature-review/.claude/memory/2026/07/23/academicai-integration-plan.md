---
name: academicai-integration-plan-2026-07-23
description: 全面融入计划：吸收 ReviewAgent + AeroWdgLiteratureReview + crawl-uon-moodle 到 literature_review，用 models.py 取代 JSON Schema
metadata:
  type: project
---

# Literature Review — AcademicAI 全面融入计划

## Context

`C:\Users\linxu\Documents\AI\AcademicAI` 下有 3 个成熟项目，各自实现了文献调研的不同环节：

| 项目 | 核心能力 | 关键技术 |
|------|----------|----------|
| **ReviewAgent** | PDF 文本提取 → AI 批量评审 → CSV 输出 | `litellm` 模型抽象、`pypdf2`、`csv2md` |
| **AeroWdgLiteratureReview** | 关键词流水线 → 搜索 → 提取 → 过滤 → 可视化 | `litellm`、14 个 pipeline 模块、`plot` |
| **crawl-uon-moodle** | 通用网页爬虫 | `beautifulsoup4`、`requests` |

加上当前 `literature_review` 已有的能力（IEEE 搜索、审批门、PDF 获取/分解、去重排序），融合后的系统应该覆盖文献调研的**完整生命周期**。

## 目标架构

```
literature_review/                    # 唯一入口包
│
├── cli.py                           # lit-review CLI（不变）
│
├── models.py                        # 🆕 取代 schemas/ 目录 — Python dataclasses
│
├── providers/                       # 文献源适配器（保留）
│   ├── base.py                      # BaseProvider
│   └── ieee.py                      # IeeeXploreProvider
│
├── search/                          # 🆕 搜索层 — 融合 AeroWdg pipeline_search
│   ├── query.py                     # 查询构建（融合 keyword_pipeline）
│   └── engine.py                    # 多源搜索编排（融合现有 search.py）
│
├── acquire/                         # 🆕 PDF 获取层 — 融合现有 browser/
│   ├── download.py                  # 浏览器下载
│   └── crawl.py                     # 🆕 通用爬虫 — 融合 crawl-uon-moodle 模式
│
├── ingest/
│   └── decompose.py                 # PDF 分解
│
├── review/                          # 🆕 评审层 — 融合 ReviewAgent + AeroWdg filter
│   ├── extract.py                   # PDF 文本提取
│   ├── screen.py                    # 摘要筛选
│   ├── reader.py                    # AI 深度阅读
│   └── synthesis.py                 # 综合分析
│
├── ai/                              # 🆕 AI 抽象层 — 统一 litellm 接口
│   └── client.py                    # 模型路由、litellm 封装
│
├── export/                          # 🆕 输出层
│   ├── render.py                    # paper_card → markdown, JSON → CSV
│   └── plot.py                      # 文献计量可视化
│
├── pipeline/                        # 流水线编排
│   ├── brief.py                     # 研究简报 + 审批门
│   └── gate.py                      # 通用审批门（SHA-256 绑定）
│
└── utils/
    ├── log.py                       # 日志
    ├── paths.py                     # 路径
    └── common.py                    # 共享工具
```

## 关键决策

### 1. `models.py` 取代所有 JSON Schema
- 删除 10 个 JSON Schema 文件，换成一个 Python dataclass 文件
- 零依赖（不需要 jsonschema、referencing、Registry）
- IDE 自动补全、类型检查
- `asdict()` 直接转 YAML/JSON

### 2. 吸收映射

| 来源 | 目标 |
|------|------|
| ReviewAgent review.py | review/reader.py |
| ReviewAgent extract_text.py | review/extract.py |
| ReviewAgent csv2md.py | export/render.py |
| AeroWdg keyword_pipeline.py | search/query.py |
| AeroWdg pipeline_search.py | search/engine.py |
| AeroWdg pipeline_filter.py | review/screen.py |
| AeroWdg pipeline_schema.py | models.py |
| AeroWdg plot.py | export/plot.py |
| crawl-uon-moodle main.py | acquire/crawl.py |

### 3. 删除项
- `literature_review/schemas/` → 换成 models.py
- `literature_review/utils/schema.py` → jsonschema 不再需要
- `templates/` → 全部删除
- `lenses/` → 保留 power_electronics.yaml，改成 Python dict 加载

## 实施路线图

### Phase 1: 数据模型 + AI 层（基础设施）
1. 创建 `models.py`，替换所有 schema
2. 创建 `ai/client.py`，融合 litellm 接口
3. 删除 `schemas/` 目录
4. 更新 CLI 和 pipeline 使用 dataclass

### Phase 2: 吸收核心逻辑
5-10. review 层（extract, reader, screen, synthesis）+ search 层（query, engine）

### Phase 3: 输出 + 爬虫
11-13. export 层（render, plot）+ acquire/crawl.py

### Phase 4: 整合 + 清理
14-17. CLI 更新、删除 templates/、更新 .claude/skills/、端到端测试

## 验证
1. `pip install -e .` 成功
2. `lit-review --version` → 0.3.0
3. `python -m pytest tests/ -v` 全部通过
4. `schemas/`、`templates/` 目录不存在
