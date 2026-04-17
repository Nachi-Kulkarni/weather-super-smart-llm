from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool

from ..domain.models import CropMetadata, EquationRule
from ..domain.repository import CatalogRepository

_psql_available = True
try:
    from psycopg_pool import ConnectionPool
except ImportError:
    ConnectionPool = None
    _psql_available = False


def _uuid_to_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    return str(value)


class PgCatalogRepository(CatalogRepository):
    """Load crops and STCR-style rules from Postgres (see `db/schema.sql`)."""

    def __init__(self, pool: "ConnectionPool") -> None:
        self._pool = pool

    def list_crops(self) -> list[CropMetadata]:
        sql = """
            SELECT c.crop_code,
                   c.crop_name,
                   c.crop_group,
                   c.default_target_yield_value,
                   c.default_target_yield_unit,
                   COALESCE(
                       array_agg(DISTINCT cc.season_name) FILTER (WHERE cc.season_name IS NOT NULL),
                       ARRAY[]::TEXT[]
                   ) AS season_names
            FROM crop c
            LEFT JOIN crop_calendar cc ON cc.crop_id = c.id
            GROUP BY c.crop_code, c.crop_name, c.crop_group,
                     c.default_target_yield_value, c.default_target_yield_unit
            ORDER BY c.crop_name
        """
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()

        crops: list[CropMetadata] = []
        for row in rows:
            code, name, group, default_yield, default_unit, season_names = row
            crops.append(
                CropMetadata(
                    crop_code=code,
                    crop_name=name,
                    crop_group=group,
                    default_target_yield_value=float(default_yield) if default_yield is not None else None,
                    default_target_yield_unit=default_unit,
                    season_names=tuple(season_names) if season_names else (),
                )
            )
        return crops

    def list_rules(self, crop_code: str | None = None) -> list[EquationRule]:
        params: list[Any] = []
        filter_sql = ""
        if crop_code is not None:
            filter_sql = "WHERE c.crop_code = %s"
            params.append(crop_code)

        sql = f"""
            SELECT c.crop_code,
                   e.equation_family,
                   e.geography_scope,
                   e.nutrient_basis,
                   e.target_yield_unit,
                   e.state_name,
                   e.district_name,
                   e.agro_region_code,
                   e.soil_order,
                   e.season_name,
                   e.confidence_band,
                   e.nr_n,
                   e.nr_p,
                   e.nr_k,
                   e.cs_n,
                   e.cs_p,
                   e.cs_k,
                   e.cf_n,
                   e.cf_p,
                   e.cf_k,
                   e.c_org_n,
                   e.c_org_p,
                   e.c_org_k,
                   e.source_doc_id,
                   sd.title AS source_title,
                   e.citation_text
            FROM stcr_equation e
            JOIN crop c ON c.id = e.crop_id
            LEFT JOIN source_document sd ON sd.id = e.source_doc_id
            {filter_sql}
            ORDER BY e.equation_family, e.geography_scope
        """
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        rules: list[EquationRule] = []
        for row in rows:
            rules.append(
                EquationRule(
                    crop_code=row[0],
                    equation_family=row[1],
                    geography_scope=row[2],
                    nutrient_basis=row[3],
                    target_yield_unit=row[4],
                    state_name=row[5],
                    district_name=row[6],
                    agro_region_code=row[7],
                    soil_order=row[8],
                    season_name=row[9],
                    confidence_band=row[10],
                    nr_n=float(row[11]) if row[11] is not None else None,
                    nr_p=float(row[12]) if row[12] is not None else None,
                    nr_k=float(row[13]) if row[13] is not None else None,
                    cs_n=float(row[14]) if row[14] is not None else None,
                    cs_p=float(row[15]) if row[15] is not None else None,
                    cs_k=float(row[16]) if row[16] is not None else None,
                    cf_n=float(row[17]) if row[17] is not None else None,
                    cf_p=float(row[18]) if row[18] is not None else None,
                    cf_k=float(row[19]) if row[19] is not None else None,
                    c_org_n=float(row[20]) if row[20] is not None else None,
                    c_org_p=float(row[21]) if row[21] is not None else None,
                    c_org_k=float(row[22]) if row[22] is not None else None,
                    source_doc_id=_uuid_to_str(row[23]),
                    source_title=row[24],
                    citation_text=row[25],
                )
            )
        return rules
