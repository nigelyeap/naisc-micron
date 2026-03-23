"""Analytics Dashboard page -- charts, KPIs, anomalies, and trends."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from frontend.api_client import APIClient


def render(client: APIClient, _section, _divider, _api, plotly_layout: dict):
    """Render the Analytics Dashboard page."""
    _section("Analytics Dashboard")

    summary = _api(client.get_summary)
    if not summary:
        return

    # -- KPI row --
    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        ("Total Records", summary.get("total_records", 0), ""),
        ("Files Ingested", summary.get("total_files", 0), "secondary"),
        ("Anomalies", summary.get("total_anomalies", 0), "error"),
        ("Avg Confidence", f'{summary.get("avg_confidence", 0):.0%}', "grad"),
    ]
    for col, (label, value, cls) in zip([c1, c2, c3, c4], kpis):
        v_str = f"{value:,}" if isinstance(value, int) else value
        col.markdown(
            f'<div class="ob-stat">'
            f'<div class="ob-stat-label">{label}</div>'
            f'<div class="ob-stat-value {cls}">{v_str}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _divider()

    # -- Severity & Events --
    col_sev, col_evt = st.columns(2)

    with col_sev:
        _section("Severity Distribution")
        sev_data = summary.get("severity_breakdown", {})
        if sev_data:
            sev_colors = {"INFO": "#69df54", "WARNING": "#ffbf81", "ERROR": "#ffb4ab", "CRITICAL": "#ff46a0"}
            sev_df = pd.DataFrame([{"Severity": k, "Count": v} for k, v in sev_data.items() if k])
            if not sev_df.empty:
                fig = px.bar(sev_df, x="Severity", y="Count", color="Severity",
                             color_discrete_map=sev_colors)
                fig.update_layout(**plotly_layout, height=300, showlegend=False, title=None)
                fig.update_traces(marker_line_width=0, opacity=0.9)
                st.plotly_chart(fig, use_container_width=True)

    with col_evt:
        _section("Event Types")
        evt_data = summary.get("event_type_breakdown", {})
        if evt_data:
            evt_df = pd.DataFrame([{"Event": k or "UNKNOWN", "Count": v} for k, v in evt_data.items()])
            if not evt_df.empty:
                fig = px.pie(evt_df, names="Event", values="Count", hole=0.6)
                fig.update_layout(**plotly_layout, height=300, title=None,
                                 legend=dict(font=dict(size=10, color="#8a8694")))
                fig.update_traces(
                    textposition='inside', textfont_size=10,
                    marker=dict(line=dict(color='#131319', width=2)),
                )
                st.plotly_chart(fig, use_container_width=True)

    _divider()

    # -- Anomaly table --
    _section("Detected Anomalies")
    anomalies = _api(client.get_anomalies)
    if anomalies:
        adf = pd.DataFrame(anomalies)
        display_anom = ["id", "parameter", "value", "expected_min", "expected_max",
                        "anomaly_type", "severity", "z_score", "description"]
        available_anom = [c for c in display_anom if c in adf.columns]
        st.dataframe(
            adf[available_anom].head(50),
            use_container_width=True,
            height=300,
            column_config={
                "z_score": st.column_config.NumberColumn("Z-Score", format="%.2f"),
                "value": st.column_config.NumberColumn("Value", format="%.4f"),
                "expected_min": st.column_config.NumberColumn("Min", format="%.4f"),
                "expected_max": st.column_config.NumberColumn("Max", format="%.4f"),
            },
        )
    elif anomalies is not None:
        st.info("No anomalies detected yet. Upload some log files first.")

    _divider()

    # -- Trend chart --
    _section("Sensor Trends")
    tcol1, tcol2 = st.columns([3, 1])
    with tcol2:
        sel_param = st.selectbox("Parameter", ["temperature_c", "pressure_pa", "power_w", "flow_sccm"])
    with tcol1:
        ts_data = _api(client.get_timeseries, sel_param)
        if ts_data:
            ts_df = pd.DataFrame(ts_data)
            if "timestamp" in ts_df.columns and "value" in ts_df.columns:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=ts_df["timestamp"], y=ts_df["value"],
                    mode="lines",
                    line=dict(color="#ff46a0", width=1.5),
                    fill="tozeroy",
                    fillcolor="rgba(255,70,160,0.04)",
                    name=sel_param,
                ))
                fig.update_layout(
                    **plotly_layout, height=380,
                    title=dict(text=f"{sel_param.replace('_', ' ').title()} Over Time",
                               font=dict(size=13, color="#e4e1ea")),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timeseries data available for this parameter.")
        elif ts_data is not None:
            st.info("No data. Try uploading more logs.")

    _divider()

    # -- Tool breakdown --
    _section("Tool Distribution")
    tool_data = summary.get("tool_breakdown", {})
    if tool_data:
        tool_df = pd.DataFrame([
            {"Tool": k, "Records": v} for k, v in tool_data.items() if k
        ]).sort_values("Records", ascending=True)
        fig = px.bar(tool_df, y="Tool", x="Records", orientation="h",
                     color_discrete_sequence=["#ff46a0"])
        fig.update_layout(**plotly_layout, height=max(200, len(tool_df) * 45),
                          title=None, showlegend=False)
        fig.update_traces(marker_line_width=0, opacity=0.85)
        st.plotly_chart(fig, use_container_width=True)
