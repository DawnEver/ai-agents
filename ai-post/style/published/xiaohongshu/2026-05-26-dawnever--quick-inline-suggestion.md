---
platform: xiaohongshu
slug: dawnever--quick-inline-suggestion
published: 2026-05-26
title: （封面 hook）
---


🔥 Copilot 越更新我越想卸载——Cmd+I 那个框现在要加载半天，还跳出一堆我根本不需要的按钮。

我受不了了，自己写了个插件。

💡 叫 quick-inline-suggestion，约 600 行 TypeScript，零依赖。就干一件事：

选中代码 → Cmd+I → 说你要改啥 → 看 diff → Keep 或 Revert

没了。

不用登录，不用订阅，后端直接走你本地的 Claude Code 或者 Codex CLI。反正这俩工具你本来就装着，插件只是帮你把它们接进编辑器里。

✨ 用下来最舒服的几个点：

AI 改完不会直接覆盖你的代码，而是先打开 diff 让你审一遍：左边是原文，右边是 AI 的修改，你自己决定要不要保留。底层用的是 WorkspaceEdit API，点 Keep 之后 Ctrl+Z 也能正常撤回。不像有些插件直接改文本，容易把 undo 栈搞乱，这个细节处理得很干净。


输入框里中英文都能自动识别。比如你问"这里为什么要用 async"，它会判断你是在提问，直接在旁边新开一个 markdown 文件回答，不会动你的代码。也不用你先选"Edit 模式"还是"Chat 模式"——就一个输入框，它自己判断意图。



Prompt 是通过 stdin 传进去的，不走命令行参数。这样既避免 shell 注入，也不会在进程列表里暴露你的提示词。这个小细节我当时查了挺久才想明白。

👇 插件 ID：quick-inline-suggestion，扩展市场直接搜，或者去 GitHub 找 DawnEver/quick-inline-suggestion～

#VSCode插件 #开发者工具 #开源工具 #程序员 #AI编程
