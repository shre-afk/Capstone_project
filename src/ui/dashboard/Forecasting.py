import pandas as pd
import plotly.express as px
import streamlit as st

from backend.analysis import api

from ui.dashboard.errors import DashboardErrorHandler, DashboardOperationError
from ui.dashboard.components import DashboardHeader
from ui.dashboard.attribution import render_attribution_footer



DashboardHeader(
    "Forecasting",
    "Plan ahead with intelligent energy demand forecasts.",
).initialize()

def _dashboard_call(operation, callback, *args, fatal=False, **kwargs):
    try:
        return DashboardErrorHandler.execute(operation, callback, *args, **kwargs)
    except DashboardOperationError as error:
        if fatal:
            st.error(str(error))
            st.stop()
        st.warning(str(error))
        return None

buildings = _dashboard_call("loading buildings", api.list_buildings, fatal=True)

if not isinstance(buildings, list):
    st.error("Could not load buildings because the response has an invalid format.")
    st.stop()
if not buildings:
    st.info("No buildings are available to forecast.")
    st.stop()

# ---- Filters row ----

with st.container(border=True, key="forecast_filters"):
    filter_col, horizon_col = st.columns([1, 1], gap="medium")
    with filter_col:
        selected_building = st.selectbox(
            "Building",
            buildings,
            format_func=lambda building: building["name"],
        )

    with horizon_col:
        days = st.selectbox(
            "Forecast horizon",
            [7, 14, 30],
            format_func=lambda n: f"{n} days",
            key="forecast_horizon_selection",
        )

# ---- Fetch forecast ----
forecast = _dashboard_call(
    f"loading the forecast for {selected_building['name']}",
    api.get_forecast,
    selected_building["id"],
    days=days,
)
if forecast is None:
    st.stop()

# ---- Prepare chart data ----
chart_data = forecast.rename_axis("Date").reset_index()
chart_data = chart_data.dropna(subset=["forecast_kwh"])

if chart_data.empty:
    st.info("There aren't enough readings to produce a forecast")
    st.stop()

# ---- Layout panels ----

# Prepare daily values for the metric cards and insight
insights_data = chart_data.copy()
insights_data["Date"] = pd.to_datetime(
    insights_data["Date"], errors="coerce"
)
insights_data["forecast_kwh"] = pd.to_numeric(
    insights_data["forecast_kwh"], errors="coerce"
)

insights_data = insights_data.dropna(subset=["Date", "forecast_kwh"])

daily_forecast = (
    insights_data.set_index("Date")["forecast_kwh"]
    .resample("D")
    .sum(min_count=1)
    .dropna()
)

if daily_forecast.empty:
    st.info("There aren't enough readings to produce a daily forecast.")
    st.stop()

total_kwh = daily_forecast.sum()
average_daily_kwh = daily_forecast.mean()
peak_day = daily_forecast.idxmax()
peak_day_kwh = daily_forecast.max()
first_day_kwh = daily_forecast.iloc[0]
last_day_kwh = daily_forecast.iloc[-1]
if first_day_kwh > 0:
    trend_change = (last_day_kwh - first_day_kwh) / first_day_kwh * 100
else:
    trend_change = None

chart_col, insights_col = st.columns(
    [1.6, 1],
    gap="medium",
    vertical_alignment="top",
)
with chart_col:
    with st.container(border=True, key="consumption_forecast"):
        st.markdown("### Consumption Forecasting")
        st.caption("Hourly demand forecast for the selected building")

        chart = px.line(
            chart_data,
            x="Date",
            y="forecast_kwh",
            markers=False,
            template="plotly_white",
        )

        chart.update_traces(
            mode="lines",
            line=dict(color="#173B63", width=2.5),
            hovertemplate=(
                "%{x|%b %d, %H:%M}<br>"
                "Forecast: %{y:.2f} kWh<extra></extra>"
            ),
        )

        chart.update_layout(
            margin=dict(l=20, r=16, t=12, b=36),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="sans-serif", color="#344B63"),
            hovermode="x unified",
            height=300,
            xaxis=dict(
                title="Date",
                tickformat="%b %d",
                nticks=8,
                showgrid=False,
                zeroline=False,
                automargin=True,
            ),
            yaxis=dict(
                title="Forecast (kWh)",
                gridcolor="#E3D8C8",
                zeroline=False,
                automargin=True,
            ),
        )
        st.plotly_chart(
            chart,
            width="stretch",
            height=300,
            config={"displayModeBar": False},
        )

    total_col, peak_col, average_col = st.columns(3, gap="small")
    with total_col:
        with st.container(border=True, key="total_kwh_forecast"):
            st.metric("Forecast total (kWh)", f"{total_kwh:,.0f}")

    with peak_col:
        with st.container(border=True, key="forecast_peak_day"):
            st.metric(
                "Peak day",
                peak_day.strftime("%b %d"),
                delta=f"{peak_day_kwh:,.1f} kWh",
                delta_color="off",
            )

    with average_col:
        with st.container(border=True, key="forecast_average_daily"):
            st.metric("Daily average (kWh)", f"{average_daily_kwh:,.1f}")

    st.caption("Summary values are based on daily totals from the hourly forecast.")

with insights_col:
    with st.container(border=True, key="insights_forecast"):
        st.markdown("### ✨ Forecast Insights")
        st.caption(f"{days}-day outlook · {selected_building['name']}")

        if trend_change is None:
            st.markdown("### Demand outlook")
            st.write("The forecast does not include a usable starting value for a trend comparison.")
        else:
            trend_direction = (
                "increase" if trend_change > 0
                else "decrease" if trend_change < 0
                else "remain steady"
            )
            st.markdown("**Demand outlook**")
            st.markdown(
                f"<div class='forecast-trend'>"
                f"<strong>{abs(trend_change):.1f}%</strong>"
                f"<span>expected to {trend_direction}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.caption(
                f"Daily forecast: {first_day_kwh:,.1f} kWh on "
                f"{daily_forecast.index[0]:%b %d} to "
                f"{last_day_kwh:,.1f} kWh on "
                f"{daily_forecast.index[-1]:%b %d}."
            )

        with st.container(key="forecast_insight_tip"):
            st.markdown(
                f"<div class='forecast-action-content'>"
                f"<div class='forecast-action-title'>"
                f"<span aria-hidden='true'>💡</span>"
                f"<strong>Recommended action</strong>"
                f"</div>"
                f"<p class='forecast-action-copy'>"
                f"Review HVAC schedules before {peak_day:%b %d}."
                f"</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

render_attribution_footer()
