---
platform: zhihu
slug: dawnever--quick-inline-suggestion
published: 2026-05-26
title: VS Code 的 AI 越来越重，我拆了三条路，选了最轻的那个
---


## VS Code 的 AI 越来越重，我拆了三条路，选了最轻的那个

先说结论：如果你已经在用 Claude Code 或 Codex CLI，[quick-inline-suggestion](https://github.com/DawnEver/quick-inline-suggestion) 值得装。它不是 Copilot 替代品，也不跟 Cursor 竞争。它只做一件事——把你已有的 CLI 工具接进 Cmd+I。完。

---

## Cmd+I 怎么变成这样了

Copilot 刚出那会儿，Cmd+I 的交互模型挺对的：选中代码，说句话，看 diff，保留或者回滚。没多余的东西。

后来它长成了一个我认不出来的东西。Chat 侧边栏、Agent 模式、多步骤工作流、越来越复杂的 UI。每个新功能单独看都合理，叠在一起之后，原来那个简单入口被埋了。而且 Copilot 把 Cmd+I 快捷键注册成自己的，你想用别的方案还得先去快捷键设置里解绑。

Cursor 走得更远，直接 fork 了 VS Code，把 AI 做进编辑器内核。重度 AI 编程的话这条路有道理。但如果你只是想在工作流里偶尔让 AI 改一段代码，Cursor 的订阅和迁移成本都过了。

我就是在某个深夜受不了了，自己写了这个插件。

---

## 它到底是什么

quick-inline-suggestion，VS Code 扩展，Marketplace 搜 `quick-inline-suggestion` 就能装。三个文件，大概 600 行 TypeScript，零运行时依赖。

后端是你本地的 `claude` 或 `codex` 命令。扩展自己不存 API key，也不往任何中间服务发请求——spawn 个子进程，prompt 走 stdin 丢进去，读输出，WorkspaceEdit 写回编辑器。

流程就四步：选中代码 → Cmd+I → 描述修改 → 看 diff 决定 Keep 还是 Revert。

---

## 跟 Copilot 和 Cursor 比呢

| 维度 | quick-inline-suggestion | GitHub Copilot | Cursor |
|------|------------------------|---------------|--------|
| 费用 | 无额外订阅（复用 Claude Code / Codex 凭据） | $10/月起 | $20/月起 |
| 安装 | 需要预装 claude 或 codex CLI | 扩展直接装 | 独立应用，迁移整个 IDE |
| inline edit | 选中 → 描述 → diff → 保留/回滚 | 同上但 UI 更重 | 同上，绑定 Cursor |
| 上下文 | 选中内容 + workspace cwd | 仓库级上下文 | 仓库级上下文 |
| 自动补全 | 无 | 有 | 有 |
| Chat 侧边栏 | 无 | 有 | 有 |
| 模型 | 取决于你装了哪个 CLI | 固定 Copilot 模型 | 多模型可选 |
| 代码量 | ~600 行，可读完 | 闭源 | 闭源 |

要不要用这个插件，基本就取决于一件事：你是不是已经在给 Claude Code 或 Codex 付钱了。如果是，零额外成本。如果不是，Copilot 整体更完整，没必要折腾。

---

## 迭代过程里发现的几个点

装完直接用，没有登录、没有网络请求、没有加载画面。确认本地 `claude` 或 `codex` 命令能用，就结束了。

isQuestion() 这个函数比我预想的好用。同一个输入框，你打"这里为什么要用 async"它会自动切到 Ask 模式，回答开在旁边 markdown 里，不会傻到把解释当代码写进去。判断逻辑就是正则，中英文常见疑问句式都覆盖了，实际用下来基本没错过。




历史指令也比我想的有用。"加单元测试"、"优化性能"这种重复指令会按频次排前面，带 ×5 这种计数，不用每次手打。


有一个边界情况调试了一下：AI 响应期间手贱改了文件，插件检测到版本冲突之后没有强行覆盖，而是提示用 Ctrl+Z 回退。这个处理是对的，但第一次遇到还是愣了一下。

几个实现细节我觉得值得提：

Prompt 走 stdin 而不是命令行参数。没长度限制、没 shell 注入、进程列表里看不到你的提示词。Codex CLI 比较特殊——它把 token 用量之类的元数据写 stderr，真正的输出得用 `--output-last-message <tmpfile>` 接到临时文件里读，读完立刻 `unlinkSync` 清掉。

VS Code 的 QuickPick 有个文档里没写清楚的行为：`qp.hide()` 会同步触发 `onDidHide`，回调里 QuickPick 被 dispose。如果你在 `hide()` 之前没调 `resolve()`，Promise 永远挂住。调了一下午，现在写在注释里了。

---

## 不适合你的情况

- 没装 Claude Code 或 Codex CLI —— 门槛反而比 Copilot 高，先搞定 CLI 的安装和账号再说
- 需要跨文件复杂重构 —— 上下文只有选中内容和 workspace cwd，Copilot 的仓库级上下文这种场景更强
- 需要自动补全（ghost text）—— 完全不在设计范围内
- 团队协作需要统一 AI 工具链 —— Copilot for Business 的管理能力这个真没有

如果以上都不沾，而且你已经装着 claude 或 codex 在用，那装一个试试，反正免费。

项目地址：https://github.com/DawnEver/quick-inline-suggestion
