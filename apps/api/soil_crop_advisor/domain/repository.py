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
    def stcr_reference(cls) -> "InMemoryCatalogRepository":
        """
        STCR REFERENCE DATA for Karnataka (UAS Bangalore 2022-2026).

        This is a REFERENCE dataset - NOT comprehensive coverage.
        Use it as a reference example for:
        - STCR equation structure and coefficients
        - How district-level rules work
        - Confidence band A for verified equations

        Coverage (limited to these locations only):
        - Crops: maize, aerobic_rice, green_gram, ragi, little_millet, coriander, groundnut, sunflower
        - Districts: Tumkur, Shimoga, Hassan, Chikmagalur (Eastern & Southern dry zones)
        - Seasons: kharif, rabi
        - Soils: Alfisols, Vertisols

        Behavior:
        - When location IS one of these districts + crop matches: returns STCR rule (A)
        - When location is OTHER Karnataka or other state: returns no match (proper fallback)
        - Use this to understand STCR structure; ingest full STCR registry for production
        """
        stcr_karnataka_source = "uasb-stcr-2022-2026-001"
        stcr_ipns_source = "uasb-stcr-ipns-2023-2024-001"

        crops = [
            CropMetadata(
                crop_code="maize",
                crop_name="Maize",
                crop_group="cereal",
                default_target_yield_value=50.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif", "rabi"),
            ),
            CropMetadata(
                crop_code="aerobic_rice",
                crop_name="Aerobic Rice",
                crop_group="cereal",
                default_target_yield_value=45.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif",),
            ),
            CropMetadata(
                crop_code="green_gram",
                crop_name="Green Gram",
                crop_group="pulse",
                default_target_yield_value=12.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif", "rabi"),
            ),
            CropMetadata(
                crop_code="ragi",
                crop_name="Finger Millet (Ragi)",
                crop_group="millet",
                default_target_yield_value=25.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif", "rabi"),
            ),
            CropMetadata(
                crop_code="little_millet",
                crop_name="Little Millet",
                crop_group="millet",
                default_target_yield_value=15.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif",),
            ),
            CropMetadata(
                crop_code="coriander",
                crop_name="Coriander",
                crop_group="spice",
                default_target_yield_value=8.0,
                default_target_yield_unit="q/ha",
                season_names=("rabi",),
            ),
            CropMetadata(
                crop_code="groundnut",
                crop_name="Groundnut",
                crop_group="oilseed",
                default_target_yield_value=18.0,
                default_target_yield_unit="q/ha",
                season_names=("kharif", "rabi"),
            ),
            CropMetadata(
                crop_code="sunflower",
                crop_name="Sunflower",
                crop_group="oilseed",
                default_target_yield_value=10.0,
                default_target_yield_unit="q/ha",
                season_names=("rabi",),
            ),
        ]

        def _stcr_rule(
            crop_code: str,
            nr_n: float,
            nr_p: float,
            nr_k: float,
            cs_n: float,
            cs_p: float,
            cs_k: float,
            district: str | None,
            soil_order: str = "Alfisol",
            season: str = "kharif",
        ) -> EquationRule:
            return EquationRule(
                crop_code=crop_code,
                equation_family="STCR",
                geography_scope="district" if district else "state",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
                state_name="Karnataka",
                district_name=district,
                soil_order=soil_order,
                season_name=season,
                confidence_band="A",
                nr_n=nr_n,
                nr_p=nr_p,
                nr_k=nr_k,
                cs_n=cs_n,
                cs_p=cs_p,
                cs_k=cs_k,
                cf_n=50.0,
                cf_p=50.0,
                cf_k=50.0,
                c_org_n=0.0,
                c_org_p=0.0,
                c_org_k=0.0,
                source_doc_id=stcr_karnataka_source,
                source_title="STCR Karnataka (UAS Bangalore 2022-2026)",
                citation_text=f"UAS Bangalore STCR validation trials {season} 2022-2024. {district or 'State-level'} equations for {soil_order} soils.",
            )

        def _stcr_ipns_rule(
            crop_code: str,
            nr_n: float,
            nr_p: float,
            nr_k: float,
            cs_n: float,
            cs_p: float,
            cs_k: float,
            district: str | None,
            soil_order: str = "Alfisol",
            season: str = "kharif",
        ) -> EquationRule:
            return EquationRule(
                crop_code=crop_code,
                equation_family="STCR_IPNS",
                geography_scope="district" if district else "state",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
                state_name="Karnataka",
                district_name=district,
                soil_order=soil_order,
                season_name=season,
                confidence_band="A",
                nr_n=nr_n,
                nr_p=nr_p,
                nr_k=nr_k,
                cs_n=cs_n,
                cs_p=cs_p,
                cs_k=cs_k,
                cf_n=45.0,
                cf_p=45.0,
                cf_k=45.0,
                c_org_n=20.0,
                c_org_p=15.0,
                c_org_k=15.0,
                source_doc_id=stcr_ipns_source,
                source_title="STCR-IPNS Karnataka (UAS Bangalore 2023-2024)",
                citation_text=f"UAS Bangalore STCR-IPNS integration trials with FYM {season} 2023-2024. Higher yields + superior cost-benefit.",
            )

        rules = [
            _stcr_rule("maize", 2.0, 1.0, 1.2, 48.0, 24.0, 20.0, "Shimoga", "Alfisol", "kharif"),
            _stcr_rule("maize", 2.0, 1.0, 1.2, 48.0, 24.0, 20.0, "Tumkur", "Vertisol", "kharif"),
            _stcr_ipns_rule("maize", 1.8, 0.9, 1.1, 48.0, 24.0, 20.0, "Shimoga", "Alfisol", "kharif"),
            _stcr_rule("aerobic_rice", 1.8, 0.9, 1.1, 45.0, 22.0, 18.0, "Tumkur", "Alfisol", "kharif"),
            _stcr_rule("aerobic_rice", 1.8, 0.9, 1.1, 45.0, 22.0, 18.0, "Hassan", "Vertisol", "kharif"),
            _stcr_ipns_rule("aerobic_rice", 1.6, 0.8, 1.0, 45.0, 22.0, 18.0, "Tumkur", "Alfisol", "kharif"),
            _stcr_rule("green_gram", 1.5, 0.8, 0.8, 40.0, 20.0, 16.0, "Tumkur", "Alfisol", "kharif"),
            _stcr_rule("green_gram", 1.5, 0.8, 0.8, 40.0, 20.0, 16.0, "Chikmagalur", "Alfisol", "kharif"),
            _stcr_ipns_rule("green_gram", 1.3, 0.7, 0.7, 40.0, 20.0, 16.0, "Tumkur", "Alfisol", "kharif"),
            _stcr_rule("ragi", 1.6, 0.8, 0.9, 42.0, 20.0, 16.0, "Tumkur", "Alfisol", "kharif"),
            _stcr_rule("ragi", 1.6, 0.8, 0.9, 42.0, 20.0, 16.0, "Hassan", "Vertisol", "kharif"),
            _stcr_rule("little_millet", 1.4, 0.7, 0.7, 38.0, 18.0, 14.0, "Tumkur", "Alfisol", "kharif"),
            _stcr_rule("coriander", 1.2, 0.6, 0.6, 35.0, 16.0, 12.0, "Tumkur", "Alfisol", "rabi"),
            _stcr_ipns_rule("coriander", 1.0, 0.5, 0.5, 35.0, 16.0, 12.0, "Tumkur", "Alfisol", "rabi"),
            _stcr_rule("groundnut", 1.4, 0.9, 1.0, 44.0, 22.0, 18.0, "Tumkur", "Alfisol", "kharif"),
            _stcr_rule("sunflower", 1.3, 0.8, 0.9, 40.0, 20.0, 16.0, "Tumkur", "Alfisol", "rabi"),
            _stcr_rule("maize", 2.0, 1.0, 1.2, 48.0, 24.0, 20.0, "Shimoga", "Alfisol", "rabi"),
        ]
        return cls(crops=crops, rules=rules)

    def list_crops(self) -> list[CropMetadata]:
        return list(self.crops)

    def list_rules(self, crop_code: str | None = None) -> list[EquationRule]:
        if crop_code is None:
            return list(self.rules)
        return [rule for rule in self.rules if rule.crop_code == crop_code]
