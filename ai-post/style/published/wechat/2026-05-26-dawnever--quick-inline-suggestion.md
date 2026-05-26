---
platform: wechat
slug: dawnever--quick-inline-suggestion
published: 2026-05-26
title: 400 行代码，还你一个干净的 Inline Suggestion
---


# 400 行代码，还你一个干净的 Inline Suggestion

## Cmd+I 坏掉了

有一天我按下 Cmd+I，等了三秒，出来的不是 diff，是一个"正在思考..."的 spinner，背后带着一个全屏的侧边栏面板。

可是我只是想把一个函数名改短一点。

这种感觉很难描述——就像你去便利店买瓶水，结账时店员问你要不要办会员、填问卷、加 APP、开通 Plus。VS Code 的 AI 辅助功能就是这样一步步变重的。Copilot Chat、内联编辑、Agent 模式、多模型切换……每个功能单独看都挺合理，但叠在一起之后，原来那个"选中代码 → 说一句话 → 看 diff"的简洁流程，悄悄消失了。

我在某个深夜决定：不如自己写一个。

## 这个插件做了什么

`quick-inline-suggestion` 的使用流程就是字面意思：

1. 选中代码（或者不选，用整个文件作上下文）
2. 按 `Cmd+I`
3. 在弹出的输入框里说你想做什么
4. 看 diff，按 Keep 或者 Revert

就这样。没有侧边栏。没有 Chat 历史。没有"AI 正在分析你的项目结构"。

后端支持 Claude Code CLI（`claude -p`）和 OpenAI Codex CLI（`codex exec`），用的都是你自己安装的命令行工具，不需要额外订阅。整个插件核心逻辑三个文件，加起来约 600 行 TypeScript，零运行时依赖。

已发布到 VS Code Marketplace，插件 ID：`MingyangBao.quick-inline-suggestion`。

## ⚡ 核心功能解析

### 1. Edit 模式：能看 diff 再决定

AI 改完代码之后，不是直接替换，而是打开一个 diff 视图：左边是你的原始代码，右边是 AI 的修改。你审一眼，满意就点 Keep，不满意就 Revert，一键回到原样。


底层用的是 VS Code 的 `WorkspaceEdit` API，这意味着 Keep 之后，undo 历史是完整的——你可以正常 Ctrl+Z 撤回。不少插件图省事直接操作文本，结果 undo 栈乱掉，这里我特别绕开了这个坑。

```typescript
// 应用修改：WorkspaceEdit 保留完整 undo 历史
const edit = new vscode.WorkspaceEdit();
edit.replace(doc.uri, selectionRange, newText);
await vscode.workspace.applyEdit(edit);

// 打开 diff 视图
await vscode.commands.executeCommand(
  'vscode.diff',
  originalUri,  // 快照
  doc.uri,      // 修改后
  'AI Suggestion — Keep or Revert?'
);
```

Keep 按钮按下去之前，代码已经改了。Revert 其实是再执行一次 `WorkspaceEdit`，把原文本写回去。这样做的好处是 diff 视图里可以直接看"真实"的编辑器状态，而不是一个假的预览。

### 2. Ask 模式：不用打开 Chat

有时候你不是要改代码，你只是想问一句"这个函数为什么这么写"或者"这里的类型错误是什么意思"。

输入框支持自动识别你是在问问题还是在下指令。`isQuestion()` 函数同时覆盖中英文问句模式：

```typescript
// 中英文问句自动识别，无需手动切换模式
function isQuestion(input: string): boolean {
  const enPattern = /^(what|why|how|when|where|who|explain|describe|tell me)/i;
  const cnPattern = /^(什么|为什么|怎么|如何|解释|说明|是否)/;
  return enPattern.test(input.trim()) || cnPattern.test(input.trim());
}
```

问题模式下，AI 的回答会在侧边打开一个临时 markdown 文件，不会污染当前编辑器，看完直接关掉。



### 3. 双后端 + 自动回退 🔧

`claude -p` 是 Claude Code 的命令行接口，`codex exec` 是 OpenAI Codex 的。你可以在设置里选主用哪个，如果主后端报错（比如网络超时、命令找不到），插件会静默切换到另一个重试，不打断你的操作。

```typescript
// 自动回退：主后端失败时静默切换
async function runWithFallback(prompt: string): Promise<string> {
  try {
    return await runClaude(prompt);
  } catch (primaryErr) {
    try {
      return await runCodex(prompt);
    } catch (fallbackErr) {
      throw new Error(`Both backends failed:\n${primaryErr}\n${fallbackErr}`);
    }
  }
}
```

提示词通过 stdin 传入，而不是命令行参数。这避免了参数长度限制和 shell 注入风险，也不会让提示词内容出现在 `ps aux` 的进程列表里。

Codex CLI 有个特殊之处：它把会话元数据（token 用量、响应头）写到 stderr，真正的输出在 stdout 或者指定的 `--output-last-message <tmpfile>`。我用了后者，读完文件之后立即 `unlinkSync` 清掉。

### 4. 指令历史：不用重复打字

每次输入的指令都会记录下来，最多保存 20 条。下次按 Cmd+I，历史记录会显示在输入框里，可以直接选择复用。

历史列表可以按使用频率排序（`×5` 这样的标注告诉你哪条用得最多），也可以按时间倒序排。重复的代码规范调整、固定的注释格式，不用每次手打。


### 5. 几个细节，踩坑才懂 💡

**Selection snapshot**：触发 Cmd+I 之后，AI 的网络请求可能要等 2-5 秒。在这段时间里，用户可能继续编辑，光标位置或选区会变。所以在异步调用开始之前，先把当前的选区范围和文本快照存下来，后续操作全部基于快照而不是当前状态。

**QuickPick 的一个内部陷阱**：VS Code 的 QuickPick 有个不那么显眼的行为——`qp.hide()` 会同步触发 `onDidHide` 回调，在这个回调里 QuickPick 对象会被 dispose。如果你在 `hide()` 之前没有先 `resolve()`，Promise 就永远不会 settle，程序挂住。正确顺序是先 resolve，再 hide。这个细节在官方文档里没有明确提到，调试了一下午才找到。

## 🚀 快速上手

**第一步：安装插件**

在 VS Code 扩展面板搜索 `quick-inline-suggestion`，或者直接安装：

```bash
code --install-extension MingyangBao.quick-inline-suggestion
```

**第二步：确认 CLI 工具已安装**

```bash
# 确认 Claude Code CLI 可用
claude --version

# 或者确认 Codex CLI 可用
codex --version
```

两个装一个就够，都装了也行。

**第三步：试一下**

打开任意代码文件，选中一段函数，按 `Cmd+I`（Windows/Linux 是 `Ctrl+I`），在弹出框里输入你想做的修改，回车。等 AI 跑完，diff 视图就打开了。

如果你想换模型，执行命令面板里的 `Quick: Select Model`，插件会解析 `claude --help` 的输出来列出可用模型，如果解析失败就回退到内置的列表（包括 claude-sonnet-4-6、gpt-5 等）。

## 为什么是 400 行

我没有刻意控制行数。写完之后数了一下，就是这么多。

这个数字说明了一件事：这个功能本来就不复杂。Copilot 的 inline 编辑功能背后可能有几万行代码，很多用于处理那些你永远不会遇到的边缘情况、UI 动画、多模型路由策略……但如果你只需要"选代码 → 说需求 → 看 diff"，600 行够了。

代码在 GitHub，没有加密，没有遥测，没有 telemetry 上报。你改什么代码、用什么提示词，只在你和你的 CLI 工具之间。

GitHub: https://github.com/DawnEver/quick-inline-suggestion
