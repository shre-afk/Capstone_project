import math
from datetime import timedelta
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend import settings
from backend.analysis import api
from ui.dashboard.components import TYPE_LABELS
from ui.dashboard.attribution import render_attribution_footer
from ui.dashboard.errors import DashboardErrorHandler, DashboardOperationError


def dashboard_call(operation, callback, *args, **kwargs):
    """Show service errors in the dashboard and return None if an operation fails."""
    try:
        return DashboardErrorHandler.execute(
            operation, callback, *args, **kwargs
        )
    except DashboardOperationError as error:
        st.warning(str(error))
        return None

def read_number(data, key):
    """Validate a numeric value returned by the analysis API."""
    if not isinstance(data, dict) or key not in data:
        raise ValueError(f"Response is missing key {key}")

    value = float(data[key])
    if not math.isfinite(value):
        raise ValueError(f"Response contains an invalid {key}")

    return value


def create_pdf_report(
    report,
    period_label,
    period_text,
    total_energy,
    total_cost,
    co2_metric_label,
    co2_metric_value,
):
    """Create a landscape PDF with report totals and the building breakdown."""
    buffer = BytesIO()
    page_width, _ = landscape(A4)
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Energy report",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            textColor=colors.HexColor("#737B95"),
            fontSize=9,
            leading=13,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportTableHeader",
            parent=styles["Normal"],
            textColor=colors.white,
            fontSize=7.5,
            leading=9,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportTableCell",
            parent=styles["Normal"],
            textColor=colors.HexColor("#1A214F"),
            fontSize=7.5,
            leading=9,
            wordWrap="CJK",
        )
    )

    content_width = page_width - document.leftMargin - document.rightMargin
    story = [
        Paragraph("Energy Consumption Report", styles["Title"]),
        Paragraph(
            f"{escape(period_label)} · {escape(period_text)}".replace("₂", "2"),
            styles["ReportSubtitle"],
        ),
        Spacer(1, 7 * mm),
    ]

    summary = Table(
        [
            [
                Paragraph(
                    f"<b>Total consumption</b><br/>{total_energy:,.1f} kWh",
                    styles["Normal"],
                ),
                Paragraph(
                    f"<b>Total cost</b><br/>€{total_cost:,.2f}",
                    styles["Normal"],
                ),
                Paragraph(
                    f"<b>{escape(co2_metric_label).replace('₂', '2')}</b><br/>"
                    f"{escape(co2_metric_value)}",
                    styles["Normal"],
                ),
            ]
        ],
        colWidths=[content_width / 3] * 3,
    )
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F1E8")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5D9C8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5D9C8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.extend([summary, Spacer(1, 7 * mm)])

    headers = [
        "Building",
        "Type",
        "Consumption<br/>(kWh)",
        "Cost<br/>(EUR)",
        "CO2 emissions<br/>(kg)",
        "Energy saved<br/>(kWh)",
        "CO2 saved<br/>(kg)",
        "Data coverage<br/>(%)",
    ]
    columns = [
        "Building",
        "Building Type",
        "Consumption (kWh)",
        "Cost (EUR)",
        "CO₂ Emissions (kg)",
        "Energy Saved vs Previous (kWh)",
        "CO₂ Saved vs Previous (kg)",
        "Data Coverage (%)",
    ]
    rows = [[Paragraph(value, styles["ReportTableHeader"]) for value in headers]]
    for _, row in report.iterrows():
        rows.append(
            [
                Paragraph(escape(str(row[column])), styles["ReportTableCell"])
                if column in ("Building", "Building Type")
                else Paragraph(
                    "—" if pd.isna(row[column]) else f"{row[column]:,.1f}",
                    styles["ReportTableCell"],
                )
                for column in columns
            ]
        )

    column_widths = [92, 67, 83, 63, 83, 112, 105, 75]
    scale = content_width / sum(column_widths)
    table = Table(
        rows,
        colWidths=[width * scale for width in column_widths],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B63")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F7F1E8"),
                ]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7CBB9")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(Paragraph("Building breakdown", styles["Heading2"]))
    story.append(Spacer(1, 2 * mm))
    story.append(table)

    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#737B95"))
        canvas.drawRightString(
            page_width - document.rightMargin,
            8 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    document.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return buffer.getvalue()


title_col, period_col = st.columns(
    [3, 1.2],
    vertical_alignment="center",
)

with title_col:
    st.title("Reports", anchor=False)
    st.caption("Download and explore detailed reports")

with period_col:
    period_label = st.selectbox(
        "Reporting period",
        ["Last 30 Days", "Last 6 Months", "Last 12 Months", "Custom Range"],
        index=2,
        key="reports_period",
        label_visibility="collapsed",
        format_func=lambda period: (
            "Custom range" if period == "Custom Range"
            else period.replace("Last ", "")
        ),
    )

period_lengths = {
    "Last 30 Days": pd.Timedelta(days=30),
    "Last 6 Months": pd.DateOffset(months=6),
    "Last 12 Months": pd.DateOffset(months=12),
}

buildings = dashboard_call("loading buildings", api.list_buildings)
if buildings is None:
    st.stop()

if not isinstance(buildings, list) or not buildings:
    st.info("No buildings are available for reporting.")
    st.stop()


buildings_with_readings = []
latest_times = []
for building in buildings:
    if not isinstance(building, dict) or not {
        "id", "name", "type"
    }.issubset(building):
        st.warning("Skipped a building with incomplete identifying information.")
        continue

    latest = dashboard_call(
        f"loading the latest reading for {building['name']}",
        api.get_latest,
        building["id"],
    )

    if not isinstance(latest, dict) or latest.get("last_reading") is None:
        continue

    timestamp = dashboard_call(
        f"reading the latest reading for {building['name']}",
        pd.to_datetime,
        latest["last_reading"],
        utc=True,
        errors="raise",
    )
    if isinstance(timestamp, pd.Timestamp) and not pd.isna(timestamp):
        latest_times.append(timestamp.tz_convert(settings.LOCAL_TZ))
        buildings_with_readings.append(building)

if not latest_times:
    st.info("No meter readings are available yet, so a report cannot be generated.")
    st.stop()

if len(buildings_with_readings) < len(buildings):
    st.info("Buildings without readings are excluded from this report.")

if period_label == "Custom Range":
    available_through = max(latest_times).date()
    default_end = available_through
    default_start = default_end - timedelta(days=29)
    with st.container(border=True, key="reports_custom_date_range"):
        start_col, end_col = st.columns(2, gap="medium")
        with start_col:
            custom_start = st.date_input(
                "Start date",
                value=default_start,
                max_value=available_through,
                key="reports_custom_start",
            )
        with end_col:
            custom_end = st.date_input(
                "End date",
                value=default_end,
                max_value=available_through,
                key="reports_custom_end",
            )

    if custom_start > custom_end:
        st.warning("Start date must be on or before the end date.")
        st.stop()

    period_start = pd.Timestamp(custom_start).tz_localize(settings.LOCAL_TZ)
    period_end = pd.Timestamp(custom_end + timedelta(days=1)).tz_localize(
        settings.LOCAL_TZ
    )
    period_text = f"{custom_start:%d %b %Y} – {custom_end:%d %b %Y}"
else:
    period_end = max(latest_times) + pd.Timedelta(minutes=15)
    period_start = period_end - period_lengths[period_label]
    period_text = (
        f"{period_start.strftime('%d %b %Y')} – "
        f"{period_end.strftime('%d %b %Y')}"
    )

rows = []
for building in buildings_with_readings:
    kpis = dashboard_call(
        f"loading report metrics for {building['name']}",
        api.get_kpis,
        building["id"],
        period_start,
        period_end,
    )
    if kpis is None:
        continue

    energy = dashboard_call(
        f"checking energy use for {building['name']}",
        read_number,
        kpis,
        "energy_kwh",
    )

    cost = dashboard_call(
        f"checking energy cost for {building['name']}",
        read_number,
        kpis,
        "cost_eur",
    )

    emissions = dashboard_call(
        f"checking emissions for {building['name']}",
        read_number,
        kpis,
        "co2_kg",
    )
    completeness = dashboard_call(
        f"checking data coverage for {building['name']}",
        read_number,
        kpis,
        "completeness",
    )

    if None in (energy, cost, emissions, completeness):
        continue
    if completeness <= 0:
        st.info(f"No readings for {building['name']} in the selected period.")
        continue

    savings = dashboard_call(
        f"comparing energy use for {building['name']}",
        api.get_savings,
        building["id"],
        period_start,
        period_end,
    )

    saved_kwh = None
    saved_co2_kg = None

    if isinstance(savings, dict):
        if "saved_kwh" in savings:
            saved_kwh = dashboard_call(
                f"checking the energy comparison for {building['name']}",
                read_number,
                savings,
                "saved_kwh",
            )
        if "saved_co2_kg" in savings:
            saved_co2_kg = dashboard_call(
                f"checking CO₂ savings for {building['name']}",
                read_number,
                savings,
                "saved_co2_kg",
            )

    rows.append(
        {
            "Building": building["name"],
            "Building Type": TYPE_LABELS.get(
                building["type"], str(building["type"]).title()
            ),
            "Consumption (kWh)": energy,
            "Cost (EUR)": cost,
            "CO₂ Emissions (kg)": emissions,
            "Energy Saved vs Previous (kWh)": saved_kwh,
            "CO₂ Saved vs Previous (kg)": saved_co2_kg,
            "Data Coverage (%)": completeness * 100,
        }
    )


if not rows:
    st.warning("Report metrics could not be loaded for any buildings.")
    st.stop()

report = pd.DataFrame(rows).sort_values(
    "Consumption (kWh)", ascending=False
)
if len(rows) < len(buildings_with_readings):
    st.warning(
        "This is a partial report; metrics could not be loaded for every "
        "building with readings."
    )

total_energy = float(report["Consumption (kWh)"].sum())
total_cost = float(report["Cost (EUR)"].sum())
total_emissions = float(report["CO₂ Emissions (kg)"].sum())

co2_saved_values = report["CO₂ Saved vs Previous (kg)"].dropna()
co2_saved_kg = (
    float(co2_saved_values.sum()) if not co2_saved_values.empty else None
)

if co2_saved_kg is None:
    co2_metric_label = "CO₂ Change"
    co2_metric_value = "Unavailable"
elif co2_saved_kg > 0:
    co2_metric_label = "CO₂ Saved"
    co2_metric_value = f"{co2_saved_kg / 1000:,.1f} t"
elif co2_saved_kg < 0:
    co2_metric_label = "CO₂ Increase"
    co2_metric_value = f"{abs(co2_saved_kg) / 1000:,.1f} t"
else:
    co2_metric_label = "CO₂ Change"
    co2_metric_value = "0.0 t"

overview_col, formats_col = st.columns(
    [1.65, 1],
    gap="medium",
    vertical_alignment="top",
)
with overview_col:
    with st.container(border=True, key="reports_overview"):
        st.subheader("Report Overview")
        st.caption(f"{period_label} · {period_text}")

        metric_cols = st.columns(3, gap="small")

        with metric_cols[0]:
            with st.container(border=True, key="reports_consumption"):
                st.metric(
                    "Consumption",
                    f"{total_energy / 1000:,.1f} MWh",
                )

        with metric_cols[1]:
            with st.container(border=True, key="reports_cost"):
                cost_value = (
                    f"€{total_cost / 1000:,.1f}k"
                    if total_cost >= 1000
                    else f"€{total_cost:,.0f}"
                )
                st.metric(
                    "Cost",
                    cost_value,
                )

        with metric_cols[2]:
            with st.container(border=True, key="reports_co2_saved"):
                st.metric(
                    co2_metric_label,
                    co2_metric_value,
                )

        st.markdown("**Included in this report**")
        st.markdown(
            """
            <ul class="report-included-list">
                <li><span aria-hidden="true">✓</span>Consumption and cost breakdown</li>
                <li><span aria-hidden="true">✓</span>Building-wise energy and emissions</li>
                <li><span aria-hidden="true">✓</span>Savings and performance comparison</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )


with formats_col:
    with st.container(border=True, key="reports_formats"):
        with st.container(key="reports_formats_intro"):
            st.subheader("Available Formats")
            st.caption(f"Reports for {period_label.lower()}.")

        with st.container(key="reports_pdf_format"):
            pdf_data = create_pdf_report(
                report,
                period_label,
                period_text,
                total_energy,
                total_cost,
                co2_metric_label,
                co2_metric_value,
            )
            st.download_button(
                "📕 Download PDF",
                data=pdf_data,
                file_name=(
                    f"energy_report_{period_label.lower().replace(' ', '_')}.pdf"
                ),
                mime="application/pdf",
                key="reports_download_pdf",
                width="stretch",
            )
            st.caption("Summary, metrics, and building data.")

        with st.container(key="reports_csv_format"):
            csv_data = report.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📄 Download CSV",
                data=csv_data,
                file_name=(
                    f"energy_report_{period_label.lower().replace(' ', '_')}.csv"
                ),
                mime="text/csv",
                key="reports_download_csv",
                width="stretch",
            )

            st.caption("Full building breakdown.")

render_attribution_footer()
