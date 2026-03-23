"""Summary page -- full log analysis report with breakdowns."""

import datetime

import streamlit as st

from frontend.api_client import APIClient


def render(client: APIClient, _section, _divider, _api):
    """Render the Summary / Report page."""
    _section("Log Analysis Report")

    summary = _api(client.get_summary)
    if summary is None:
        st.warning("Backend is not reachable.")
        return

    total_records = summary.get("total_records", 0)
    total_files = summary.get("total_files", 0)
    total_anomalies = summary.get("total_anomalies", 0)
    avg_conf = summary.get("avg_confidence", 0)
    sev_data = summary.get("severity_breakdown", {})
    evt_data = summary.get("event_type_breakdown", {})
    tool_data = summary.get("tool_breakdown", {})

    # -- Report header card -- Obsidian Protocol: 0px radius, no border, surface layer, glow accent
    st.markdown(f"""
    <div style="background:var(--ob-surface-low);
                padding:32px 36px;margin-bottom:1.75rem;
                position:relative;overflow:hidden;animation:fadeSlideUp 0.5s ease-out;
                box-shadow:var(--ob-glow-ambient)">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--ob-grad)"></div>
        <div style="font-size:0.58rem;color:var(--ob-text-faint);text-transform:uppercase;
                    letter-spacing:0.1em;margin-bottom:20px;display:flex;align-items:center;gap:8px">
            <span style="display:inline-block;width:2px;height:2px;background:var(--ob-primary-container);box-shadow:0 0 6px var(--ob-primary-container);animation:pulse-square 2s ease-in-out infinite"></span>
            Analysis Report &mdash; Generated {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:28px">
            <div>
                <div style="font-size:0.56rem;color:var(--ob-text-faint);text-transform:uppercase;
                            letter-spacing:0.1em">Log Files</div>
                <div style="font-family:var(--font-mono);font-size:2.2rem;font-weight:700;color:var(--ob-on-bg);line-height:1.1;
                            margin-top:4px">{total_files}</div>
            </div>
            <div>
                <div style="font-size:0.56rem;color:var(--ob-text-faint);text-transform:uppercase;
                            letter-spacing:0.1em">Parsed Records</div>
                <div style="font-family:var(--font-mono);font-size:2.2rem;font-weight:700;color:var(--ob-secondary);line-height:1.1;
                            margin-top:4px">{total_records:,}</div>
            </div>
            <div>
                <div style="font-size:0.56rem;color:var(--ob-text-faint);text-transform:uppercase;
                            letter-spacing:0.1em">Anomalies</div>
                <div style="font-family:var(--font-mono);font-size:2.2rem;font-weight:700;color:var(--ob-error);line-height:1.1;
                            margin-top:4px">{total_anomalies:,}</div>
            </div>
            <div>
                <div style="font-size:0.56rem;color:var(--ob-text-faint);text-transform:uppercase;
                            letter-spacing:0.1em">Avg Confidence</div>
                <div style="font-family:var(--font-mono);font-size:2.2rem;font-weight:700;line-height:1.1;margin-top:4px;
                            background:var(--ob-grad);-webkit-background-clip:text;
                            -webkit-text-fill-color:transparent;background-clip:text">{avg_conf:.0%}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -- Severity + Tools side by side --
    col_left, col_right = st.columns(2)

    with col_left:
        _section("Severity Breakdown")
        if sev_data:
            sev_order = ["INFO", "WARNING", "ERROR", "CRITICAL"]
            sev_colors = {"INFO": "#69df54", "WARNING": "#ffbf81", "ERROR": "#ffb4ab", "CRITICAL": "#ff46a0"}
            for i, sev_key in enumerate(sev_order):
                count = sev_data.get(sev_key, 0)
                if count > 0:
                    pct = count / max(total_records, 1) * 100
                    c = sev_colors.get(sev_key, "#8a8694")
                    st.markdown(f"""
                    <div class="ob-bar-row" style="animation-delay:{i*0.06}s">
                        <span class="ob-sev {sev_key.lower()}" style="min-width:80px;text-align:center">{sev_key}</span>
                        <div class="ob-bar-track">
                            <div class="ob-bar-fill" style="width:{min(pct,100):.1f}%;background:{c}"></div>
                        </div>
                        <span class="ob-bar-count">{count:,}</span>
                    </div>
                    """, unsafe_allow_html=True)

    with col_right:
        _section("Tools Active")
        if tool_data:
            for i, (tool, count) in enumerate(sorted(tool_data.items(), key=lambda x: -x[1])):
                if tool:
                    pct = count / max(total_records, 1) * 100
                    st.markdown(f"""
                    <div class="ob-bar-row" style="animation-delay:{i*0.06}s">
                        <span class="ob-bar-label">{tool}</span>
                        <div class="ob-bar-track">
                            <div class="ob-bar-fill" style="width:{min(pct,100):.1f}%;background:var(--ob-grad)"></div>
                        </div>
                        <span class="ob-bar-count">{count:,}</span>
                    </div>
                    """, unsafe_allow_html=True)

    _divider()

    # -- Event classification --
    _section("Event Classification")
    if evt_data:
        evt_items = sorted(evt_data.items(), key=lambda x: -x[1])
        n_cols = min(len(evt_items), 6)
        evt_cols = st.columns(n_cols)
        for idx, (evt_name, evt_count) in enumerate(evt_items):
            with evt_cols[idx % n_cols]:
                st.markdown(f"""
                <div class="ob-stat" style="text-align:center;padding:16px;animation-delay:{idx*0.06}s">
                    <div class="ob-stat-label">{evt_name or "UNKNOWN"}</div>
                    <div class="ob-stat-value" style="font-size:1.4rem">{evt_count:,}</div>
                </div>
                """, unsafe_allow_html=True)

    _divider()

    # -- Recent anomalies --
    _section("Recent Anomalies")
    anomalies = _api(client.get_anomalies)
    if anomalies:
        for i, a in enumerate(anomalies[:10]):
            param = a.get("parameter", "?")
            atype = a.get("anomaly_type", "?")
            asev = a.get("severity", "?")
            desc = a.get("description", "")
            sev_c = {"low": "var(--ob-secondary)", "medium": "var(--ob-error)", "high": "var(--ob-primary-container)"}.get(asev, "var(--ob-text-dim)")
            st.markdown(f"""
            <div class="ob-anomaly-row" style="border-left:2px solid {sev_c};animation:fadeSlideUp 0.4s ease-out {i*0.04}s backwards">
                <div>
                    <span class="ob-anomaly-param">{param}</span>
                    <span class="ob-anomaly-desc">{desc[:90]}</span>
                </div>
                <div style="display:flex;gap:14px;align-items:center">
                    <span class="ob-anomaly-tag">{atype}</span>
                    <span style="font-size:0.76rem;font-weight:700;color:{sev_c}">{asev.upper()}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    elif anomalies is not None:
        st.info("No anomalies to report.")
