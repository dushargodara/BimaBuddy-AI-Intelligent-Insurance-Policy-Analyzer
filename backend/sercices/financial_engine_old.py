"""
Financial calculation engine for insurance policy analysis.

Computes ROI, CAGR, net profit, and comparative returns with validation.
"""

from dataclasses import dataclass
from typing import Optional

from config import DEFAULT_INFLATION_RATE, FD_RETURN_RATE, MF_SIP_RETURN_RATE
from backend.core.logger import get_logger

logger = get_logger(__name__)

# Frequency: payments per year
FREQUENCY_MAP = {
    "yearly": 1,
    "half_yearly": 2,
    "quarterly": 4,
    "monthly": 12,
}


@dataclass
class FinancialResult:
    """Structured financial calculation result."""

    total_investment: float
    net_profit: float
    roi_percent: float
    cagr_percent: Optional[float]
    inflation_adjusted_cagr: Optional[float]
    fd_comparison: Optional[float]
    mf_sip_comparison: Optional[float]


def _safe_float(value: float | int | None) -> float:
    """Convert to float, return 0.0 for invalid."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def calculate_total_investment(
    premium: float, tenure_years: int, frequency: str = "yearly"
) -> float:
    """
    Calculate total investment (premium × number of payments).

    Formula: Total = Premium × (Tenure_years × Payments_per_year)

    Args:
        premium: Premium amount per payment.
        tenure_years: Policy tenure in years.
        frequency: "yearly", "half_yearly", "quarterly", "monthly".

    Returns:
        Total amount invested over tenure.
    """
    premium = _safe_float(premium)
    tenure_years = max(0, int(tenure_years))
    payments_per_year = FREQUENCY_MAP.get(str(frequency).lower(), 1)
    total_payments = tenure_years * payments_per_year
    result = premium * total_payments
    return round(result, 2)


def calculate_net_profit(maturity_value: float, total_investment: float) -> float:
    """
    Calculate net profit (maturity - total investment).

    Args:
        maturity_value: Maturity amount.
        total_investment: Total amount invested.

    Returns:
        Net profit amount.
    """
    return round(_safe_float(maturity_value) - _safe_float(total_investment), 2)


def calculate_cagr(
    maturity_value: float, total_investment: float, tenure_years: float
) -> Optional[float]:
    """
    Calculate Compound Annual Growth Rate (CAGR).

    CAGR = (End Value / Start Value)^(1/Years) - 1

    Note: For SIP-style investments, this is an approximation since
    money is invested over time rather than as a single lump sum.

    Args:
        maturity_value: End value (maturity amount).
        total_investment: Total amount invested (used as proxy for start value).
        tenure_years: Number of years.

    Returns:
        CAGR as decimal (e.g., 0.08 for 8%), or None if invalid.
    """
    mv = _safe_float(maturity_value)
    ti = _safe_float(total_investment)
    years = _safe_float(tenure_years)

    if years <= 0 or ti <= 0 or mv <= 0:
        return None

    try:
        cagr = (mv / ti) ** (1 / years) - 1
        if not (-1 <= cagr <= 10):  # Sanity: -100% to 1000% max
            logger.warning("CAGR out of expected range: %s", cagr)
        return round(float(cagr), 6)
    except (ValueError, ZeroDivisionError) as e:
        logger.debug("CAGR calculation failed: %s", e)
        return None


def inflation_adjusted_return(
    cagr: float, inflation_rate: float = DEFAULT_INFLATION_RATE
) -> float:
    """
    Calculate inflation-adjusted (real) return.

    Real Return = (1 + CAGR) / (1 + inflation) - 1

    Args:
        cagr: Nominal CAGR as decimal.
        inflation_rate: Inflation rate as decimal (default 6%).

    Returns:
        Real return as decimal.
    """
    cagr = _safe_float(cagr)
    inf = _safe_float(inflation_rate)
    if inf <= -1:
        return cagr
    real = (1 + cagr) / (1 + inf) - 1
    return round(float(real), 6)


def calculate_fd_comparison(
    total_investment: float, tenure_years: float, rate: float = FD_RETURN_RATE
) -> float:
    """
    Simulate lump-sum Fixed Deposit returns for comparison.

    FV = PV × (1 + r)^n

    Note: Policy invests via regular premiums (SIP). This assumes
    equivalent lump sum at start for apples-to-apples comparison.

    Args:
        total_investment: Lump sum (total premiums) invested.
        tenure_years: Tenure in years.
        rate: Annual FD rate as decimal.

    Returns:
        FD maturity amount.
    """
    ti = _safe_float(total_investment)
    years = max(0.0, _safe_float(tenure_years))
    r = _safe_float(rate)
    if years <= 0 or ti <= 0:
        return 0.0
    result = ti * ((1 + r) ** years)
    return round(result, 2)


def calculate_mf_sip_projection(
    premium: float,
    tenure_years: int,
    frequency: str = "yearly",
    rate: float = MF_SIP_RETURN_RATE,
) -> float:
    """
    Simulate Mutual Fund SIP future value.

    FV = P × [((1 + r)^n - 1) / r] × (1 + r)

    Assumes payments at start of each period (advance SIP).

    Args:
        premium: SIP amount per installment.
        tenure_years: Tenure in years.
        frequency: "yearly", "half_yearly", "quarterly", "monthly".
        rate: Expected annual return as decimal.

    Returns:
        Projected SIP maturity amount.
    """
    p = _safe_float(premium)
    years = max(0, int(tenure_years))
    r_annual = _safe_float(rate)
    n_per_year = FREQUENCY_MAP.get(str(frequency).lower(), 1)

    if years <= 0 or p <= 0:
        return 0.0

    n = years * n_per_year
    r_period = r_annual / n_per_year

    if abs(r_period) < 1e-9:
        return round(p * n, 2)

    # FV of annuity due: P * [((1+r)^n - 1) / r] * (1+r)
    fv = p * (((1 + r_period) ** n - 1) / r_period) * (1 + r_period)
    return round(float(fv), 2)


def compute_financial_summary(
    premium: float,
    tenure_years: int,
    maturity_value: float,
    frequency: str = "yearly",
    is_term_insurance: bool = False,
) -> FinancialResult:
    """
    Compute complete financial summary for a policy.

    Args:
        premium: Premium amount.
        tenure_years: Tenure in years.
        maturity_value: Maturity amount (0 for term).
        frequency: Premium frequency.
        is_term_insurance: If True, maturity is 0 (pure protection).

    Returns:
        FinancialResult with all calculations.
    """
    premium = _safe_float(premium)
    tenure_years = max(0, int(tenure_years))
    maturity_value = _safe_float(maturity_value)
    freq = str(frequency).lower() or "yearly"

    total_inv = calculate_total_investment(premium, tenure_years, freq)

    if is_term_insurance or maturity_value <= 0:
        fd_val = calculate_fd_comparison(total_inv, tenure_years)
        mf_val = calculate_mf_sip_projection(premium, tenure_years, freq)
        return FinancialResult(
            total_investment=total_inv,
            net_profit=0.0,
            roi_percent=0.0,
            cagr_percent=None,
            inflation_adjusted_cagr=None,
            fd_comparison=round(fd_val, 2),
            mf_sip_comparison=round(mf_val, 2),
        )

    net_profit = calculate_net_profit(maturity_value, total_inv)
    roi = (net_profit / total_inv * 100) if total_inv > 0 else 0.0
    cagr = calculate_cagr(maturity_value, total_inv, float(tenure_years))
    real_cagr = inflation_adjusted_return(cagr) if cagr is not None else None
    fd_val = calculate_fd_comparison(total_inv, tenure_years)
    mf_val = calculate_mf_sip_projection(premium, tenure_years, freq)

    return FinancialResult(
        total_investment=total_inv,
        net_profit=net_profit,
        roi_percent=round(roi, 2),
        cagr_percent=round(cagr * 100, 2) if cagr is not None else None,
        inflation_adjusted_cagr=round(real_cagr * 100, 2) if real_cagr is not None else None,
        fd_comparison=round(fd_val, 2),
        mf_sip_comparison=round(mf_val, 2),
    )
