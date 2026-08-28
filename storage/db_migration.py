"""
数据库迁移管理器 - PostgreSQL schema 自举

此前版本依赖外部迁移脚本创建表结构（含 tsv 列与触发器），但仓库从未提供
该脚本，导致:
  - documents / memory_atoms / graph_entries 缺少 tsv 列 → BM25 检索报
    "column tsv does not exist"
  - graph_nodes.created_at / updated_at 列类型错误（float8）
    → upsert_node 传 datetime 报 "must be real number, not datetime"

本模块在插件初始化时自动:
  1. 创建缺失的表（幂等，IF NOT EXISTS）
  2. 补齐缺失的列（ALTER TABLE ... ADD COLUMN IF NOT EXISTS）
  3. 为 tsv 列创建或重建触发器（保证更新时同步 tsvector）
  4. 修正错误的列类型（graph 表时间列 → timestamptz）
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("astrbot_plugin_ama_10_cognition_memory.migration")

# ---------------------------------------------------------------------------
# 表结构定义
# 说明:
#   - conversation 表时间列使用 DOUBLE PRECISION（代码传 time.time()）
#   - graph 表时间列使用 TIMESTAMPTZ（代码传 datetime.now(timezone.utc)）
#   - atoms 表时间列使用 DOUBLE PRECISION（代码传 time.time()）
# ---------------------------------------------------------------------------

# (table, create_sql, extra_ddl)
_TABLES: list[dict[str, Any]] = [
    {
        "table": "sessions",
        "sql": """
            CREATE TABLE IF NOT EXISTS sessions (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL UNIQUE,
                platform TEXT,
                created_at DOUBLE PRECISION,
                last_active_at DOUBLE PRECISION,
                message_count INTEGER DEFAULT 0,
                participants JSONB DEFAULT '[]'::jsonb,
                metadata JSONB DEFAULT '{}'::jsonb
            )
        """,
    },
    {
        "table": "messages",
        "sql": """
            CREATE TABLE IF NOT EXISTS messages (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT,
                content TEXT,
                sender_id TEXT,
                sender_name TEXT,
                group_id TEXT,
                platform TEXT,
                timestamp DOUBLE PRECISION,
                metadata JSONB DEFAULT '{}'::jsonb
            )
        """,
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)",
        ],
    },
    {
        "table": "documents",
        "sql": """
            CREATE TABLE IF NOT EXISTS documents (
                id BIGSERIAL PRIMARY KEY,
                doc_id TEXT NOT NULL UNIQUE,
                text TEXT NOT NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at DOUBLE PRECISION DEFAULT 0,
                updated_at DOUBLE PRECISION DEFAULT 0
            )
        """,
        "tsv": True,
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_documents_tsv ON documents USING GIN (tsv)",
        ],
    },
    {
        "table": "documents_vec",
        "sql": """
            CREATE TABLE IF NOT EXISTS documents_vec (
                doc_id BIGINT PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
                embedding vector(1024)
            )
        """,
    },
    {
        "table": "graph_documents",
        "sql": """
            CREATE TABLE IF NOT EXISTS graph_documents (
                id BIGSERIAL PRIMARY KEY,
                doc_id TEXT NOT NULL UNIQUE,
                text TEXT NOT NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at DOUBLE PRECISION DEFAULT 0,
                updated_at DOUBLE PRECISION DEFAULT 0
            )
        """,
        "tsv": True,
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_graph_documents_tsv ON graph_documents USING GIN (tsv)",
        ],
    },
    {
        "table": "graph_documents_vec",
        "sql": """
            CREATE TABLE IF NOT EXISTS graph_documents_vec (
                doc_id BIGINT PRIMARY KEY REFERENCES graph_documents(id) ON DELETE CASCADE,
                embedding vector(1024)
            )
        """,
    },
    {
        "table": "memory_atoms",
        "sql": """
            CREATE TABLE IF NOT EXISTS memory_atoms (
                id BIGSERIAL PRIMARY KEY,
                parent_memory_id BIGINT,
                atom_type TEXT,
                content TEXT,
                entities JSONB DEFAULT '{}'::jsonb,
                importance DOUBLE PRECISION DEFAULT 0.5,
                confidence DOUBLE PRECISION DEFAULT 0.5,
                created_at DOUBLE PRECISION,
                last_accessed_at DOUBLE PRECISION,
                last_reinforced_at DOUBLE PRECISION,
                event_time DOUBLE PRECISION,
                ttl_days DOUBLE PRECISION,
                expires_at DOUBLE PRECISION,
                status TEXT DEFAULT 'active',
                reinforcement_count INTEGER DEFAULT 0,
                decay_type TEXT,
                session_id TEXT,
                persona_id TEXT,
                metadata JSONB DEFAULT '{}'::jsonb
            )
        """,
        "tsv": True,
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_atoms_parent ON memory_atoms (parent_memory_id)",
            "CREATE INDEX IF NOT EXISTS idx_atoms_tsv ON memory_atoms USING GIN (tsv)",
            "CREATE INDEX IF NOT EXISTS idx_atoms_session ON memory_atoms (session_id)",
        ],
    },
    {
        "table": "graph_nodes",
        "sql": """
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id BIGSERIAL PRIMARY KEY,
                node_key TEXT NOT NULL UNIQUE,
                node_type TEXT,
                node_value TEXT,
                canonical_value TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "time_columns": ["created_at", "updated_at"],  # 期望 TIMESTAMPTZ
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_graph_nodes_canonical ON graph_nodes (canonical_value)",
        ],
    },
    {
        "table": "graph_edges",
        "sql": """
            CREATE TABLE IF NOT EXISTS graph_edges (
                id BIGSERIAL PRIMARY KEY,
                edge_key TEXT NOT NULL UNIQUE,
                source_node_id BIGINT REFERENCES graph_nodes(id) ON DELETE CASCADE,
                target_node_id BIGINT REFERENCES graph_nodes(id) ON DELETE CASCADE,
                relation_type TEXT,
                source_memory_id BIGINT,
                weight DOUBLE PRECISION DEFAULT 1.0,
                confidence DOUBLE PRECISION DEFAULT 0.8,
                status TEXT DEFAULT 'active',
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "time_columns": ["created_at", "updated_at"],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges (source_node_id)",
            "CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges (target_node_id)",
            "CREATE INDEX IF NOT EXISTS idx_graph_edges_memory ON graph_edges (source_memory_id)",
        ],
    },
    {
        "table": "graph_entries",
        "sql": """
            CREATE TABLE IF NOT EXISTS graph_entries (
                id BIGSERIAL PRIMARY KEY,
                entry_key TEXT NOT NULL UNIQUE,
                source_memory_id BIGINT,
                session_id TEXT,
                persona_id TEXT,
                entry_type TEXT,
                relation_type TEXT,
                content TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                edge_id BIGINT,
                vector_doc_id BIGINT,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "tsv": True,
        # 历史表可能为 DOUBLE PRECISION，需修正
        "time_columns": ["created_at", "updated_at"],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_graph_entries_tsv ON graph_entries USING GIN (tsv)",
            "CREATE INDEX IF NOT EXISTS idx_graph_entries_memory ON graph_entries (source_memory_id)",
        ],
    },
    {
        "table": "graph_entry_nodes",
        "sql": """
            CREATE TABLE IF NOT EXISTS graph_entry_nodes (
                entry_id BIGINT REFERENCES graph_entries(id) ON DELETE CASCADE,
                node_id BIGINT REFERENCES graph_nodes(id) ON DELETE CASCADE,
                PRIMARY KEY (entry_id, node_id)
            )
        """,
    },
]

# 需要 tsv 列 + 触发器的表
_TSV_TABLES = ["documents", "graph_documents", "memory_atoms", "graph_entries"]

# 时间列类型期望映射: (表名, 列) -> 期望类型
_TIME_COL_EXPECT: dict[tuple[str, str], str] = {
    ("graph_nodes", "created_at"): "timestamp with time zone",
    ("graph_nodes", "updated_at"): "timestamp with time zone",
    ("graph_edges", "created_at"): "timestamp with time zone",
    ("graph_edges", "updated_at"): "timestamp with time zone",
    ("graph_entries", "created_at"): "timestamp with time zone",
    ("graph_entries", "updated_at"): "timestamp with time zone",
}


def _trigger_function_sql(schema: str) -> str:
    """返回统一的 tsvector 触发器函数定义（按表名生成不同的列引用）。"""
    return f"""
        CREATE OR REPLACE FUNCTION {schema}.fn_tsv_sync()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_TABLE_NAME = 'documents' THEN
                NEW.tsv := to_tsvector('simple', COALESCE(NEW.text, ''));
            ELSIF TG_TABLE_NAME = 'graph_documents' THEN
                NEW.tsv := to_tsvector('simple', COALESCE(NEW.text, ''));
            ELSIF TG_TABLE_NAME = 'memory_atoms' THEN
                NEW.tsv := to_tsvector('simple', COALESCE(NEW.content, ''));
            ELSIF TG_TABLE_NAME = 'graph_entries' THEN
                NEW.tsv := to_tsvector('simple', COALESCE(NEW.content, ''));
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """


def _create_ddl(schema: str = "livingmemory") -> list[str]:
    """生成完整的 DDL 语句列表（幂等），指定目标 schema。

    关键: 若用户旧表建在 public，自举必须作用于 public，否则旧数据
    在新 schema 中不可见（表现为"记忆全部消失"）。
    """
    ddl: list[str] = []

    # 1. schema + 扩展
    ddl.append(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    ddl.append("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. 建表（目标 schema）
    for spec in _TABLES:
        ddl.append(spec["sql"].replace("CREATE TABLE IF NOT EXISTS ", f"CREATE TABLE IF NOT EXISTS {schema}.", 1))

    # 3. 触发器函数（只创建一次）
    ddl.append(_trigger_function_sql(schema))

    # 4. tsv 列（旧表可能没有）
    for tname in _TSV_TABLES:
        ddl.append(f"ALTER TABLE {schema}.{tname} ADD COLUMN IF NOT EXISTS tsv tsvector")

    # 5. 触发器（重建，保证最新定义）
    for tname in _TSV_TABLES:
        ddl.append(f"DROP TRIGGER IF EXISTS trg_{tname}_tsv ON {schema}.{tname}")
        ddl.append(
            f"""
            CREATE TRIGGER trg_{tname}_tsv
            BEFORE INSERT OR UPDATE ON {schema}.{tname}
            FOR EACH ROW EXECUTE FUNCTION {schema}.fn_tsv_sync()
            """
        )

    # 6. 索引
    for spec in _TABLES:
        for idx in spec.get("indexes", []):
            ddl.append(idx.replace(" ON ", f" ON {schema}.", 1))

    # 7. 修正 graph 表时间列类型（float8 → timestamptz）
    for (tname, col), _expected in _TIME_COL_EXPECT.items():
        ddl.append(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = '{schema}'
                      AND table_name = '{tname}'
                      AND column_name = '{col}'
                      AND data_type NOT IN ('timestamp with time zone', 'timestamp without time zone')
                ) THEN
                    ALTER TABLE {schema}.{tname}
                    ALTER COLUMN {col} TYPE timestamptz
                    USING to_timestamp({col});
                END IF;
            END $$
            """
        )

    return ddl


async def _detect_schema(pool) -> str:
    """探测存储层实际使用的 schema。

    优先级:
      1. livingmemory.documents 存在 → livingmemory
      2. public.documents 存在 → public
      3. 默认 livingmemory
    """
    try:
        row = await pool.fetchrow(
            "SELECT to_regclass('livingmemory.documents') AS lmm, "
            "to_regclass('public.documents') AS pub"
        )
        if row and row["lmm"] is not None:
            return "livingmemory"
        if row and row["pub"] is not None:
            return "public"
    except Exception:
        pass
    return "livingmemory"


class DBMigration:
    """数据库迁移管理器 (PostgreSQL schema 自举)"""

    CURRENT_VERSION = 8

    VERSION_HISTORY = {
        1: "初始版本 - 基础记忆存储",
        2: "FTS5索引预处理",
        3: "会话ID迁移",
        4: "Schema v2 双通道总结字段",
        5: "Graph memory",
        6: "FTS 表前缀化",
        7: "PG schema 自举: 建表 + tsv 触发器 + 时间列类型修正",
        8: "向量维度检测修复: 无维度约束 vector(atttypmod=-1) 不再误判/清空",
    }

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def ensure_schema(self, pool=None) -> dict[str, Any]:
        """幂等地创建/补齐 PG schema，返回执行摘要。

        在插件初始化时调用（init_pool 之后），保证所有存储层引用的
        表/列/触发器一定存在。
        """
        if pool is None:
            from .pg_connection import get_pool

            pool = get_pool()

        schema = await _detect_schema(pool)
        logger.info(f"[迁移] 目标 schema: {schema}")

        # 同步连接池 search_path：若旧数据在 public 而 pool 仍指向 livingmemory，
        # 新建的表会落入 livingmemory，导致新旧数据分裂（旧数据不可见）
        try:
            from .pg_connection import set_search_path

            set_search_path(schema)
            # 逐个同步池中已存在的连接（asyncpg 私有 _holders，失败则忽略）
            for _holder in getattr(pool, "_holders", []):
                _conn = getattr(_holder, "con", None)
                if _conn is not None:
                    try:
                        await _conn.execute(f"SET search_path TO {schema},public")
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"[迁移] 更新 search_path 失败（忽略）: {e}")

        executed = 0
        skipped = 0

        for ddl in _create_ddl(schema):
            try:
                await pool.execute(ddl)
                executed += 1
            except Exception as e:
                # 幂等失败不致命，记录后继续（例如 vector 扩展缺失）
                logger.warning(f"[迁移] DDL 执行失败（跳过）: {str(e)[:120]}")
                skipped += 1

        logger.info(f"[迁移] PG schema 自举完成: 执行 {executed} 条 DDL，跳过 {skipped} 条")
        return {
            "success": True,
            "message": f"PG schema 自举完成 (schema={schema}, DDL {executed} 条)",
            "duration": 0,
            "schema": schema,
            "executed": executed,
            "skipped": skipped,
        }

    async def ensure_vector_dimension(self, pool, table: str) -> int | None:
        """检查向量表当前声明的维度，返回维度或 None。

        用于 PgVecDB 在维度不匹配时决定是否清空旧维度向量。
        """
        try:
            row = await pool.fetchrow(
                """
                SELECT atttypmod
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = ANY(current_schemas(false))
                  AND c.relname = $1 AND a.attname = 'embedding'
                """,
                table,
            )
            if row and row["atttypmod"] is not None and int(row["atttypmod"]) != -1:
                # vector 维度 = typmod - 4 (VECTOR_TYPEMOD_HEADER)
                # atttypmod == -1 表示无维度约束的 vector，维度由数据决定，返回 None
                return int(row["atttypmod"]) - 4
        except Exception:
            pass
        return None

    async def get_db_version(self) -> int:
        return self.CURRENT_VERSION

    async def needs_migration(self) -> bool:
        return False  # schema 自举在初始化时执行，此接口仅为兼容

    async def migrate(self, progress_callback=None) -> dict[str, Any]:
        return await self.ensure_schema(None)

    async def create_backup(self) -> str | None:
        return None

    async def get_migration_info(self) -> dict[str, Any]:
        return {
            "current_version": self.CURRENT_VERSION,
            "latest_version": self.CURRENT_VERSION,
            "needs_migration": False,
        }
