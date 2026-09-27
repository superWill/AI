# english

IELTS Academic 7.0 备考工作区。

## 怎么用

在这个目录里开会话，直接说要练什么，Claude 会调 `ielts-coach` agent：

```
练雅思
/ielts
帮我改这篇 Task 2
今天读点东西
```

第一次会跑一套诊断（约 45 分钟：长句解析 → 词汇量估测 → 限时 Task 2 → Speaking Part 1），
结果写进 `progress/profile.md`。**别跳过诊断**——自评的水平和实测差一个 band 是常态。

## Session modes

| mode | 干什么 |
|---|---|
| `read` | 一篇文章：先拆长句，再做题，再复盘 |
| `write` | 限时 Task 1 / Task 2，按四项评分标准打分 |
| `speak` | Part 1/2/3 文字版，只评内容/结构/语法（听不到发音） |
| `vocab` | 从 `progress/vocab.md` 间隔复习 + 语境新词 |
| `input` | 财报电话会/CNBC/巴菲特信节选，泛读 + 英文复述 |
| `listen` | 音频得自己在别处听，agent 只做转写稿训练 |

阅读弱的阶段默认配比：`input` 40% / `read` 25% / `write` 20% / `vocab` 15%。
做题技巧占比很小——技巧救不了不认识的词。

## progress/

agent 每次会话结束会写这三个文件，别手动删：

- `profile.md` — 水平、目标、当前主攻方向
- `error-log.md` — 反复犯的错，按频次排；连续 3 次不犯才移进 Fixed
- `vocab.md` — 生词 + 出处原句 + 复习间隔（1天/3天/1周/3周）

## Agent 定义

`~/.claude/agents/ielts-coach.md`（全局，在任何目录都能调用）。
