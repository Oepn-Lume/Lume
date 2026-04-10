---
id: zhihu-marketing-playbook-v1-md
type: doc
relative_path: zhihu-marketing-playbook-v1.md
language: zh
section: root
---

# Zhihu Marketing Playbook V1

## Source
- Path: `zhihu-marketing-playbook-v1.md`
- Language: `zh`
- Section: `root`
- Original file: [zhihu-marketing-playbook-v1.md](C:/Users/yh-PC-003/Desktop/codex/lume/docs/zhihu-marketing-playbook-v1.md)

## Body

# Zhihu Marketing Playbook V1

## English

Zhihu publishing is currently handled as a content-generation path, not a guaranteed direct-post API path.

### What Exists Today

- `scripts/zhihu_marketing_agent.py`
- Zhihu-ready article title, summary, body, and tags
- publish checklist artifacts under `data/marketing/zhihu/`

### Command

```powershell
python scripts/zhihu_marketing_agent.py
```

### Outputs

- `data/marketing/zhihu/article.json`
- `data/marketing/zhihu/article.md`
- `data/marketing/zhihu/publish_checklist.md`

### Boundary

This workflow prepares high-quality publishable assets. It does not claim a stable official Zhihu direct-post API path.

## 中文

知乎发布当前采用“内容工厂”路径，而不是承诺稳定可用的直发 API 路径。

### 当前已具备

- `scripts/zhihu_marketing_agent.py`
- 面向知乎的标题、摘要、正文与标签建议
- 输出到 `data/marketing/zhihu/` 的发布清单

### 命令

```powershell
python scripts/zhihu_marketing_agent.py
```

### 输出位置

- `data/marketing/zhihu/article.json`
- `data/marketing/zhihu/article.md`
- `data/marketing/zhihu/publish_checklist.md`

### 边界

这条工作流负责生成高质量可发布资产，但不宣称当前存在稳定可依赖的知乎官方直发 API。

