from __future__ import annotations

from dataclasses import dataclass

from .models import CropMetadata, EquationRule


class CatalogRepository:
    def list_crops(self) -> list[CropMetadata]:
        raise NotImplementedError

    def list_rules(self, crop_code: str | None = None) -> list[EquationRule]:
        raise NotImplementedError


@dataclass
class InMemoryCatalogRepository(CatalogRepository):
    crops: list[CropMetadata]
    rules: list[EquationRule]

    @classmethod
    def empty(cls) -> "InMemoryCatalogRepository":
        return cls(crops=[], rules=[])

    @classmethod
    def demo_karnataka(cls) -> "InMemoryCatalogRepository":
        """
        In-memory mirror of `db/seed.sql` so `/recommend` works without Postgres during local dev.

        Coefficients are scaffold-only — not verified ICAR STCR extracts.
        """
        demo_source_id = "11111111-1111-1111-1111-111111111101"
        crops = [
            CropMetadata(
                crop_code="maize",
                crop_name="Maize",
                crop_group="cereal",
                default_target_yield_value=50.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif",),
            ),
            CropMetadata(
                crop_code="wheat",
                crop_name="Wheat",
                crop_group="cereal",
                default_target_yield_value=48.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif",),
            ),
            CropMetadata(
                crop_code="rice",
                crop_name="Rice",
                crop_group="cereal",
                default_target_yield_value=55.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif",),
            ),
            CropMetadata(
                crop_code="ragi",
                crop_name="Ragi",
                crop_group="millet",
                default_target_yield_value=25.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif",),
            ),
            CropMetadata(
                crop_code="groundnut",
                crop_name="Groundnut",
                crop_group="oilseed",
                default_target_yield_value=18.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif",),
            ),
        ]
        rules = [
            EquationRule(
                crop_code="maize",
                equation_family="STCR",
                geography_scope="state",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
                state_name="Karnataka",
                season_name="kharif",
                confidence_band="B",
                nr_n=2.0,
                nr_p=1.0,
                nr_k=1.2,
                cs_n=50.0,
                cs_p=25.0,
                cs_k=20.0,
                cf_n=50.0,
                cf_p=50.0,
                cf_k=50.0,
                c_org_n=0.0,
                c_org_p=0.0,
                c_org_k=0.0,
                source_doc_id=demo_source_id,
                source_title="SCAFFOLD: Karnataka demo coefficients (NOT verified ICAR STCR)",
                citation_text="Dev seed — replace with district STCR citation text from ICAR source registry.",
            ),
            EquationRule(
                crop_code="wheat",
                equation_family="STCR",
                geography_scope="state",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
                state_name="Karnataka",
                season_name="kharif",
                confidence_band="B",
                nr_n=2.1,
                nr_p=1.05,
                nr_k=1.1,
                cs_n=48.0,
                cs_p=24.0,
                cs_k=19.0,
                cf_n=50.0,
                cf_p=50.0,
                cf_k=50.0,
                c_org_n=0.0,
                c_org_p=0.0,
                c_org_k=0.0,
                source_doc_id=demo_source_id,
                source_title="SCAFFOLD: Karnataka demo coefficients (NOT verified ICAR STCR)",
                citation_text="Dev seed — replace with district STCR citation text from ICAR source registry.",
            ),
            EquationRule(
                crop_code="rice",
                equation_family="STCR",
                geography_scope="state",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
                state_name="Karnataka",
                season_name="kharif",
                confidence_band="B",
                nr_n=2.2,
                nr_p=1.0,
                nr_k=1.15,
                cs_n=52.0,
                cs_p=26.0,
                cs_k=21.0,
                cf_n=50.0,
                cf_p=50.0,
                cf_k=50.0,
                c_org_n=0.0,
                c_org_p=0.0,
                c_org_k=0.0,
                source_doc_id=demo_source_id,
                source_title="SCAFFOLD: Karnataka demo coefficients (NOT verified ICAR STCR)",
                citation_text="Dev seed — replace with district STCR citation text from ICAR source registry.",
            ),
            EquationRule(
                crop_code="ragi",
                equation_family="STCR",
                geography_scope="state",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
                state_name="Karnataka",
                season_name="kharif",
                confidence_band="B",
                nr_n=1.6,
                nr_p=0.8,
                nr_k=0.9,
                cs_n=45.0,
                cs_p=22.0,
                cs_k=18.0,
                cf_n=50.0,
                cf_p=50.0,
                cf_k=50.0,
                c_org_n=0.0,
                c_org_p=0.0,
                c_org_k=0.0,
                source_doc_id=demo_source_id,
                source_title="SCAFFOLD: Karnataka demo coefficients (NOT verified ICAR STCR)",
                citation_text="Dev seed — replace with district STCR citation text from ICAR source registry.",
            ),
            EquationRule(
                crop_code="groundnut",
                equation_family="STCR",
                geography_scope="state",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
                state_name="Karnataka",
                season_name="kharif",
                confidence_band="B",
                nr_n=1.4,
                nr_p=0.9,
                nr_k=1.0,
                cs_n=46.0,
                cs_p=23.0,
                cs_k=18.5,
                cf_n=50.0,
                cf_p=50.0,
                cf_k=50.0,
                c_org_n=0.0,
                c_org_p=0.0,
                c_org_k=0.0,
                source_doc_id=demo_source_id,
                source_title="SCAFFOLD: Karnataka demo coefficients (NOT verified ICAR STCR)",
                citation_text="Dev seed — replace with district STCR citation text from ICAR source registry.",
            ),
        ]
        return cls(crops=crops, rules=rules)

    def list_crops(self) -> list[CropMetadata]:
        return list(self.crops)

    def list_rules(self, crop_code: str | None = None) -> list[EquationRule]:
        if crop_code is None:
            return list(self.rules)
        return [rule for rule in self.rules if rule.crop_code == crop_code]
