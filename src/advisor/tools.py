from langchain.tools import tool

from backend.analysis import api


@tool
def list_buildings() -> list[dict]:
    """List available buildings with their IDs, names, types and floor areas.

    Use this to find valid building IDs before requesting energy analytics.
    """
    return api.list_buildings()


@tool
def get_consumption(
    building_id: int,
    start: str,
    end: str,
) -> dict:
    """Get electricity imported from the grid and estimated costs.

    Use a building ID returned by list_buildings.
    Dates must use YYYY-MM-DD format.
    Start is included; end is excluded. Dates use Berlin time.
    """
    kpis = api.get_kpis(building_id, start, end)
    if kpis["completeness"] == 0:
        return {
            "status": "no_data",
            "message": "No readings exist for the requested period.",
        }
    return {
        "status": "ok",
        "building_id": building_id,
        "start": start,
        "end_exclusive": end,
        "measurement": "grid_import",
        "metrics": kpis,
        "note": (
            "Costs use an assumed tariff. "
            "If completeness is below 1, totals cover only available readings."
        ),
    }


@tool
def compare_buildings(
    building_id_a: int,
    building_id_b: int,
    start: str,
    end: str,
) -> dict:
    """Compare electricity imported by two buildings over the same period.

    Use building IDs returned by list_buildings.
    Dates use YYYY-MM-DD, Berlin time; start is included and end is excluded.
    Returns both buildings' consumption, estimated costs, completeness and
    annualized energy intensity, plus differences calculated as B minus A.
    """
    building_a = get_consumption.invoke({
        "building_id": building_id_a,
        "start": start,
        "end": end,
    })
    building_b = get_consumption.invoke({
        "building_id": building_id_b,
        "start": start,
        "end": end,
    })

    if building_a["status"] != "ok" or building_b["status"] != "ok":
        return {
            "status": "no_data",
            "building_a": building_a,
            "building_b": building_b,
            "message": "One or both buildings have no readings for this period; comparison is unavailable.",
        }

    a = building_a["metrics"]
    b = building_b["metrics"]
    return {
        "status": "ok",
        "building_a": building_a,
        "building_b": building_b,
        "difference_b_minus_a_kwh": round(b["energy_kwh"] - a["energy_kwh"], 2),
        "difference_b_minus_a_eur": round(b["cost_eur"] - a["cost_eur"], 2),
        "note": (
            "Positive differences mean building B imported more electricity or cost more. "
            "Check both completeness values: incomplete totals cannot establish a full-period ranking. "
            "Costs use an assumed flat tariff; annualized intensity uses assumed floor areas."
        ),
    }
