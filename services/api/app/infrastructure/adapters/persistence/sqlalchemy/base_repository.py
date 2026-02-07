"""Base SQLAlchemy repository with shared query helpers."""
from __future__ import annotations

from typing import List, Union

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.orm import Session

from app.domain.value_objects.tenant_id import TenantId


class BaseSQLAlchemyRepository:
    """Common SQL helper methods to reduce duplication."""

    def __init__(self, db: Session):
        self.db = db

    def _execute_query(
        self,
        sql: Union[str, TextClause],
        params: dict,
        fetch_one: bool = False,
    ) -> Union[dict, list[dict], None]:
        statement = sql if isinstance(sql, TextClause) else text(sql)
        result = self.db.execute(statement, params)

        if fetch_one:
            row = result.fetchone()
            return dict(row._mapping) if row else None

        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    def _ensure_tenant_filter(self, tenant_id: TenantId, params: dict) -> dict:
        params["tenant_id"] = str(tenant_id.value)
        return params

    def _paginate(
        self,
        sql: str,
        params: dict,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[dict], bool]:
        params["limit"] = limit + 1
        params["offset"] = offset

        rows = self._execute_query(sql, params)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        return rows, has_more
