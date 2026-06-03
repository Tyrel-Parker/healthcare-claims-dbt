import anthropic
import snowflake.connector
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Healthcare Claims Assistant",
    page_icon="🏥",
    layout="wide",
)

SCHEMA_CONTEXT = """
You are a SQL expert working with a Snowflake database called HEALTHCARE_CLAIMS.
IMPORTANT: This is an annual summary dataset for calendar year 2024. There are NO date,
month, or time-series columns. If a question requires time-series or trend analysis,
respond with exactly: CANNOT_ANSWER: <one sentence explaining why>

The gold layer contains these tables (always qualify with HEALTHCARE_CLAIMS.GOLD.<table>):

HEALTHCARE_CLAIMS.GOLD.DIM_PROVIDER — one row per NPI
  provider_key, npi, last_org_name, first_name, credentials, entity_type,
  city, state_code, zip_code, ruca_code, provider_type, is_medicare_participating

HEALTHCARE_CLAIMS.GOLD.FACT_PROVIDER_UTILIZATION — one row per NPI
  utilization_key, provider_key, npi, state_code, provider_type, entity_type,
  is_medicare_participating, tot_hcpcs_codes, tot_beneficiaries, tot_services,
  tot_submitted_charge, tot_medicare_allowed, tot_medicare_payment, tot_medicare_standardized,
  drug_suppression_flag, drug_beneficiaries, drug_services, drug_submitted_charge, drug_medicare_payment,
  med_suppression_flag, med_beneficiaries, med_services, med_submitted_charge, med_medicare_payment,
  payment_to_charge_ratio, drug_payment_share

HEALTHCARE_CLAIMS.GOLD.RPT_PROVIDER_COST_SUMMARY — aggregate per state + provider_type + entity_type
  state_code, provider_type, entity_type, provider_count,
  total_beneficiaries, total_services, total_submitted_charge, total_medicare_payment,
  avg_payment_per_provider, avg_payment_to_charge_ratio, avg_beneficiary_age, avg_risk_score,
  avg_diabetes_prevalence, avg_hypertension_prevalence, avg_depression_prevalence,
  avg_ischemic_heart_prevalence, avg_dual_eligible_rate

Rules:
- Return ONLY a valid Snowflake SQL SELECT statement. No explanation, no markdown, no backticks.
- Always fully qualify table names: HEALTHCARE_CLAIMS.GOLD.<table>
- Use LIMIT 500 unless the query is an aggregate.
- Use DIV0() instead of / to avoid divide-by-zero errors.
- Prefer RPT_PROVIDER_COST_SUMMARY for state/specialty aggregates — it is pre-computed.
- Join FACT_PROVIDER_UTILIZATION to DIM_PROVIDER on provider_key when provider attributes are needed.
"""

EXAMPLE_QUESTIONS = [
    "Which 10 provider specialties have the highest average Medicare payment per provider?",
    "Which states have the most dual-eligible patients on average?",
    "Compare total Medicare payments for Individual vs Organization providers by state",
    "Which provider types have the highest drug payment share?",
    "Show the top 20 providers by total Medicare payment in California",
]


@st.cache_resource
def get_snowflake_conn():
    sf = st.secrets["snowflake"]
    return snowflake.connector.connect(
        account=sf["account"],
        user=sf["user"],
        password=sf["password"],
        database=sf["database"],
        schema=sf["schema"],
        warehouse=sf["warehouse"],
        role=sf["role"],
    )


def generate_sql(question: str) -> str:
    client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SCHEMA_CONTEXT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": question}],
    )
    result = response.content[0].text.strip()
    if result.startswith("CANNOT_ANSWER:"):
        raise ValueError(result[len("CANNOT_ANSWER:"):].strip())
    if not result.upper().startswith("SELECT"):
        raise ValueError(
            "The question can't be answered with this dataset. "
            f"Claude responded: {result[:200]}"
        )
    return result


def run_query(sql: str) -> pd.DataFrame:
    conn = get_snowflake_conn()
    cur = conn.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=cols)


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("🏥 Healthcare Claims Assistant")
st.caption(
    "Ask plain-English questions about CMS Medicare provider data. "
    "Claude generates the SQL; Snowflake runs it."
)

with st.expander("Example questions"):
    for q in EXAMPLE_QUESTIONS:
        st.markdown(f"- {q}")

question = st.text_area(
    "Your question:",
    height=80,
    placeholder="Which states have the highest average beneficiary risk score?",
)

run = st.button("Run", type="primary", disabled=not question)

if run and question:
    with st.status("Generating SQL with Claude...") as status:
        try:
            sql = generate_sql(question)
            status.update(label="Running query on Snowflake...")
            df = run_query(sql)
            status.update(label="Done", state="complete")
        except Exception as e:
            status.update(label="Error", state="error")
            st.error(str(e))
            st.stop()

    with st.expander("Generated SQL", expanded=False):
        st.code(sql, language="sql")

    st.dataframe(df, use_container_width=True)
    st.caption(f"{len(df):,} rows returned")

    # auto-chart if result is simple enough to visualize
    text_cols = [c for c in df.columns if df[c].dtype == object]
    num_cols  = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(text_cols) == 1 and len(num_cols) == 1 and len(df) <= 50:
        st.bar_chart(df.set_index(text_cols[0])[num_cols[0]])
