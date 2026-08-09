# Claude Code 2.1.226 Main System Prompt — Full Audit List (2026-08-09)

Source: Piebald-AI/claude-code-system-prompts (npm-extracted, exact). The main
system prompt is `system-prompts/system-prompt-*.md` — **140 files, ~217k chars**
(≈55-70k tokens when fully injected; actual injection is conditional). Also
relevant: `tool-description-*` (153 files, tool schemas live in `body.tools`),
`system-reminder-*` (81 files, runtime injections), `agent-prompt-*` (65, subagents),
`data-*` (106, reference docs), `skill-*` (84). Our own prompt replaces the
system-prompt-* set; tool schemas are NOT affected (body.tools is auto-attached).

Legend: ✅ keep (core) · 🧹 clean (not needed) · 🤔 decide

## A. Identity / core stance (base layer)
| part | chars | verdict |
|---|---|---|
| system-section | 545 | ✅ harness root — rewrite as our own identity |
| harness-instructions | 1250 | ✅ terminal-markdown/identity core — adapt |
| interactive-agent-intro-output-style-conditional | 815 | 🧹 replaced by our prompt (no output-style branching) |
| claude-fable-5-model-identity | 975 | 🧹 we run our own models (deepseek etc.) |
| communication-style | 1659 | ✅ keep brief-updates discipline |
| outcome-first-communication-style | 3005 | 🤔 overlaps communication-style — pick one or merge |
| tone-and-style-concise-output-short | 201 | ✅ concise default |
| tone-and-style-code-references | 335 | ✅ file:line references |
| respond-in-configured-language | 718 | ✅ language preference |
| emoji-avoidance | 276 | ✅ |
| act-when-ready | 480 | ✅ |
| correction-restraint | 1516 | ✅ |
| delivering-work-at-full-scope | 2333 | ✅ |
| task-approval-continuity | 649 | ✅ |
| doing-tasks-ambitious-tasks | 385 | ✅ |
| doing-tasks-help-and-feedback | 240 | ✅ |
| doing-tasks-no-compatibility-hacks | 388 | ✅ |
| doing-tasks-no-unnecessary-additions | 504 | ✅ |
| doing-tasks-no-unnecessary-error-handling | 483 | ✅ |
| doing-tasks-security | 420 | ✅ |
| doing-tasks-software-engineering-focus | 694 | 🤔 we do more than SE (academic/post modes) — soften |
| exploratory-questions-analyze-before-implementing | 588 | ✅ |
| troubleshooting-confirmation-policy | 524 | ✅ |

## B. Tool discipline (behavior core)
| part | chars | verdict |
|---|---|---|
| comment-what-and-task-context-avoidance | 496 | ✅ |
| comment-why-only-guidance | 466 | ✅ |
| prefer-editing-existing-files | 235 | ✅ |
| tool-call-colon-avoidance | 419 | ✅ |
| tool-call-summary-label | 654 | ✅ |
| parallel-tool-call-note-part-of-tool-usage-policy | 700 | ✅ |
| tool-usage-task-management | 484 | ✅ |
| tool-usage-subagent-guidance | 645 | ✅ |
| executing-actions-with-care | 3742 | ✅ |
| action-safety-and-truthful-reporting | 1006 | ✅ |
| frontend-browser-verification | 607 | 🧹 no frontend work |
| repl-tool-usage-and-scripting-conventions | 4029 | 🧹 no REPL tool usage |

## C. Memory system — **biggest clean candidate** (user runs `rem` plugin)
| part | chars | verdict |
|---|---|---|
| memory-instructions | 1397 | 🧹 replaced by rem |
| memory-persistence-scope | 518 | 🧹 |
| memory-save-exclusions | 219 | 🧹 |
| memory-index-pointer-instructions | 577 | 🧹 |
| combined-memory-index-pointer-instructions | 705 | 🧹 |
| description-part-of-memory-instructions | 945 | 🧹 |
| memory-description-of-user-feedback | 943 | 🧹 |
| feedback-memory-body-structure | 502 | 🧹 |
| feedback-memory-save-guidance | 694 | 🧹 |
| project-memory-body-structure | 544 | 🧹 |
| project-memory-save-guidance | 561 | 🧹 |
| project-skill-upkeep-for-feedback-memory | 1187 | 🧹 |
| personal-project-memory-description | 572 | 🧹 |
| team-project-memory-description | 562 | 🧹 |
| team-memory-index-pointer-instructions | 654 | 🧹 |
| user-memory-usage-guidance | 575 | 🧹 |
| auto-memory-durable-lesson-instructions | 3665 | 🧹 |
| dream-claude-md-memory-reconciliation | 1398 | 🧹 |
| dream-team-memory-handling | 1422 | 🧹 |
| plan-vs-memory-guidance | 587 | 🧹 |
| tasks-vs-memory-guidance | 580 | 🧹 |
| **subtotal** | **~18.5k chars** | 🧹 |

## D. Plan mode
| part | chars | verdict |
|---|---|---|
| phase-four-of-plan-mode | 1118 | ✅ core plan writing |
| plan-mode-interactive-workshop-offer | 2499 | 🤔 optional interactive workshop — keep |
| plan-sent-to-ultraplan | 620 | 🧹 no ultraplan |
| remote-plan-mode-ultraplan | 2991 | 🧹 no remote planning |
| remote-planning-session | 2155 | 🧹 |
| option-previewer | 852 | 🤔 AskUserQuestion previews — keep |

## E. Background / subagents / teams (fabric manages its own)
| part | chars | verdict |
|---|---|---|
| background-session-instructions | 1326 | 🤔 fabric spawns — keep if fabric children inherit |
| background-session-worktree-persistence-guidance | 849 | 🧹 |
| background-worktree-isolation-guidance | 758 | 🧹 |
| background-subagent-delegation-examples | 1901 | 🤔 |
| subagent-delegation-examples | 2675 | ✅ delegation guidance |
| subagent-delegation-restraint | 1761 | ✅ |
| fresh-subagent-delegation-example | 1163 | ✅ |
| foreground-subagent-delegation-examples | 1140 | ✅ |
| writing-subagent-prompts | 1439 | ✅ |
| forked-agent-guidance | 751 | 🤔 |
| fork-usage-guidelines | 1604 | 🤔 |
| forked-conversation-worktree-isolation-guidance | 1319 | 🧹 |
| agent-summary-generation | 805 | 🧹 fabric substitutes |
| agent-thread-notes | 1176 | 🧹 |
| worker-instructions | 1147 | 🧹 fabric workers |
| coordinator-mode-orchestration | 16214 | 🧹 fabric fan_out/teams replace it |
| coordinator-cross-session-peer-guidance | 1140 | 🧹 |
| teammate-communication | 594 | 🧹 |
| how-to-use-the-sendusermessage-tool | 1319 | 🧹 |
| saving-skills-via-file-delivery | 1007 | 🤔 |
| skillify-current-session | 7547 | 🤔 maybe useful |
| advisor-tool-instructions | 2172 | 🧹 no Advisor tool |
| harness-instructions (dup) | — | — |

## F. Autonomous loop (user uses fabric; official loop is separate)
| part | chars | verdict |
|---|---|---|
| autonomous-loop-check | 5261 | 🧹 official loop — we run fabric's |
| autonomous-loop-persistence-guidance-…persistent | 5729 | 🧹 |
| autonomous-loop-tick | 575 | 🧹 |
| autonomous-loop-tick-dynamic-pacing | 958 | 🧹 |
| autonomous-operation-guidelines | 1624 | 🤔 useful safety stance |
| autonomous-loop-notification-guidance | 681 | 🤔 |
| loop-tick-loop-md-absent-dynamic-pacing | 967 | 🧹 |
| loop-tick-loop-md-tasks | 575 | 🧹 |
| loop-tick-loop-md-tasks-dynamic-pacing | 915 | 🧹 |
| monitor-fallback-heartbeat-guidance | 852 | 🤔 Monitor tool guidance — keep essence |
| avoiding-unnecessary-sleep-commands-…powershell | 1001 | ✅ sleep discipline |

## G. Safety / permissions (keep all)
| part | chars | verdict |
|---|---|---|
| censoring-assistance-with-malicious-activities | 750 | ✅ |
| deny-rule-circumvention-classifier-guidance | 504 | ✅ |
| permission-classifier-strict-review-guidance | 596 | ✅ |

## H. Feature-specific (mostly cleanable)
| part | chars | verdict |
|---|---|---|
| artifact-comment-decision-reformat-retry | 1019 | 🧹 no artifact comments |
| artifact-comment-edit-composer | 2956 | 🧹 |
| artifact-comment-list-framing | 1200 | 🧹 |
| artifact-comment-reply-composer | 1556 | 🧹 |
| artifact-comment-thread-framing | 2090 | 🧹 |
| insights-at-a-glance-summary | 2660 | 🧹 user has traceme |
| insights-friction-analysis | 716 | 🧹 |
| insights-interaction-style | 645 | 🧹 |
| insights-memorable-moment | 551 | 🧹 |
| insights-on-the-horizon | 725 | 🧹 |
| insights-session-facets-extraction | 1360 | 🧹 |
| insights-suggestions | 2896 | 🧹 |
| insights-summary-at-a-glance | 717 | 🧹 |
| insights-what-works | 596 | 🧹 |
| learning-mode | 4752 | 🧹 |
| learning-mode-insights | 773 | 🧹 |
| minimal-mode | 801 | 🧹 |
| focus-mode-long-form | 659 | 🧹 |
| focus-mode-short-form | 598 | 🧹 |
| auto-mode | 1271 | 🤔 |
| auto-mode-setup-proposal-generator | 7935 | 🧹 |
| chrome-browser-mcp-tools | 1237 | 🧹 no Chrome automation |
| claude-in-chrome-browser-automation | 4358 | 🧹 |
| claude-in-chrome-browser-selection-instructions | 834 | 🧹 |
| self-hosted-runner-doctor | 15969 | 🧹 |
| self-hosted-runner-setup | 5355 | 🧹 |
| wsl-managed-settings-double-opt-in | 781 | 🧹 |
| pr-slack-notification-step | 672 | 🧹 |
| explain-code-review-ultra | 771 | 🧹 |
| code-review-artifact-publishing-instructions | 1141 | 🤔 user has sharp-review/evolve — own pipeline |
| hooks-configuration | 4584 | 🤔 user has own hooks — keep essentials |
| hook-evaluator-truncated-transcript-note | 584 | 🤔 |
| hook-feedback-handling | 566 | ✅ treat hook output as user feedback |
| how-to-use-the-sendusermessage-tool (dup) | — | — |
| powershell-edition-for-5-1 | 1217 | ✅ Windows user |
| powershell-edition-for-7 | 593 | ✅ |
| powershell-edition-unknown | 529 | ✅ |
| shared-git-stash-safety | 757 | ✅ |
| git-status | 316 | ✅ (moves to user message w/ exclude-dynamic flag) |
| scratchpad-directory | 898 | ✅ .scratch concept |
| context-compaction-summary | 1503 | ✅ |
| partial-compaction-instructions | 4253 | ✅ |
| interactive-agent-intro-output-style-conditional | 815 | 🧹 |
| tool-call-colon-avoidance (dup) | — | — |

## Totals (140 parts, 217k chars)
- 🧹 clean candidates: **~75 parts ≈ 90k+ chars** (memory system ~18.5k, insights ~10k,
  artifact-comments ~8.8k, coordinator ~16.2k, self-hosted-runner ~21k, chrome ~6.4k,
  autonomous-loop ~15k, learning/focus/auto-mode ~14k)
- ✅ keep core: ~50 parts ≈ 60k chars
- 🤔 decide: ~15 parts

Note: `--system-prompt` replaces this whole layer in our platform, so "cleaning"
means: we author our own prompt.md containing only the ✅ items (rewritten/adapted),
plus our own sections (identity, memory via rem, styles). The cleaned parts simply
never enter our prompt. Official prompt stays intact for native claude sessions.
