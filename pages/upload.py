"""Upload & Parse page -- ingest log files and display parse results."""

import streamlit as st

from frontend.api_client import APIClient


def render(client: APIClient, sample_logs_dir, _section, _divider, _fmt_badge, _api):
    """Render the Upload & Parse page."""
    _section("Ingest Log Files")

    uploaded_files = st.file_uploader(
        "Drop log files here",
        type=["json", "xml", "csv", "log", "txt", "bin"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # Sample logs quick-load
    if sample_logs_dir.is_dir():
        sample_files = [f for f in sorted(sample_logs_dir.iterdir()) if f.suffix != ".py"]
        if sample_files:
            _section("Quick Demo -- Sample Logs")
            st.markdown(
                '<p style="font-size:0.72rem;color:var(--ob-text-dim);margin-bottom:14px">'
                'Load synthetic semiconductor equipment logs</p>',
                unsafe_allow_html=True,
            )
            cols = st.columns(min(len(sample_files), 4))
            for idx, sf in enumerate(sample_files):
                with cols[idx % 4]:
                    if st.button(f"{sf.name}", key=f"sample_{idx}", use_container_width=True):
                        with open(sf, "rb") as fh:
                            class _F:
                                def __init__(self, n, d):
                                    self.name = n
                                    self._d = d
                                def read(self):
                                    return self._d
                                def getvalue(self):
                                    return self._d
                            result = _api(client.upload_file, _F(sf.name, fh.read()))
                            if result:
                                st.session_state[f"upload_result_{sf.name}"] = result

    # Process uploaded files
    if uploaded_files:
        for uf in uploaded_files:
            with st.spinner(f"Parsing {uf.name}..."):
                result = _api(client.upload_file, uf)
            if result:
                st.session_state[f"upload_result_{uf.name}"] = result

    # Display results
    results_to_show = {k: v for k, v in st.session_state.items() if k.startswith("upload_result_")}
    if results_to_show:
        _section("Parse Results")
        for key, result in results_to_show.items():
            fname = result.get("filename", "unknown")
            fmt = result.get("format_detected", "?")
            n_records = result.get("total_records", 0)
            confidence = result.get("avg_confidence", 0)
            parse_ms = result.get("parse_time_ms", 0)
            n_anomalies = result.get("anomalies_found", 0)
            anomaly_cls = " has-anomalies" if n_anomalies > 0 else ""

            st.markdown(f"""
            <div class="ob-result{anomaly_cls}" style="animation-delay:{list(results_to_show.keys()).index(key)*0.08}s">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
                    <span class="ob-result-name">{fname}</span>
                    {_fmt_badge(fmt)}
                </div>
                <div class="ob-result-meta">
                    <div class="ob-result-meta-item">
                        <span class="ob-result-meta-label">Records</span>
                        <span class="ob-result-meta-val">{n_records:,}</span>
                    </div>
                    <div class="ob-result-meta-item">
                        <span class="ob-result-meta-label">Confidence</span>
                        <span class="ob-result-meta-val" style="color:{"var(--ob-tertiary)" if confidence >= 0.8 else "var(--ob-secondary)"}">{confidence:.0%}</span>
                    </div>
                    <div class="ob-result-meta-item">
                        <span class="ob-result-meta-label">Parse Time</span>
                        <span class="ob-result-meta-val">{parse_ms:.0f}ms</span>
                    </div>
                    <div class="ob-result-meta-item">
                        <span class="ob-result-meta-label">Anomalies</span>
                        <span class="ob-result-meta-val" style="color:{"var(--ob-error)" if n_anomalies > 0 else "var(--ob-text-dim)"}">{n_anomalies}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
