# AMA-10 Cognition Memory

<div align="center">

<img src="https://count.getloli.com/@preca-hoshino?name=ama-10_cognition_memory&theme=rule34&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto" alt="Moe Counter">

**An intelligent long-term memory plugin for [AstrBot](https://github.com/AstrBotDevs/AstrBot)** — Full memory lifecycle, graph memory, and multi-route retrieval, so your bot truly "remembers".

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A54.24.2-green)
![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey)
[![Repo](https://img.shields.io/badge/repo-Restart--Game--Lab-blue)](https://github.com/Restart-Game-Lab/astrbot_plugin_ama-10_cognition_memory)

[中文](README.md) | [English](README_EN.md) | [日本語](README_JA.md)

</div>

---

## Introduction

`astrbot_plugin_ama-10_cognition_memory` is an intelligent long-term memory plugin built on [AstrBot](https://github.com/AstrBotDevs/AstrBot). It automatically extracts, evaluates, stores, decays, and forgets memories from group/private conversations, and combines a knowledge graph with multi-route retrieval so that the bot's "cognition" truly persists. This project is forked from [lxfight/astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory).

## Features

- **Full memory lifecycle** — Automatic extraction, evaluation, storage, decay, and forgetting from conversations
- **Graph memory** — Structured memory based on a knowledge graph with entity-relation extraction and reasoning
- **Multi-route retrieval** — BM25 + vector search + graph search, fused with RRF ranking
- **LLM Tool integration** — `memorize_long_term_memory` / `recall_long_term_memory` tools so the Agent can manage memory proactively
- **LLM context injection** — Automatically injects relevant memories before each LLM request
- **Session-aware** — Distinguishes group/private chats, supports per-persona and per-session memory isolation
- **WebUI management** — Manage memories, graphs, and recall debugging visually via the AstrBot dashboard
- **PostgreSQL support** — pgvector vector backend, suitable for large-scale deployments
- **Multilingual** — Supports Chinese, English, and Russian

## Project Structure

```
astrbot_plugin_ama-10_cognition_memory/
├── main.py                 # Plugin entry: registers commands + initialization + lifecycle
├── metadata.yaml           # Plugin metadata
├── _conf_schema.json       # Plugin config panel schema
├── core/
│   ├── base/               # Base config, constants, exceptions
│   ├── managers/           # Memory engine, graph memory, sessions, atom lifecycle, backup
│   ├── models/             # Memory atom, graph, conversation models
│   ├── processors/         # Memory extraction/classification, graph extraction, entity resolution, text preprocessing
│   ├── retrieval/          # BM25 / vector / graph retrieval + RRF fusion
│   ├── schedulers/         # Memory decay and other scheduled tasks
│   ├── tools/              # LLM Tools: memorize / recall
│   ├── prompts/            # LLM prompt templates
│   ├── i18n/               # Multilingual
│   ├── command_handler.py  # /lmem command handling
│   ├── event_handler.py    # Event handling
│   └── plugin_initializer.py # Plugin initialization
└── storage/                # PostgreSQL storage layer
    ├── pg_connection.py    # PG connection pool management
    ├── pg_adapter.py       # asyncpg-compatible adapter
    ├── pg_vec_db.py        # pgvector vector database
    ├── graph_store.py      # Graph memory storage
    ├── atom_store.py       # Atom storage
    ├── conversation_store.py # Conversation storage
    └── db_migration.py     # Database migration
```

## Installation

### Prerequisites

- AstrBot >= 4.24.2
- PostgreSQL >= 14 (with the pgvector extension)

### Manual Installation

```bash
cd /path/to/AstrBot/data/plugins
git clone https://github.com/Restart-Game-Lab/astrbot_plugin_ama-10_cognition_memory.git astrbot_plugin_ama_10_cognition_memory
```

Then enable the plugin in the AstrBot management panel and restart AstrBot.

### Dependencies

```bash
pip install networkx jieba pytz aiofiles asyncpg
```

### PostgreSQL Configuration

This plugin **only supports PostgreSQL** (requires the pgvector extension). Install pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Configuration

Configure in the AstrBot plugin management panel, or directly edit the config file:

| Config key | Description | Default |
|--------|------|--------|
| `database_settings.pg_dsn` | PostgreSQL connection URL | `""` (required) |
| `bot_language` | Bot reply language (zh / en / ru) | `zh` |
| `provider_settings.llm_provider_id` | LLM model ID for memory summarization | (AstrBot default) |
| `provider_settings.embedding_provider_id` | Embedding model ID for embeddings | (AstrBot default) |
| `session_manager.*` | Session cache, context window size | — |
| `recall_engine.*` | Recall count, memory injection position | — |
| `importance_decay.*` | Memory importance decay over time | — |
| `fusion_strategy.*` | RRF fusion parameters for multi-route retrieval | — |
| `filtering_settings.*` | Per-persona/session memory isolation | — |
| `reflection_engine.*` | Conversation summary trigger rounds | — |
| `agent_tools.*` | Agent proactive memory tool switches | — |
| `graph_memory.*` | Graph memory dual-route retrieval, memory atomization | — |
| `index_rebuild_settings.*` | Index rebuild batch size and rate limits | — |
| `backup_settings.*` | Daily automatic backup | — |
| `forgetting_agent.*` | Automatic cleanup of old memories | — |
| `migration_settings.*` | Automatic database migration | — |

See the comments in `_conf_schema.json` for detailed configuration descriptions.

## Usage

### Commands

| Command | Description |
|------|------|
| `/lmem status` | View system status |
| `/lmem search <keyword> [count]` | Search memories (default 5) |
| `/lmem forget <ID>` | Delete a specific memory |
| `/lmem rebuild-index` | Rebuild index (fix index inconsistencies) |
| `/lmem rebuild-graph` | Rebuild graph memory index |
| `/lmem webui` | View WebUI management entry |
| `/lmem summarize` | Trigger memory summary for the current session immediately |
| `/lmem reset` | Reset current session memory context |
| `/lmem cleanup [preview\|exec]` | Clean up memory fragments in historical messages |
| `/lmem help` | Show help |

### LLM Tools

The plugin registers two tools with the LLM:

- **`memorize_long_term_memory`** — Agent actively writes memories (knowledge, preferences, events, etc.)
- **`recall_long_term_memory`** — Agent actively recalls relevant memories

### Automatic Context Injection

Before each LLM request, the plugin automatically retrieves memories relevant to the current conversation and injects them into the system prompt — no manual action needed.

## Updating

Run `git pull` to update the code, then select "Reload Plugin" for this plugin in the WebUI or restart AstrBot. The database is migrated automatically at startup (`migration_settings.auto_migrate`) — no manual upgrade needed.

## License

This project is licensed under [GNU AGPL-3.0](LICENSE). The original code comes from [lxfight/astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory) (AGPL-3.0), and this project is released under the same license.

> **Acknowledgements**: Thanks to **[lxfight](https://github.com/lxfight)** for the original author's contribution, as well as the support of [AstrBot](https://github.com/AstrBotDevs/AstrBot), [jieba](https://github.com/fxsjy/jieba), [NetworkX](https://networkx.org/) and other open-source projects.
