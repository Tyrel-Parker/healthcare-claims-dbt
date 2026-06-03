import streamlit as st
import pandas as pd
import plotly.express as px

# When running inside Snowflake (SiS) the active session is available directly.
# When running locally, fall back to snowflake-connector via st.secrets.
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    def query(sql: str) -> pd.DataFrame:
        return session.sql(sql).to_pandas()
    RUNNING_IN_SNOWFLAKE = True
except Exception:
    import snowflake.connector
    RUNNING_IN_SNOWFLAKE = False
    _conn = None
    def _get_conn():
        global _conn
        if _conn is None:
            sf = st.secrets["snowflake"]
            _conn = snowflake.connector.connect(
                account=sf["account"], user=sf["user"], password=sf["password"],
                database=sf["database"], schema=sf["schema"],
                warehouse=sf["warehouse"], role=sf["role"],
            )
        return _conn
    @st.cache_data(ttl=3600)
    def query(sql: str) -> pd.DataFrame:
        cur = _get_conn().cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=cols)
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass
        return df


def bar(df, x, y, title, x_label=None, y_label=None, dollars=False, pct=False):
    fmt = "$,.0f" if dollars else ",.1%" if pct else ",.0f"
    fig = px.bar(
        df, x=x, y=y, title=title,
        labels={x: x_label or x, y: y_label or y},
        color_discrete_sequence=["#1f77b4"],
        height=400,
    )
    fig.update_layout(
        xaxis_tickangle=-40,
        yaxis_tickformat=fmt,
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig.update_traces(hovertemplate=f"%{{x}}<br>{y_label or y}: %{{y:{fmt}}}<extra></extra>")
    return fig


# ── Headline metrics ──────────────────────────────────────────────────────────
totals = query("""
    SELECT
        SUM(total_medicare_payment)      AS total_payment,
        SUM(total_beneficiaries)         AS total_benes,
        SUM(provider_count)              AS total_providers,
        AVG(avg_payment_to_charge_ratio) AS avg_ratio
    FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
""").iloc[0]

st.title("🏥 Healthcare Claims Analytics")
st.caption("2024 CMS Medicare Physician & Other Practitioners — 1.3M providers across the U.S.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Medicare Payments", f"${float(totals['TOTAL_PAYMENT'])/1e9:.1f}B")
c2.metric("Total Beneficiaries",     f"{float(totals['TOTAL_BENES'])/1e6:.1f}M")
c3.metric("Providers",               f"{float(totals['TOTAL_PROVIDERS']):,.0f}")
c4.metric("Avg Payment / Charge",    f"{float(totals['AVG_RATIO']):.1%}")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    states = query("""
        SELECT state_code, SUM(total_medicare_payment) AS total_payment
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        WHERE state_code NOT IN ('XX','ZZ')
        GROUP BY state_code ORDER BY total_payment DESC LIMIT 15
    """)
    st.plotly_chart(bar(
        states, "STATE_CODE", "TOTAL_PAYMENT",
        title="Top 15 States by Medicare Payment",
        x_label="State", y_label="Total Medicare Payment", dollars=True,
    ), use_container_width=True)

with col_b:
    specs = query("""
        SELECT provider_type, SUM(total_medicare_payment) AS total_payment
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        GROUP BY provider_type ORDER BY total_payment DESC LIMIT 15
    """)
    st.plotly_chart(bar(
        specs, "PROVIDER_TYPE", "TOTAL_PAYMENT",
        title="Top 15 Specialties by Medicare Payment",
        x_label="Specialty", y_label="Total Medicare Payment", dollars=True,
    ), use_container_width=True)

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    dual = query("""
        SELECT provider_type, AVG(avg_dual_eligible_rate) AS dual_rate
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        WHERE avg_dual_eligible_rate IS NOT NULL
        GROUP BY provider_type ORDER BY dual_rate DESC LIMIT 15
    """)
    st.plotly_chart(bar(
        dual, "PROVIDER_TYPE", "DUAL_RATE",
        title="Highest Dual-Eligible Rate by Specialty",
        x_label="Specialty", y_label="Dual-Eligible Patient Rate", pct=True,
    ), use_container_width=True)

with col_d:
    ratio = query("""
        SELECT provider_type, AVG(avg_payment_to_charge_ratio) AS ratio
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        WHERE avg_payment_to_charge_ratio IS NOT NULL
        GROUP BY provider_type ORDER BY ratio DESC LIMIT 15
    """)
    st.plotly_chart(bar(
        ratio, "PROVIDER_TYPE", "RATIO",
        title="Medicare Payment as % of Submitted Charge",
        x_label="Specialty", y_label="Payment / Charge Ratio", pct=True,
    ), use_container_width=True)

st.divider()

st.subheader("Average Chronic Condition Burden by Specialty")
st.caption("% of each provider's patient panel with the condition — top 20 specialties by diabetes prevalence")
cc = query("""
    SELECT
        provider_type                                AS "Specialty",
        ROUND(AVG(avg_diabetes_prevalence), 1)       AS "Diabetes %",
        ROUND(AVG(avg_hypertension_prevalence), 1)   AS "Hypertension %",
        ROUND(AVG(avg_depression_prevalence), 1)     AS "Depression %",
        ROUND(AVG(avg_ischemic_heart_prevalence), 1) AS "Ischemic Heart %",
        ROUND(AVG(avg_risk_score), 3)                AS "Avg Risk Score"
    FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
    WHERE avg_diabetes_prevalence IS NOT NULL
    GROUP BY provider_type
    ORDER BY "Diabetes %" DESC LIMIT 20
""")
st.dataframe(cc.set_index("Specialty"), use_container_width=True)

st.caption("Source: CMS Medicare Physician & Other Practitioners by Provider (2024)")
