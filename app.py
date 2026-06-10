import streamlit as st
from datetime import date, timedelta

from gsc_engine import (
    auth_gsc,
    get_sites,
    run_analysis,
    generate_excel_report
)

st.set_page_config(
    page_title="GSC Cannibalization Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 GSC Cannibalization Analyzer")

# Connect GSC
if st.button("Connect GSC"):

    with st.spinner("Connecting to Google Search Console..."):

        service = auth_gsc()
        sites = get_sites(service)

        st.session_state["service"] = service
        st.session_state["sites"] = sites

    st.success("Connected Successfully")

# Show controls after connection
if "sites" in st.session_state:

    properties = [
        site["siteUrl"]
        for site in st.session_state["sites"]
    ]

    selected_property = st.selectbox(
        "Select Property",
        properties
    )

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=date.today() - timedelta(days=30)
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=date.today()
        )

    if st.button("Run Analysis"):

        try:

            with st.spinner("Fetching Search Console data..."):

                df_summary, df_swap = run_analysis(
                    st.session_state["service"],
                    selected_property,
                    start_date,
                    end_date
                )

            st.success("Analysis Complete")

            # Dashboard Metrics
            m1, m2 = st.columns(2)

            with m1:
                st.metric(
                    "Cannibalization Opportunities",
                    len(df_summary)
                )

            with m2:
                st.metric(
                    "Keyword Swapping Records",
                    len(df_swap)
                )

            # Cannibalization Summary
            st.subheader("Cannibalization Summary")

            if not df_summary.empty:

                st.dataframe(
                    df_summary,
                    use_container_width=True
                )

                st.info(
                    f"{len(df_summary)} cannibalization opportunities found."
                )

            else:

                st.warning(
                    "No cannibalization opportunities found."
                )

            # Daily Swapping
            st.subheader("Daily Swapping Analysis")

            if not df_swap.empty:

                st.dataframe(
                    df_swap,
                    use_container_width=True
                )

                st.info(
                    f"{len(df_swap)} keyword swapping records found."
                )

            else:

                st.warning(
                    "No swapping data found."
                )

            # Excel Download
            excel_file = generate_excel_report(
                df_summary,
                df_swap
            )

            st.download_button(
                label="📥 Download Excel Report",
                data=excel_file,
                file_name="Cannibalization_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:

            st.error(
                f"Error: {str(e)}"
            )