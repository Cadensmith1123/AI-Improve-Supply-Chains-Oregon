from typing import Optional

USEFUL_LIFE_YEARS = 8

def _to_float(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0

def _safe_div(numer, denom) -> float:
    d = _to_float(denom)
    if d <= 0:
        return 0.0
    return _to_float(numer) / d

# Depreciation
def depreciation_cost_per_mile(purchase_price, salvage_value, total_projected_mileage) -> float:
    pp = _to_float(purchase_price)
    sv = _to_float(salvage_value)
    miles = _to_float(total_projected_mileage)
    base = max(pp - sv, 0.0)
    return _safe_div(base, miles)

def trip_depreciation_cost(purchase_price, salvage_value, expected_annual_mileage, trip_miles) -> float:
    total_projected_mileage = expected_annual_mileage * USEFUL_LIFE_YEARS if expected_annual_mileage > 0 else 0.0
    dppm = depreciation_cost_per_mile(purchase_price, salvage_value, total_projected_mileage)
    return dppm * _to_float(trip_miles)

# Insurance
def insurance_cost_per_mile(annual_insurance_cost, expected_annual_mileage) -> float:

    return _safe_div(_to_float(annual_insurance_cost), _to_float(expected_annual_mileage))

def trip_insurance_cost(annual_insurance_cost, expected_annual_mileage, trip_miles) -> float:
    icpm = insurance_cost_per_mile(annual_insurance_cost, expected_annual_mileage)
    return icpm * _to_float(trip_miles)