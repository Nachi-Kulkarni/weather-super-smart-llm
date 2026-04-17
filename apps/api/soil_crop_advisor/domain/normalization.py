from __future__ import annotations

from .models import SoilSample


P_TO_P2O5 = 2.291
P2O5_TO_P = 0.4364
K_TO_K2O = 1.2047
K2O_TO_K = 0.8301


def convert_nutrient_value(
    nutrient: str,
    value: float | None,
    from_basis: str,
    to_basis: str,
) -> float | None:
    if value is None or from_basis == to_basis or nutrient == "N":
        return value

    if nutrient == "P":
        if from_basis == "N-P-K" and to_basis == "N-P2O5-K2O":
            return round(value * P_TO_P2O5, 4)
        if from_basis == "N-P2O5-K2O" and to_basis == "N-P-K":
            return round(value * P2O5_TO_P, 4)

    if nutrient == "K":
        if from_basis == "N-P-K" and to_basis == "N-P2O5-K2O":
            return round(value * K_TO_K2O, 4)
        if from_basis == "N-P2O5-K2O" and to_basis == "N-P-K":
            return round(value * K2O_TO_K, 4)

    raise ValueError(f"Unsupported basis conversion: {from_basis} -> {to_basis}")


def normalize_soil_sample(sample: SoilSample, target_basis: str) -> SoilSample:
    return SoilSample(
        n_value=convert_nutrient_value("N", sample.n_value, sample.nutrient_basis, target_basis),
        p_value=convert_nutrient_value("P", sample.p_value, sample.nutrient_basis, target_basis),
        k_value=convert_nutrient_value("K", sample.k_value, sample.nutrient_basis, target_basis),
        ph_value=sample.ph_value,
        ec_value=sample.ec_value,
        oc_value=sample.oc_value,
        nutrient_basis=target_basis,
        extras=dict(sample.extras),
    )
