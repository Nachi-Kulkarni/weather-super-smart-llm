from __future__ import annotations

from dataclasses import dataclass

from .models import EquationRule, Location


@dataclass(frozen=True)
class RuleSelection:
    selected_rule: EquationRule | None
    rejected_rules: list[EquationRule]
    warnings: list[str]


_FAMILY_PRIORITY = {
    "STCR": 0,
    "STCR_IPNS": 0,
    "TEST_SYNTHETIC": 0,
    "POP_FALLBACK": 1,
}

_GEOGRAPHY_PRIORITY = {
    "district": 0,
    "state": 1,
    "agro_region": 2,
    "national": 3,
}


def _season_matches(rule: EquationRule, season_name: str) -> bool:
    return rule.season_name in (None, "", season_name)


def _geography_matches(rule: EquationRule, location: Location) -> bool:
    if rule.geography_scope == "district":
        return (
            rule.state_name == location.state
            and rule.district_name == location.district
        )
    if rule.geography_scope == "state":
        return rule.state_name == location.state
    if rule.geography_scope == "agro_region":
        return rule.agro_region_code == location.agro_region_code
    return True


def _sort_key(rule: EquationRule) -> tuple[int, int]:
    return (
        _FAMILY_PRIORITY.get(rule.equation_family, 99),
        _GEOGRAPHY_PRIORITY.get(rule.geography_scope, 99),
    )


def select_best_rule(
    crop_code: str,
    location: Location,
    season_name: str,
    rules: list[EquationRule],
) -> RuleSelection:
    candidate_rules = [rule for rule in rules if rule.crop_code == crop_code and _season_matches(rule, season_name)]
    matched_rules = [rule for rule in candidate_rules if _geography_matches(rule, location)]
    warnings: list[str] = []

    if not matched_rules:
        if candidate_rules:
            warnings.append("No geography-matched rule found for the requested location.")
        else:
            warnings.append("No rule found for the requested crop and season.")
        return RuleSelection(selected_rule=None, rejected_rules=candidate_rules, warnings=warnings)

    selected_rule = sorted(matched_rules, key=_sort_key)[0]
    rejected_rules = [rule for rule in matched_rules if rule != selected_rule]

    if selected_rule.geography_scope != "district":
        warnings.append(f"Using {selected_rule.geography_scope}-scope rule instead of district scope.")
    if selected_rule.equation_family == "POP_FALLBACK":
        warnings.append("Using package-of-practice fallback instead of a verified STCR equation.")

    return RuleSelection(
        selected_rule=selected_rule,
        rejected_rules=rejected_rules,
        warnings=warnings,
    )
