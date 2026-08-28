# AMA-10 Cognition Memory

<div align="center">

<img src="https://count.getloli.com/@preca-hoshino?name=ama-10_cognition_memory&theme=rule34&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto" alt="Moe Counter">

**[AstrBot](https://github.com/AstrBotDevs/AstrBot) 向けのインテリジェント長期記憶プラグイン** — 完全な記憶ライフサイクル、グラフ記憶、複数経路検索で、ボットが本当に「覚えている」状態に。

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A54.24.2-green)
![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey)
[![Repo](https://img.shields.io/badge/repo-Restart--Game--Lab-blue)](https://github.com/Restart-Game-Lab/astrbot_plugin_ama-10_cognition_memory)

[中文](README.md) | [English](README_EN.md) | [日本語](README_JA.md)

</div>

---

## 概要

`astrbot_plugin_ama-10_cognition_memory` は [AstrBot](https://github.com/AstrBotDevs/AstrBot) ベースのインテリジェント長期記憶プラグインです。グループチャット/プライベートチャットの会話から記憶を自動的に抽出・評価・保存・減衰・忘却し、ナレッジグラフと複数経路検索を組み合わせることで、ボットの「認知」を本当に永続化します。本プロジェクトは [lxfight/astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory) からフォークされています。

## 特徴

- **完全な記憶ライフサイクル** — 会話からの自動抽出、評価、保存、減衰、忘却
- **グラフ記憶** — ナレッジグラフに基づく構造化記憶。エンティティ関係の抽出と推論に対応
- **複数経路検索** — BM25 + ベクトル検索 + グラフ検索、RRF 融合ソート
- **LLM ツール統合** — `memorize_long_term_memory` / `recall_long_term_memory` ツールでエージェントが自発的に記憶を管理
- **LLM コンテキスト注入** — LLM リクエスト前に自動的に関連記憶を注入
- **セッション認識** — グループ/プライベートを区別し、人格・セッション単位の記憶分離に対応
- **WebUI 管理** — AstrBot ダッシュボードから記憶・グラフ・検索デバッグを視覚的に管理
- **PostgreSQL 対応** — pgvector ベクトルバックエンド、大規模デプロイに最適
- **多言語対応** — 中国語、英語、ロシア語に対応

## ディレクトリ構成

```
astrbot_plugin_ama-10_cognition_memory/
├── main.py                 # プラグインエントリ: コマンド登録 + 初期化 + ライフサイクル
├── metadata.yaml           # プラグインメタデータ
├── _conf_schema.json       # プラグイン設定パネルスキーマ
├── core/
│   ├── base/               # 基本設定、定数、例外
│   ├── managers/           # 記憶エンジン、グラフ記憶、セッション、アトムライフサイクル、バックアップ
│   ├── models/             # 記憶アトム、グラフ、会話モデル
│   ├── processors/         # 記憶抽出/分類、グラフ抽出、エンティティ解決、テキスト前処理
│   ├── retrieval/          # BM25 / ベクトル / グラフ検索 + RRF 融合
│   ├── schedulers/         # 記憶減衰などの定期タスク
│   ├── tools/              # LLM ツール: memorize / recall
│   ├── prompts/            # LLM プロンプトテンプレート
│   ├── i18n/               # 多言語
│   ├── command_handler.py  # /lmem コマンド処理
│   ├── event_handler.py    # イベント処理
│   └── plugin_initializer.py # プラグイン初期化
└── storage/                # PostgreSQL ストレージ層
    ├── pg_connection.py    # PG 接続プール管理
    ├── pg_adapter.py       # asyncpg 互換アダプタ
    ├── pg_vec_db.py        # pgvector ベクトルデータベース
    ├── graph_store.py      # グラフ記憶ストレージ
    ├── atom_store.py       # アトムストレージ
    ├── conversation_store.py # 会話ストレージ
    └── db_migration.py     # データベースマイグレーション
```

## インストール

### 前提条件

- AstrBot >= 4.24.2
- PostgreSQL >= 14（pgvector 拡張が必要）

### 手動インストール

```bash
cd /path/to/AstrBot/data/plugins
git clone https://github.com/Restart-Game-Lab/astrbot_plugin_ama-10_cognition_memory.git astrbot_plugin_ama_10_cognition_memory
```

その後、AstrBot 管理パネルでプラグインを有効化し、AstrBot を再起動します。

### 依存関係

```bash
pip install networkx jieba pytz aiofiles asyncpg
```

### PostgreSQL 設定

本プラグインは**PostgreSQL のみ対応**（pgvector 拡張が必要）。pgvector のインストール:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 設定

AstrBot プラグイン管理パネルで設定するか、設定ファイルを直接編集します:

| 設定項目 | 説明 | デフォルト |
|--------|------|--------|
| `database_settings.pg_dsn` | PostgreSQL 接続 URL | `""`（必須） |
| `bot_language` | ボットの返信言語（zh / en / ru） | `zh` |
| `provider_settings.llm_provider_id` | 記憶要約に使用する LLM モデル ID | （AstrBot デフォルト） |
| `provider_settings.embedding_provider_id` | ベクトル化に使用する Embedding モデル ID | （AstrBot デフォルト） |
| `session_manager.*` | セッションキャッシュ、コンテキストウィンドウサイズ | — |
| `recall_engine.*` | 検索件数、記憶注入位置 | — |
| `importance_decay.*` | 記憶重要度の時間減衰 | — |
| `fusion_strategy.*` | 複数経路検索の RRF 融合パラメータ | — |
| `filtering_settings.*` | 人格/セッション単位の記憶分離 | — |
| `reflection_engine.*` | 会話要約のトリガーラウンド数 | — |
| `agent_tools.*` | エージェント自発的記憶ツールのオン/オフ | — |
| `graph_memory.*` | グラフ記憶の二重経路検索、記憶アトム化 | — |
| `index_rebuild_settings.*` | インデックス再構築のバッチサイズとレート制限 | — |
| `backup_settings.*` | 毎日自動バックアップ | — |
| `forgetting_agent.*` | 古い記憶の自動クリーンアップ | — |
| `migration_settings.*` | データベース自動マイグレーション | — |

詳細な設定説明は `_conf_schema.json` のコメントを参照してください。

## 使い方

### コマンド

| コマンド | 説明 |
|------|------|
| `/lmem status` | システム状態を表示 |
| `/lmem search <キーワード> [件数]` | 記憶を検索（デフォルト 5 件） |
| `/lmem forget <ID>` | 指定した記憶を削除 |
| `/lmem rebuild-index` | インデックスを再構築（不整合を修正） |
| `/lmem rebuild-graph` | グラフ記憶インデックスを再構築 |
| `/lmem webui` | WebUI 管理画面の入口を表示 |
| `/lmem summarize` | 現在のセッションの記憶要約を即時実行 |
| `/lmem reset` | 現在のセッションの記憶コンテキストをリセット |
| `/lmem cleanup [preview\|exec]` | 履歴メッセージ内の記憶フラグメントをクリーンアップ |
| `/lmem help` | ヘルプを表示 |

### LLM ツール

このプラグインは LLM に 2 つのツールを登録します:

- **`memorize_long_term_memory`** — エージェントが記憶を自発的に書き込む（知識、好み、出来事など）
- **`recall_long_term_memory`** — エージェントが関連記憶を自発的に検索

### 自動コンテキスト注入

LLM リクエストのたびに、現在の会話に関連する記憶を自動検索して system prompt に注入します。手動操作は不要です。

## 更新

`git pull` でコードを更新した後、WebUI でこのプラグインの「プラグインを再読み込み」を実行するか、AstrBot を再起動します。データベースは起動時に自動マイグレーションされます（`migration_settings.auto_migrate`）— 手動アップグレードは不要です。

## ライセンス

このプロジェクトは [GNU AGPL-3.0](LICENSE) の下でライセンスされています。元のコードは [lxfight/astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory)（AGPL-3.0）に由来し、本プロジェクトも同一ライセンスで公開されます。

> **謝辞**: 原作者 **[lxfight](https://github.com/lxfight)** の貢献、および [AstrBot](https://github.com/AstrBotDevs/AstrBot)、[jieba](https://github.com/fxsjy/jieba)、[NetworkX](https://networkx.org/) などのオープンソースプロジェクトのサポートに感謝します。
