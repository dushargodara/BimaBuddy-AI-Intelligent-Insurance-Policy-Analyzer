"""
Advanced financial calculation engine for insurance policy analysis.

Computes CAGR, IRR, cashflows, and comparative returns with accurate formulas.
"""

from dataclasses import dataclass
from typing import Optional, List
import math
import numpy as np
import numpy_financial as nf

from config import DEFAULT_INFLATION_RATE, FD_RETURN_RATE, MF_SIP_RETURN_RATE
from backend.core.logger import get_logger

logger = get_logger(__name__)

INFLATION = DEFAULT_INFLATION_RATE  # 0.06 by default


@dataclass
class FinancialResult:
    """Enhanced financial calculation result."""

    total_investment: float
    net_profit: float
    roi_percent: Optional[float]
    cagr_percent: Optional[float]
    irr_percent: Optional[float]
    inflation_adjusted_cagr: Optional[float]
    fd_comparison: Optional[float]
    mf_sip_comparison: Optional[float]
    break_even_year: Optional[float]   # now float for fractional year support
    total_premium_paid: float


def _safe_float(value) -> float:
    """Convert to float, return 0.0 for invalid."""
    if value is None:
        return 0.0
    try:
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    except (ValueError, TypeError):
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CAGR
# ─────────────────────────────────────────────────────────────────────────────
def calculate_cagr(
    investment: float,
    maturity: float,
    years: float,
) -> Optional[float]:
    """
    Compound Annual Growth Rate.

    Formula: CAGR = (maturity / investment)^(1 / years) - 1

    Works with fractional years. Returns None on invalid inputs.
    """
    try:
        inv = _safe_float(investment)
        mat = _safe_float(maturity)
        yrs = _safe_float(years)

        if inv <= 0 or mat <= 0 or yrs <= 0:
            return None

        ratio = mat / inv
        if ratio <= 0:
            return None

        cagr = (ratio ** (1.0 / yrs) - 1) * 100
        cagr = round(cagr, 2)

        # Sanity: insurance CAGR is realistically between -10% and 30%
        if not (-10 <= cagr <= 30):
            logger.warning("CAGR out of plausible range (%.2f%%), returning None", cagr)
            return None

        return cagr

    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        logger.warning("CAGR calculation failed: %s", exc)
        return None


def calculate_inflation_adjusted_cagr(
    nominal_cagr_pct: float,
    inflation_rate: float = INFLATION,
) -> Optional[float]:
    """
    Real (inflation-adjusted) CAGR using Fisher equation.

    Formula: real = (1 + nominal) / (1 + inflation) - 1
    """
    try:
        nominal = _safe_float(nominal_cagr_pct) / 100
        real = (1 + nominal) / (1 + inflation_rate) - 1
        return round(real * 100, 2)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# IRR
# ─────────────────────────────────────────────────────────────────────────────
def calculate_irr(
    premium: float,
    pay_years: int,
    policy_term: int,
    maturity: float,
    survival_benefits: Optional[List[tuple]] = None,
    gst_adjusted_first_year: Optional[float] = None,
) -> Optional[float]:
    """
    Internal Rate of Return using precise year-by-year cashflows.

    Cashflow construction:
      Year 0  : GST-adjusted first-year premium (outflow, negative)
      Years 1 … PPT-1 : regular annual premium (outflow, negative)
      Years PPT … term-2 : zero (waiting period — no premium, no payout)
      Year term-1 : maturity payout (inflow, positive)
      Survival benefits overlaid at their exact years.

    Returns:
        IRR as percentage (e.g. 5.5 for 5.5%), or None if calculation fails.
    """
    try:
        _ppt  = max(int(_safe_float(pay_years)), 1)
        _term = max(int(_safe_float(policy_term)), _ppt)
        _mat  = _safe_float(maturity)
        _prem = _safe_float(premium)

        if _prem <= 0 or _mat <= 0:
            logger.warning("IRR: invalid premium (%.2f) or maturity (%.2f)", _prem, _mat)
            return None

        # Year 0: first-year premium is ~2.2% higher due to Indian GST differential
        _y1 = (
            _safe_float(gst_adjusted_first_year)
            if gst_adjusted_first_year and gst_adjusted_first_year > _prem
            else round(_prem * 1.022, 2)
        )

        # Build cashflows
        cashflows = [-_y1] + [-_prem] * max(_ppt - 1, 0)       # premium years
        waiting   = max(_term - _ppt - 1, 0)
        cashflows += [0.0] * waiting                             # waiting years

        # Overlay survival benefits (Money-Back periodic payouts)
        if survival_benefits:
            cf_len = len(cashflows)
            for year, amount in survival_benefits:
                idx = int(year)
                if 0 <= idx < cf_len:
                    cashflows[idx] += _safe_float(amount)

        # Final inflow: maturity at end of term
        cashflows.append(_mat)

        irr_raw = nf.irr(cashflows)

        if (
            irr_raw is None
            or math.isnan(irr_raw)
            or math.isinf(irr_raw)
            or irr_raw <= -1
        ):
            logger.warning("IRR solver returned invalid value: %s", irr_raw)
            return None

        irr_pct = round(irr_raw * 100, 2)

        # Sanity check: insurance IRR realistically sits between -5% and 30%
        if not (-5 <= irr_pct <= 30):
            logger.warning(
                "IRR out of plausible range (%.2f%%), discarding result", irr_pct
            )
            return None

        return irr_pct

    except Exception as exc:
        logger.warning("IRR calculation failed: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Annualized ROI  (After-Tax Compound Annual Return)
# ─────────────────────────────────────────────────────────────────────────────
def calculate_annualized_roi(
    total_investment: float,
    maturity: float,
    avg_holding_years: float,
    tax_saved: float = 0.0,
) -> Optional[float]:
    """
    After-tax compound annual return.

    Definition
    ----------
    Uses Section 80C savings to reduce the effective investment base, then
    compounds to maturity over the money-weighted holding period.

    Formula: (maturity / effective_investment)^(1 / avg_time) - 1

    Why "effective investment"?
    ---------------------------
    Every rupee deducted under Section 80C reduces your real cash outflow.
    A policy with ₹1.5 L annual premium and 30% tax bracket actually costs
    ₹1.05 L per year in after-tax terms, making genuine returns higher than
    a naive CAGR would suggest.

    Args
    ----
    total_investment  : Gross premium paid over PPT (₹)
    maturity          : Maturity / death benefit received (₹)
    avg_holding_years : Money-weighted average holding period (years)
                        = policy_term − (PPT − 1) / 2
    tax_saved         : Cumulative Section 80C tax benefit (₹)
                        = min(annual_premium, 1_50_000) × tax_rate × PPT

    Returns
    -------
    After-tax annualized ROI as percentage (e.g. 8.42), or None on failure.
    """
    try:
        inv = _safe_float(total_investment)
        mat = _safe_float(maturity)
        yrs = _safe_float(avg_holding_years)
        tax = _safe_float(tax_saved)

        if inv <= 0 or mat <= 0 or yrs <= 0:
            return None

        # Effective economic outlay after 80C benefit
        effective_inv = max(inv - tax, 1.0)   # floor at ₹1 to avoid /0

        # Compound annual growth on the after-tax base
        roi = (mat / effective_inv) ** (1.0 / yrs) - 1
        roi_pct = round(roi * 100, 2)

        # Sanity bounds: after-tax base is lower so ceiling is a bit higher
        if not (-10 <= roi_pct <= 60):
            logger.warning(
                "After-tax Annualized ROI out of plausible range: %.2f%%", roi_pct
            )
            return None

        return roi_pct

    except Exception as exc:
        logger.warning("Annualized ROI calculation failed: %s", exc)
        return None


def calculate_tax_effective_irr(
    annual_premium: float,
    pay_years: int,
    policy_term: int,
    maturity: float,
    tax_rate: float = 0.312,           # 30% slab + 4% cess (default top bracket)
    sec80c_limit: float = 150_000.0,
    gst_adjusted_first_year: Optional[float] = None,
) -> Optional[float]:
    """
    Tax-Effective IRR — the most accurate "after-tax" return metric.

    Method
    ------
    Builds year-by-year cashflows identical to `calculate_irr`, but each
    premium outflow is *reduced* by the annual Section 80C tax shield:

        tax_shield_per_year = min(annual_premium, sec80c_limit) × tax_rate

    Construction
    ------------
    Year 0  : GST-inflated first-year premium − tax_shield
    Years 1…PPT−1: regular premium − tax_shield
    Years PPT…term−2: 0 (no premium, no payout)
    Year term−1: maturity inflow (+)

    Prefers IRR when available; falls back to None so callers can fall back
    to `calculate_annualized_roi`.

    Args
    ----
    annual_premium           : Annualised premium (₹)
    pay_years                : Premium Paying Term (years)
    policy_term              : Total policy term (years)
    maturity                 : Maturity / death benefit (₹)
    tax_rate                 : Marginal tax rate incl. cess (default 31.2%)
    sec80c_limit             : Annual 80C deduction cap (default ₹1,50,000)
    gst_adjusted_first_year  : First-year premium with GST already loaded (₹)

    Returns
    -------
    Tax-effective IRR as percentage (e.g. 9.1), or None on failure.
    """
    try:
        _ppt  = max(int(_safe_float(pay_years)), 1)
        _term = max(int(_safe_float(policy_term)), _ppt)
        _mat  = _safe_float(maturity)
        _prem = _safe_float(annual_premium)

        if _prem <= 0 or _mat <= 0:
            return None

        # Annual tax shield from 80C deduction
        annual_deductible  = min(_prem, sec80c_limit)
        annual_tax_shield  = annual_deductible * tax_rate

        # Year-0 premium (GST-adjusted); default to 2.2% uplift
        _y1 = (
            _safe_float(gst_adjusted_first_year)
            if gst_adjusted_first_year and gst_adjusted_first_year > _prem
            else round(_prem * 1.022, 2)
        )

        # Net after-tax cash outflows
        y0_net  = _y1   - annual_tax_shield    # year-0 (higher GST premium)
        yn_net  = _prem - annual_tax_shield     # years 1…PPT−1

        # Build cashflow array
        cashflows  = [-y0_net] + [-yn_net] * max(_ppt - 1, 0)
        waiting    = max(_term - _ppt - 1, 0)
        cashflows += [0.0] * waiting
        cashflows.append(_mat)                 # maturity inflow

        irr_raw = nf.irr(cashflows)

        if (
            irr_raw is None
            or math.isnan(irr_raw)
            or math.isinf(irr_raw)
            or irr_raw <= -1
        ):
            logger.warning("Tax-effective IRR solver returned invalid value: %s", irr_raw)
            return None

        irr_pct = round(irr_raw * 100, 2)

        # After-tax base makes effective returns higher; allow up to 40%
        if not (-5 <= irr_pct <= 40):
            logger.warning(
                "Tax-effective IRR out of plausible range (%.2f%%), discarding",
                irr_pct,
            )
            return None

        return irr_pct

    except Exception as exc:
        logger.warning("Tax-effective IRR calculation failed: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Break-Even Year
# ─────────────────────────────────────────────────────────────────────────────
def calculate_break_even_year(
    annual_premium: float,
    pay_years: int,
    policy_term: int,
    maturity: float,
    cagr_pct: Optional[float] = None,
) -> Optional[float]:
    """
    Break-Even Year: the first year at which the policy's accumulated value
    equals or exceeds total cumulative premiums paid.

    Method (iterative, no approximation):
      Each year t:
        - Accumulated value = total_investment_so_far × (1 + cagr)^t
        - Break-even when accumulated_value >= total_investment_to_date

    If CAGR is unavailable, we distribute maturity linearly across the term
    to detect the crossover year.

    Returns a fractional year interpolated between integer years.
    Returns policy_term if break-even never occurs within the term.
    """
    try:
        _prem = _safe_float(annual_premium)
        _ppt  = max(int(_safe_float(pay_years)), 1)
        _term = max(int(_safe_float(policy_term)), _ppt)
        _mat  = _safe_float(maturity)

        if _prem <= 0 or _mat <= 0:
            return None

        total_investment = _prem * _ppt

        # If maturity <= total investment, policy never truly breaks even
        if _mat <= total_investment:
            return float(_term)

        # ── If CAGR is valid, use analytical formula with interpolation ─────────
        if cagr_pct is not None and cagr_pct > 0:
            r = cagr_pct / 100.0

            prev_val = 0.0
            for yr in range(1, _term + 1):
                cumulative_inv = _prem * min(yr, _ppt)   # premiums stop at PPT
                # Value of the fund grows at CAGR from the start
                val = total_investment * ((1 + r) ** yr)

                if val >= cumulative_inv and yr >= _ppt:
                    # We crossed break-even between yr-1 and yr — interpolate
                    if prev_val > 0 and val != prev_val:
                        prev_inv = _prem * min(yr - 1, _ppt)
                        # Linear interpolation fraction
                        frac = (prev_inv - prev_val) / ((val - prev_val) - (cumulative_inv - prev_inv))
                        frac = max(0.0, min(1.0, frac))
                        return round((yr - 1) + frac, 1)
                    return float(yr)

                prev_val = val

            return float(_term)

        # ── Fallback: linear growth model ────────────────────────────────────────
        # Distribute maturity gain linearly over term years
        if _term > 0:
            gain_per_year = (_mat - total_investment) / _term
            if gain_per_year > 0:
                years_needed = math.ceil((_mat - total_investment) / gain_per_year)
                return float(min(years_needed, _term))

        return float(_term)

    except Exception as exc:
        logger.warning("Break-even year calculation failed: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Net Profit
# ─────────────────────────────────────────────────────────────────────────────
def calculate_net_profit(maturity_value: float, total_premium: float) -> float:
    """Net cash profit = maturity − total premiums paid."""
    return _safe_float(maturity_value) - _safe_float(total_premium)


def calculate_inflation_adjusted_profit(
    maturity_value: float,
    total_investment: float,
    years: float,
    inflation: float = INFLATION,
) -> float:
    """
    Net profit in today's purchasing power.

    real_maturity = maturity / (1 + inflation)^years
    result = real_maturity - total_investment
    """
    try:
        mat  = _safe_float(maturity_value)
        inv  = _safe_float(total_investment)
        yrs  = _safe_float(years)
        real = mat / ((1 + inflation) ** yrs) if yrs > 0 else mat
        return round(real - inv, 2)
    except Exception:
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Total Premium
# ─────────────────────────────────────────────────────────────────────────────
def calculate_total_premium(yearly_premium: float, premium_payment_term: int) -> float:
    """Total premium paid over the payment term."""
    return _safe_float(yearly_premium) * max(int(_safe_float(premium_payment_term)), 0)


# ─────────────────────────────────────────────────────────────────────────────
# Comparison (FD / MF SIP)
# ─────────────────────────────────────────────────────────────────────────────
def calculate_comparisons(
    total_investment: float,
    policy_term: int,
) -> tuple:
    """
    Lump-sum FD and MF SIP projections for the same investment.

    Returns:
        (fd_maturity, mf_sip_maturity)
    """
    inv  = _safe_float(total_investment)
    yrs  = max(int(_safe_float(policy_term)), 1)
    fd   = round(inv * ((1 + FD_RETURN_RATE)  ** yrs), 2)
    mf   = round(inv * ((1 + MF_SIP_RETURN_RATE) ** yrs), 2)
    return fd, mf


# ─────────────────────────────────────────────────────────────────────────────
# Money-Back Survival Benefits
# ─────────────────────────────────────────────────────────────────────────────
def calculate_money_back_benefits(
    sum_assured: float,
    policy_term: int,
) -> List[tuple]:
    """
    Typical Money-Back staggered payouts:
      20% at ¼ term, 20% at ½ term, 20% at ¾ term, 40% at maturity.
    """
    benefits = []
    sa = _safe_float(sum_assured)
    if sa > 0 and policy_term >= 5:
        q = policy_term // 4
        if q > 0:
            benefits.append((q,     sa * 0.20))
            benefits.append((q * 2, sa * 0.20))
            benefits.append((q * 3, sa * 0.20))
    return benefits


# ─────────────────────────────────────────────────────────────────────────────
# ULIP Returns
# ─────────────────────────────────────────────────────────────────────────────
def calculate_ulip_returns(
    premium: float,
    years: int,
    market_return: float = 0.12,
) -> float:
    """Future Value for a single premium ULIP (simplified)."""
    try:
        return _safe_float(premium) * ((1 + market_return) ** max(int(years), 1))
    except Exception:
        return _safe_float(premium) * max(int(years), 1)


# ─────────────────────────────────────────────────────────────────────────────
# compute_financials (convenience wrapper used by api.py)
# ─────────────────────────────────────────────────────────────────────────────
def compute_financials(premium, ppt, policy_term, maturity):
    """
    Compute all financial metrics from raw inputs.

    Returns a dict with keys:
        total_investment, net_profit, roi, cagr, irr, break_even_year,
        inflation_adjusted_cagr, fd_projection, mf_projection
    """
    logger.debug(
        "compute_financials called: premium=%s ppt=%s term=%s maturity=%s",
        premium, ppt, policy_term, maturity,
    )

    if not premium or not ppt:
        return {"error": "Missing premium or payment term"}

    _prem = _safe_float(premium)
    _ppt  = max(int(_safe_float(ppt)), 1)
    _term = max(int(_safe_float(policy_term or _ppt)), _ppt)
    _mat  = _safe_float(maturity) if maturity else 0.0

    # First-year premium with GST uplift (~2.2%)
    first_year_premium = round(_prem * 1.022, 2)
    total_investment   = first_year_premium + _prem * max(_ppt - 1, 0)

    # Money-weighted average holding period
    avg_time = max(_term - (_ppt - 1) / 2.0, 1.0)

    # ── Metrics ───────────────────────────────────────────────────────────────
    cagr = calculate_cagr(total_investment, _mat, avg_time) if _mat > 0 else None
    inflation_adjusted_cagr = calculate_inflation_adjusted_cagr(cagr) if cagr is not None else None

    roi = calculate_annualized_roi(total_investment, _mat, avg_time) if _mat > 0 else None

    irr = calculate_irr(
        premium     = _prem,
        pay_years   = _ppt,
        policy_term = _term,
        maturity    = _mat,
        gst_adjusted_first_year = first_year_premium,
    ) if _mat > 0 else None

    # Prefer IRR as the ROI figure when it converges sensibly
    effective_roi = irr if irr is not None else roi

    break_even_year = calculate_break_even_year(
        annual_premium  = _prem,
        pay_years       = _ppt,
        policy_term     = _term,
        maturity        = _mat,
        cagr_pct        = cagr,
    ) if _mat > 0 else None

    net_profit = calculate_net_profit(_mat, total_investment)
    inflation_adj_profit = calculate_inflation_adjusted_profit(_mat, total_investment, _term)

    fd_proj, mf_proj = calculate_comparisons(total_investment, _term)

    return {
        "total_investment"         : round(total_investment, 2),
        "net_profit"               : round(net_profit, 2),
        "roi"                      : effective_roi,
        "roi_percent"              : effective_roi,
        "cagr"                     : cagr,
        "cagr_percent"             : cagr,
        "irr"                      : irr,
        "irr_percent"              : irr,
        "break_even_year"          : break_even_year,
        "inflation_adjusted_cagr"  : inflation_adjusted_cagr,
        "inflation_adj_net_profit" : round(inflation_adj_profit, 2),
        "fd_projection"            : fd_proj,
        "mf_projection"            : mf_proj,
    }
