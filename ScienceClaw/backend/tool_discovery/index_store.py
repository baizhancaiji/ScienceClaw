from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .aliases import expand_query_terms, get_tool_category_sort_index, normalize_text
from .schemas import ToolIndexItem, ToolSearchHit


class ToolIndexStore:
    """Rebuildable SQLite FTS5 index for lightweight tool search."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_index (
              tool_ref TEXT PRIMARY KEY,
              source_type TEXT NOT NULL,
              name TEXT NOT NULL,
              display_name TEXT NOT NULL,
              name_zh TEXT NOT NULL,
              description TEXT NOT NULL,
              description_zh TEXT NOT NULL,
              category_zh TEXT NOT NULL,
              aliases TEXT NOT NULL,
              keywords TEXT NOT NULL,
              provider TEXT NOT NULL,
              enabled INTEGER NOT NULL,
              blocked INTEGER NOT NULL,
              schema_status TEXT NOT NULL,
              has_examples INTEGER NOT NULL,
              last_success_at INTEGER
            )
            """
        )
        self._conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS tool_index_fts USING fts5(
              tool_ref UNINDEXED,
              name,
              display_name,
              name_zh,
              description,
              description_zh,
              category_zh,
              aliases,
              keywords,
              provider
            )
            """
        )
        self._conn.commit()

    def rebuild(self, items: Iterable[ToolIndexItem]) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM tool_index")
            self._conn.execute("DELETE FROM tool_index_fts")
            for item in items:
                self._insert_item(item)

    def is_empty(self) -> bool:
        row = self._conn.execute("SELECT COUNT(*) AS count FROM tool_index").fetchone()
        return int(row["count"]) == 0

    def _insert_item(self, item: ToolIndexItem) -> None:
        values = {
            **item.model_dump(),
            "display_name": item.display_name or item.name,
            "aliases": json.dumps(item.aliases, ensure_ascii=False),
            "keywords": json.dumps(item.keywords, ensure_ascii=False),
            "enabled": 1 if item.enabled else 0,
            "blocked": 1 if item.blocked else 0,
            "has_examples": 1 if item.has_examples else 0,
        }
        self._conn.execute(
            """
            INSERT INTO tool_index (
              tool_ref, source_type, name, display_name, name_zh, description,
              description_zh, category_zh, aliases, keywords, provider, enabled,
              blocked, schema_status, has_examples, last_success_at
            ) VALUES (
              :tool_ref, :source_type, :name, :display_name, :name_zh, :description,
              :description_zh, :category_zh, :aliases, :keywords, :provider, :enabled,
              :blocked, :schema_status, :has_examples, :last_success_at
            )
            """,
            values,
        )
        self._conn.execute(
            """
            INSERT INTO tool_index_fts (
              tool_ref, name, display_name, name_zh, description, description_zh,
              category_zh, aliases, keywords, provider
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.tool_ref,
                item.name,
                item.display_name or item.name,
                item.name_zh,
                item.description,
                item.description_zh,
                item.category_zh,
                " ".join(item.aliases),
                " ".join(item.keywords),
                item.provider,
            ),
        )

    def search(
        self,
        query: str,
        *,
        source_type: str | None = None,
        category_zh: str | None = None,
        limit: int = 30,
    ) -> list[ToolSearchHit]:
        terms = expand_query_terms(query)
        fts_scores = self._fts_scores(terms) if terms else {}
        rows = self._candidate_rows(source_type=source_type, category_zh=category_zh)
        hits: list[ToolSearchHit] = []
        for row in rows:
            item = self._row_to_item(row)
            score, hit_fields = self._score_item(item, terms)
            if item.tool_ref in fts_scores:
                score += fts_scores[item.tool_ref]
                if "fts" not in hit_fields:
                    hit_fields.append("fts")
            if terms and score <= 0:
                continue
            hits.append(ToolSearchHit(item=item, score=score, hit_fields=hit_fields))
        hits.sort(
            key=lambda hit: (
                -hit.score,
                get_tool_category_sort_index(hit.item.category_zh),
                hit.item.display_name or hit.item.name,
            )
        )
        return hits[:limit]

    def _candidate_rows(self, *, source_type: str | None, category_zh: str | None) -> list[sqlite3.Row]:
        clauses = ["enabled = 1", "blocked = 0"]
        params: list[str] = []
        if source_type:
            clauses.append("source_type = ?")
            params.append(source_type)
        if category_zh:
            clauses.append("category_zh = ?")
            params.append(category_zh)
        where = " AND ".join(clauses)
        return list(self._conn.execute(f"SELECT * FROM tool_index WHERE {where}", params))

    def _fts_scores(self, terms: list[str]) -> dict[str, float]:
        fts_query = self._fts_query(terms)
        if not fts_query:
            return {}
        try:
            rows = self._conn.execute(
                """
                SELECT tool_ref, bm25(tool_index_fts) AS rank
                FROM tool_index_fts
                WHERE tool_index_fts MATCH ?
                LIMIT 100
                """,
                (fts_query,),
            ).fetchall()
        except sqlite3.Error:
            return {}
        scores: dict[str, float] = {}
        for row in rows:
            # bm25 is lower for better matches. Convert it to a positive bonus.
            scores[str(row["tool_ref"])] = max(0.0, 10.0 - float(row["rank"]))
        return scores

    @staticmethod
    def _fts_query(terms: list[str]) -> str:
        safe_terms = []
        for term in terms:
            cleaned = term.replace('"', " ").strip()
            if cleaned:
                safe_terms.append(f'"{cleaned}"')
        return " OR ".join(safe_terms[:20])

    @staticmethod
    def _score_item(item: ToolIndexItem, terms: list[str]) -> tuple[float, list[str]]:
        if not terms:
            return 1.0, []
        weighted_fields = [
            ("name", item.name, 5.0),
            ("display_name", item.display_name, 5.0),
            ("name_zh", item.name_zh, 6.0),
            ("category_zh", item.category_zh, 4.0),
            ("aliases", " ".join(item.aliases), 4.0),
            ("keywords", " ".join(item.keywords), 3.0),
            ("provider", item.provider, 2.0),
            ("description_zh", item.description_zh, 2.0),
            ("description", item.description, 1.0),
        ]
        score = 0.0
        hit_fields: list[str] = []
        for field, value, weight in weighted_fields:
            normalized = normalize_text(value)
            if not normalized:
                continue
            for term in terms:
                if term and term in normalized:
                    score += weight
                    if field not in hit_fields:
                        hit_fields.append(field)
        if item.has_examples:
            score += 0.1
        if item.schema_status == "available":
            score += 0.2
        return score, hit_fields

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> ToolIndexItem:
        return ToolIndexItem(
            tool_ref=row["tool_ref"],
            source_type=row["source_type"],
            name=row["name"],
            display_name=row["display_name"],
            name_zh=row["name_zh"],
            description=row["description"],
            description_zh=row["description_zh"],
            category_zh=row["category_zh"],
            aliases=json.loads(row["aliases"] or "[]"),
            keywords=json.loads(row["keywords"] or "[]"),
            provider=row["provider"],
            enabled=bool(row["enabled"]),
            blocked=bool(row["blocked"]),
            schema_status=row["schema_status"],
            has_examples=bool(row["has_examples"]),
            last_success_at=row["last_success_at"],
        )
