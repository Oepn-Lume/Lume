---
id: x-marketing-playbook-v1-md
type: doc
relative_path: x-marketing-playbook-v1.md
language: mixed
section: root
---

# X Marketing Playbook V1

## Source
- Path: `x-marketing-playbook-v1.md`
- Language: `mixed`
- Section: `root`
- Original file: [x-marketing-playbook-v1.md](C:/Users/yh-PC-003/Desktop/codex/lume/docs/x-marketing-playbook-v1.md)

## Body

# X Marketing Playbook V1

## English

This document describes the current marketing path for `Lume` on `X`.

### What Exists Today

- `scripts/x_agent_executor.py`
- preview thread generation
- optional live-post path when credentials are available
- watchman report and publish result artifacts
- `scripts/x_marketing_agent.py` for daily post planning
- `scripts/x_mention_monitor.py` for mention inbox and reply suggestions

### Required Credentials

Store these in `.env` or the environment:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

Optional OAuth 2.0 path:

- `X_CLIENT_ID`
- `X_CLIENT_SECRET`
- `X_OAUTH2_ACCESS_TOKEN`
- `X_OAUTH2_REFRESH_TOKEN`
- `X_REDIRECT_URI`

### Example Commands

Preview English thread:

```powershell
python scripts/x_agent_executor.py --repo-url "https://github.com/Oepn-Lume/Lume" --language en
```

Preview Chinese thread:

```powershell
python scripts/x_agent_executor.py --repo-url "https://github.com/Oepn-Lume/Lume" --language zh
```

Attempt live posting:

```powershell
python scripts/x_agent_executor.py --repo-url "https://github.com/Oepn-Lume/Lume" --language en --post
```

Generate a daily post plan:

```powershell
python scripts/x_marketing_agent.py --language en
```

Generate mention reply suggestions:

```powershell
python scripts/x_mention_monitor.py
```

### Outputs

- `data/marketing/starfire_launch/x_thread_drafts.json`
- `data/marketing/starfire_launch/publish_results.json`
- `data/marketing/starfire_launch/watchman_report.md`
- `data/marketing/daily_agent/*.json`
- `data/marketing/mentions/reply_suggestions.json`

## 中文

本文档描述 `Lume` 当前在 `X` 平台上的宣传路径。

### 当前已具备

- `scripts/x_agent_executor.py`
- 预览线程生成
- 在凭据齐全时可尝试真实发帖
- 守望者报告与发布结果文件
- `scripts/x_marketing_agent.py` 用于生成每日宣传计划
- `scripts/x_mention_monitor.py` 用于生成提及回复建议

### 所需凭据

将以下变量放入 `.env` 或环境变量：

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

可选的 OAuth 2.0 路径：

- `X_CLIENT_ID`
- `X_CLIENT_SECRET`
- `X_OAUTH2_ACCESS_TOKEN`
- `X_OAUTH2_REFRESH_TOKEN`
- `X_REDIRECT_URI`

### 示例命令

预览英文线程：

```powershell
python scripts/x_agent_executor.py --repo-url "https://github.com/Oepn-Lume/Lume" --language en
```

预览中文线程：

```powershell
python scripts/x_agent_executor.py --repo-url "https://github.com/Oepn-Lume/Lume" --language zh
```

尝试真实发帖：

```powershell
python scripts/x_agent_executor.py --repo-url "https://github.com/Oepn-Lume/Lume" --language en --post
```

生成每日宣传计划：

```powershell
python scripts/x_marketing_agent.py --language en
```

生成提及回复建议：

```powershell
python scripts/x_mention_monitor.py
```

### 输出位置

- `data/marketing/starfire_launch/x_thread_drafts.json`
- `data/marketing/starfire_launch/publish_results.json`
- `data/marketing/starfire_launch/watchman_report.md`
- `data/marketing/daily_agent/*.json`
- `data/marketing/mentions/reply_suggestions.json`

