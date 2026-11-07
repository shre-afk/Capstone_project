"""Validate an energy summary before generating simple rule-based advice."""

from math import isfinite
from numbers import Real

from .errors import InvalidSummaryError


def build_advice(summary):
    for field in ('energy_kwh', 'cost_eur', 'co2_kg', 'after_hours_kwh'):
        value = summary.get(field)
        if (isinstance(value, bool) or not isinstance(value, Real)
                or not isfinite(value) or value < 0):
            raise InvalidSummaryError(f'{field} must be a finite, nonnegative number.')
    if summary['after_hours_kwh'] > summary['energy_kwh']:
        raise InvalidSummaryError('After-hours consumption cannot exceed total consumption.')

    if summary['after_hours_kwh'] > 0:
        message = 'Review equipment schedules and check whether after-hours operation is necessary.'
    else:
        message = 'Compare consumption with previous periods before deciding on changes.'
    return {**summary, 'advice': message}
