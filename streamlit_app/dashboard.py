import snowflake.connector
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Healthcare Claims Dashboard",
    page_icon="🏥",
    layout="wide",
)

@st.cache_resource
def get_conn():
    sf = st.secrets["snowflake"]
    return snowflake.connector.connect(
        account=sf["account"], user=sf["user"], password=sf["password"],
        database=sf["database"], schema=sf["schema"],
        warehouse=sf["warehouse"], role=sf["role"],
    )

@st.cache_data(ttl=3600)
def query(sql: str) -> pd.DataFrame:
    cur = get_conn().cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=cols)


st.title("🏥 Healthcare Claims Analytics")
st.caption("2024 CMS Medicare Physician & Other Practitioners — 1.3M providers across the U.S.")

# ── Row 1: headline metrics ───────────────────────────────────────────────────
totals = query("""
    SELECT
        SUM(total_medicare_payment)   AS total_payment,
        SUM(total_beneficiaries)      AS total_benes,
        SUM(provider_count)           AS total_providers,
        AVG(avg_payment_to_charge_ratio) AS avg_ratio
    FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Medicare Payments", f"${totals['TOTAL_PAYMENT']/1e9:.1f}B")
c2.metric("Total Beneficiaries",     f"{totals['TOTAL_BENES']/1e6:.1f}M")
c3.metric("Providers",               f"{totals['TOTAL_PROVIDERS']/1e6:.2f}M")
c4.metric("Avg Payment / Charge",    f"{totals['AVG_RATIO']:.1%}")

st.divider()

# ── Row 2: top states | top specialties ──────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Top 15 States by Medicare Payment")
    states = query("""
        SELECT state_code, SUM(total_medicare_payment) AS total_payment
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        WHERE state_code NOT IN ('XX','ZZ')
        GROUP BY state_code
        ORDER BY total_payment DESC
        LIMIT 15
    """)
    states.columns = ["State", "Total Payment"]
    st.bar_chart(states.set_index("State"))

with col_b:
    st.subheader("Top 15 Provider Specialties by Medicare Payment")
    specs = query("""
        SELECT provider_type, SUM(total_medicare_payment) AS total_payment
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        GROUP BY provider_type
        ORDER BY total_payment DESC
        LIMIT 15
    """)
    specs.columns = ["Specialty", "Total Payment"]
    st.bar_chart(specs.set_index("Specialty"))

st.divider()

# ── Row 3: drug share | chronic conditions ────────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Individual vs Organization — Payment Split by State")
    entity = query("""
        SELECT entity_type, SUM(total_medicare_payment) AS total_payment
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        GROUP BY entity_type
        ORDER BY total_payment DESC
    """)
    entity.columns = ["Entity Type", "Total Payment"]
    st.bar_chart(entity.set_index("Entity Type"))

with col_d:
    st.subheader("Avg Chronic Condition Burden by Specialty (Top 15)")
    cc = query("""
        SELECT
            provider_type,
            AVG(avg_diabetes_prevalence)      AS diabetes,
            AVG(avg_hypertension_prevalence)  AS hypertension,
            AVG(avg_depression_prevalence)    AS depression,
            AVG(avg_ischemic_heart_prevalence) AS ischemic_heart
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        WHERE avg_diabetes_prevalence IS NOT NULL
        GROUP BY provider_type
        ORDER BY diabetes DESC
        LIMIT 15
    """)
    cc.columns = ["Specialty", "Diabetes %", "Hypertension %", "Depression %", "Ischemic Heart %"]
    st.dataframe(cc.set_index("Specialty"), use_container_width=True)

st.divider()

# ── Row 4: dual eligible | payment efficiency ─────────────────────────────────
col_e, col_f = st.columns(2)

with col_e:
    st.subheader("Highest Dual-Eligible Patient Rate by Specialty")
    dual = query("""
        SELECT provider_type, AVG(avg_dual_eligible_rate) AS dual_rate
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        WHERE avg_dual_eligible_rate IS NOT NULL
        GROUP BY provider_type
        ORDER BY dual_rate DESC
        LIMIT 15
    """)
    dual.columns = ["Specialty", "Dual-Eligible Rate"]
    st.bar_chart(dual.set_index("Specialty"))

with col_f:
    st.subheader("Payment Efficiency: Best vs Worst Specialties")
    ratio = query("""
        SELECT provider_type, AVG(avg_payment_to_charge_ratio) AS ratio
        FROM HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY
        WHERE avg_payment_to_charge_ratio IS NOT NULL
        GROUP BY provider_type
        ORDER BY ratio DESC
        LIMIT 15
    """)
    ratio.columns = ["Specialty", "Payment / Charge Ratio"]
    st.bar_chart(ratio.set_index("Specialty"))

st.caption("Source: CMS Medicare Physician & Other Practitioners by Provider (2024)")
