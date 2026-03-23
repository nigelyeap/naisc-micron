"""Natural Language Query page -- ask questions about log data in plain English."""

import streamlit as st
import pandas as pd

from frontend.api_client import APIClient


def render(client: APIClient, _section, _divider, _api):
    """Render the Natural Language Query page."""
    _section("Natural Language Query")

    st.markdown(
        '<p style="font-size:0.84rem;color:var(--ob-text-dim);margin-bottom:18px">'
        'Ask questions about your log data in plain English. '
        'The system converts your question to SQL and returns results.</p>',
        unsafe_allow_html=True,
    )

    question = st.text_input(
        "Your question",
        placeholder="e.g. Show me all alarm events in the last 24 hours",
        label_visibility="collapsed",
    )

    st.markdown(
        '<p style="font-size:0.6rem;color:var(--ob-text-faint);text-transform:uppercase;'
        'letter-spacing:0.1em;margin:14px 0 8px 0">Try an example</p>',
        unsafe_allow_html=True,
    )
    examples = [
        "Show me all alarm events",
        "What's the average temperature per tool?",
        "Which tool has the most faults?",
        "Show records with confidence below 0.7",
    ]
    ecols = st.columns(2)
    for idx, ex in enumerate(examples):
        with ecols[idx % 2]:
            if st.button(ex, key=f"ex_{idx}", use_container_width=True):
                question = ex

    if question:
        with st.spinner("Generating SQL and executing query..."):
            result = _api(client.nl_query, question)

        if result:
            _divider()

            sql = result.get("generated_sql", "")
            if sql:
                st.markdown(
                    '<p style="font-size:0.6rem;color:var(--ob-text-faint);text-transform:uppercase;'
                    'letter-spacing:0.1em;margin-bottom:8px">Generated SQL</p>',
                    unsafe_allow_html=True,
                )
                st.code(sql, language="sql")

            explanation = result.get("explanation", "")
            if explanation:
                st.markdown(
                    f'<div style="background:var(--ob-surface-container);'
                    f'border-left:2px solid var(--ob-primary);'
                    f'padding:16px 20px;margin:14px 0;'
                    f'font-size:0.84rem;color:var(--ob-on-bg)">{explanation}</div>',
                    unsafe_allow_html=True,
                )

            rows = result.get("results", [])
            if rows:
                st.markdown(
                    f'<p style="font-size:0.6rem;color:var(--ob-text-faint);text-transform:uppercase;'
                    f'letter-spacing:0.1em;margin:14px 0 8px 0">{len(rows)} results</p>',
                    unsafe_allow_html=True,
                )
                st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
            elif rows is not None:
                st.info("Query returned no results.")
