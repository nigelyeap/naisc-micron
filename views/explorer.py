"""Log Explorer page -- filter and browse parsed log records."""

import json

import streamlit as st
import pandas as pd

from frontend.api_client import APIClient


def render(client: APIClient, _section, _divider, _api):
    """Render the Log Explorer page."""
    _section("Log Explorer")

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        tool_id = st.text_input("Tool ID", placeholder="e.g. ETCH-001")
    with fc2:
        event_type = st.selectbox("Event Type", ["All", "SENSOR_READ", "ALARM", "EVENT", "RECIPE", "WAFER_OP", "UNKNOWN"])
    with fc3:
        severity = st.selectbox("Severity", ["All", "INFO", "WARNING", "ERROR", "CRITICAL"])
    with fc4:
        limit = st.number_input("Limit", min_value=10, max_value=1000, value=100, step=50)

    filters: dict = {"limit": limit}
    if tool_id:
        filters["tool_id"] = tool_id
    if event_type != "All":
        filters["event_type"] = event_type
    if severity != "All":
        filters["severity"] = severity

    if st.button("Search Records", type="primary", use_container_width=False):
        data = _api(client.get_records, filters)
        if data is not None:
            if not data:
                st.info("No records match the current filters.")
            else:
                st.markdown(
                    f'<p style="font-size:0.76rem;color:var(--ob-text-dim);margin-bottom:12px">'
                    f'Found <strong style="color:var(--ob-on-bg)">{len(data)}</strong> records</p>',
                    unsafe_allow_html=True,
                )
                df = pd.DataFrame(data)
                display_cols = ["id", "timestamp", "tool_id", "module_id",
                                "event_type", "severity", "confidence", "source_format"]
                available = [c for c in display_cols if c in df.columns]
                st.dataframe(
                    df[available],
                    use_container_width=True,
                    height=480,
                    column_config={
                        "confidence": st.column_config.ProgressColumn(
                            "Confidence", min_value=0, max_value=1, format="%.0%%",
                        ),
                    },
                )

                _divider()
                st.markdown(
                    '<p style="font-size:0.64rem;color:var(--ob-text-faint);text-transform:uppercase;'
                    'letter-spacing:0.1em">Record Details (first 20)</p>',
                    unsafe_allow_html=True,
                )
                for _, row in df.head(20).iterrows():
                    ts = row.get("timestamp", "")
                    tid = row.get("tool_id", "")
                    evt = row.get("event_type", "")
                    sev = row.get("severity", "")
                    # Short label: just tool + event + severity
                    ts_short = str(ts)[:19] if ts else "---"
                    label = f"{ts_short} | {tid or '---'} | {evt or '---'} | {sev or '---'}"
                    with st.expander(label):
                        # Show key fields as compact columns
                        c1, c2, c3, c4 = st.columns(4)
                        c1.markdown(f"**Timestamp**\n\n`{ts}`")
                        c2.markdown(f"**Tool**\n\n`{tid}`")
                        c3.markdown(f"**Event**\n\n`{evt}`")
                        c4.markdown(f"**Severity**\n\n`{sev}`")

                        params_raw = row.get("parameters_json", "{}")
                        if params_raw:
                            try:
                                params = json.loads(params_raw) if isinstance(params_raw, str) else params_raw
                                if params:
                                    st.markdown("**Parameters:**")
                                    st.json(params, expanded=False)
                            except Exception:
                                pass
                        raw = row.get("raw_content", "")
                        if raw:
                            st.markdown("**Raw Content:**")
                            st.code(str(raw)[:500], language=None)
