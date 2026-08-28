# AMA-10 Cognition Memory

<div align="center">

<img src="https://count.getloli.com/@preca-hoshino?name=ama-10_cognition_memory&theme=rule34&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto" alt="Moe Counter">

**为 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 打造的智能长期记忆插件** — 完整的记忆生命周期、图记忆、多路召回，让机器人真正"记得住"。

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A54.24.2-green)
![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey)
[![Repo](https://img.shields.io/badge/repo-Restart--Game--Lab-blue)](https://github.com/Restart-Game-Lab/astrbot_plugin_ama-10_cognition_memory)

[中文](README.md) | [English](README_EN.md) | [日本語](README_JA.md)

</div>

---

## 简介

`astrbot_plugin_ama-10_cognition_memory` 是一个基于 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 的智能长期记忆插件。它会自动从群聊/私聊对话中提取、评估、存储、衰减、遗忘记忆，并结合知识图谱与多路召回，让机器人的"认知"真正持久化。本项目 Fork 自 [lxfight/astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory)。

## 特性

- **完整的记忆生命周期** — 从对话中自动提取、评估、存储、衰减、遗忘
- **图记忆** — 基于知识图谱的结构化记忆，支持实体关系抽取与推理
- **多路召回** — BM25 + 向量检索 + 图检索，RRF 融合排序
- **LLM Tool 集成** — 提供 `memorize_long_term_memory` / `recall_long_term_memory` 工具，让 Agent 主动管理记忆
- **LLM 上下文注入** — 在 LLM 请求前自动注入相关记忆
- **会话感知** — 区分群聊/私聊，支持按人格、会话隔离记忆
- **WebUI 管理** — 通过 AstrBot 仪表盘可视化管理记忆、图谱、召回调试
- **PostgreSQL 支持** — pgvector 向量后端，适合大规模部署
- **多语言** — 支持中文、英文、俄文

## 目录结构

```
astrbot_plugin_ama-10_cognition_memory/
├── main.py                 # 插件入口: 注册命令 + 初始化 + 生命周期
├── metadata.yaml           # 插件元数据
├── _conf_schema.json       # 插件配置面板 Schema
├── core/
│   ├── base/               # 基础配置、常量、异常
│   ├── managers/           # 记忆引擎、图记忆、会话、原子生命周期、备份
│   ├── models/             # 记忆原子、图谱、会话模型
│   ├── processors/         # 记忆提取/分类、图谱抽取、实体消歧、文本预处理
│   ├── retrieval/          # BM25 / 向量 / 图检索 + RRF 融合
│   ├── schedulers/         # 记忆衰减等定时任务
│   ├── tools/              # LLM Tools: memorize / recall
│   ├── prompts/            # LLM 提示词模板
│   ├── i18n/               # 多语言
│   ├── command_handler.py  # /lmem 指令处理
│   ├── event_handler.py    # 事件处理
│   └── plugin_initializer.py # 插件初始化
└── storage/                # PostgreSQL 存储层
    ├── pg_connection.py    # PG 连接池管理
    ├── pg_adapter.py       # asyncpg 兼容适配器
    ├── pg_vec_db.py        # pgvector 向量数据库
    ├── graph_store.py      # 图记忆存储
    ├── atom_store.py       # Atom 存储
    ├── conversation_store.py # 会话存储
    └── db_migration.py     # 数据库迁移
```

## 安装

### 前置要求

- AstrBot >= 4.24.2
- PostgreSQL >= 14（需 pgvector 扩展）

### 手动安装

```bash
cd /path/to/AstrBot/data/plugins
git clone https://github.com/Restart-Game-Lab/astrbot_plugin_ama-10_cognition_memory.git astrbot_plugin_ama_10_cognition_memory
```

然后在 AstrBot 管理面板中启用插件，重启 AstrBot。

### 依赖

```bash
pip install networkx jieba pytz aiofiles asyncpg
```

### PostgreSQL 配置

本插件**仅支持 PostgreSQL**（需要 pgvector 扩展）。安装 pgvector：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 配置

在 AstrBot 插件管理面板中配置，或直接编辑配置文件：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `database_settings.pg_dsn` | PostgreSQL 连接 URL | `""`（必填） |
| `bot_language` | 机器人回复语言（zh / en / ru） | `zh` |
| `provider_settings.llm_provider_id` | 记忆摘要用的 LLM 模型 ID | （AstrBot 默认） |
| `provider_settings.embedding_provider_id` | 向量化用的 Embedding 模型 ID | （AstrBot 默认） |
| `session_manager.*` | 会话缓存、上下文窗口大小 | — |
| `recall_engine.*` | 召回数量、记忆注入位置 | — |
| `importance_decay.*` | 记忆重要性随时间衰减 | — |
| `fusion_strategy.*` | 多路召回 RRF 融合参数 | — |
| `filtering_settings.*` | 按人格/会话隔离记忆 | — |
| `reflection_engine.*` | 对话总结触发轮次 | — |
| `agent_tools.*` | Agent 主动记忆工具开关 | — |
| `graph_memory.*` | 图记忆双路检索、记忆原子化 | — |
| `index_rebuild_settings.*` | 索引重建批量与限速 | — |
| `backup_settings.*` | 每日自动备份 | — |
| `forgetting_agent.*` | 旧记忆自动清理 | — |
| `migration_settings.*` | 数据库自动迁移 | — |

详细配置说明请参考 `_conf_schema.json` 中的注释。

## 使用

### 指令

| 指令 | 说明 |
|------|------|
| `/lmem status` | 查看系统状态 |
| `/lmem search <关键词> [数量]` | 搜索记忆（默认 5 条） |
| `/lmem forget <ID>` | 删除指定记忆 |
| `/lmem rebuild-index` | 重建索引（修复索引不一致） |
| `/lmem rebuild-graph` | 重建图记忆索引 |
| `/lmem webui` | 查看 WebUI 管理界面入口 |
| `/lmem summarize` | 立即触发当前会话的记忆总结 |
| `/lmem reset` | 重置当前会话记忆上下文 |
| `/lmem cleanup [preview\|exec]` | 清理历史消息中的记忆片段 |
| `/lmem help` | 显示帮助 |

### LLM Tools

插件向 LLM 注册了两个工具：

- **`memorize_long_term_memory`** — Agent 主动写入记忆（知识、偏好、事件等）
- **`recall_long_term_memory`** — Agent 主动检索相关记忆

### 自动上下文注入

插件在每次 LLM 请求前，自动检索与当前对话相关的记忆并注入到 system prompt 中，无需手动操作。

## 更新

执行 `git pull` 更新代码后，在 WebUI 对本插件执行「重载插件」或重启 AstrBot 即可。数据库会在启动时自动迁移（`migration_settings.auto_migrate`），无需手动升级。

## 许可证

本项目源代码基于 [GNU AGPL-3.0](LICENSE) 许可证开源，原始代码来自 [lxfight/astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory)（AGPL-3.0），本项目在同一协议下发布。

> **致谢**：感谢 **[lxfight](https://github.com/lxfight)** 原作者的贡献，以及 [AstrBot](https://github.com/AstrBotDevs/AstrBot)、[jieba](https://github.com/fxsjy/jieba)、[NetworkX](https://networkx.org/) 等开源项目的支持。
