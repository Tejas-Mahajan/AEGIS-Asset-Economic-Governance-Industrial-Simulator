import os
import sys
import pandas as pd
import streamlit as st

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_simulation import (
    load_fd001_dataframe,
    to_asset_record,
    EventManager,
    PipelineConfig,
    process_record_pipeline,
)
from predictive_analytics import predict_rul
from economic_governance import (
    get_asset_cost_table,
    generate_ranking_output,
    generate_risk_budget_output,
)
from dashboard.mock_upstream import (
    get_mock_asset_records,
    get_mock_rul_predictions,
    get_mock_ranking_outputs,
    get_mock_risk_budget_outputs,
)
from dashboard.audit_trail import generate_decision_audit_explanation

# Page setup
st.set_page_config(
    page_title="Smart Industrial Asset Evaluation System",
    page_icon="⚡",
    layout="wide",
)

# Custom CSS for rich aesthetics
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.0rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Session state initialization
if "event_manager" not in st.session_state:
    st.session_state.event_manager = EventManager()
if "engine_cycles" not in st.session_state:
    st.session_state.engine_cycles = {i: 1 for i in range(1, 6)}
if "history" not in st.session_state:
    st.session_state.history = {f"ENG-{i:03d}": [] for i in range(1, 6)}
if "dataset_df" not in st.session_state:
    st.session_state.dataset_df = load_fd001_dataframe()
if "max_cycles_map" not in st.session_state:
    st.session_state.max_cycles_map = (
        st.session_state.dataset_df.groupby("engine_id")["cycle"].max().to_dict()
    )

df_data = st.session_state.dataset_df
max_cycles_map = st.session_state.max_cycles_map

# Header
st.markdown('<div class="main-header">Smart Industrial Asset Evaluation System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-Time Predictive Analytics, AHP Governance & CVaR Risk Budgeting</div>', unsafe_allow_html=True)

# Sidebar Configuration & Controls
st.sidebar.title("🎛️ Control Panel")
mode = st.sidebar.radio("Data Source Mode", ["Live Real-Time Pipeline", "Standalone Mock Mode"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Event Injection API (D3)")
inject_asset = st.sidebar.selectbox("Target Asset", [f"ENG-{i:03d}" for i in range(1, 6)])
inject_event_type = st.sidebar.selectbox("Event Type", ["sensor_spike", "manual_failure"])
inject_magnitude = st.sidebar.slider("Event Magnitude", min_value=0.1, max_value=2.0, value=0.5, step=0.1)

if st.sidebar.button("🚀 Inject Event"):
    resp = st.session_state.event_manager.inject_event(
        {
            "asset_id": inject_asset,
            "event_type": inject_event_type,
            "magnitude": inject_magnitude,
        }
    )
    if resp["accepted"]:
        st.sidebar.success(resp["message"])
    else:
        st.sidebar.error(resp["message"])

st.sidebar.markdown("---")
st.sidebar.subheader("⏩ Fast-Forward Simulation (D5)")
fast_forward_n = st.sidebar.slider("Advance Cycles (N)", min_value=1, max_value=50, value=5)
if st.sidebar.button("Advance N Cycles"):
    for eng_id in range(1, 6):
        st.session_state.engine_cycles[eng_id] += fast_forward_n
    st.sidebar.info(f"Advanced all streams by {fast_forward_n} cycles.")

# Fetch & Process Current State Records
current_asset_records = []
current_rul_records = []

if mode == "Standalone Mock Mode":
    current_asset_records = get_mock_asset_records(count=5)
    current_rul_records = get_mock_rul_predictions(count=5)
    ranking_records = get_mock_ranking_outputs(count=5)
    risk_budget_records = get_mock_risk_budget_outputs(count=5)
else:
    # Real integrated pipeline execution
    for eng_id in range(1, 6):
        asset_id = f"ENG-{eng_id:03d}"
        max_cycle = max_cycles_map[eng_id]
        curr_c = st.session_state.engine_cycles[eng_id]

        # Fetch cycle row from dataset
        eng_rows = df_data[df_data["engine_id"] == eng_id].sort_values("cycle")
        row_idx = min(curr_c - 1, len(eng_rows) - 1)
        row = eng_rows.iloc[row_idx]

        # Step 1: Base Asset Record from data_simulation
        raw_rec = to_asset_record(row, max_cycle)
        # Apply pending event injections if any
        event_applied_rec = st.session_state.event_manager.apply_events(raw_rec)
        # Apply pipeline noise/anomaly processing
        cfg = PipelineConfig(enable_noise=False, enable_anomaly=True)
        processed_rec = process_record_pipeline(
            event_applied_rec,
            history=st.session_state.history[asset_id],
            config=cfg,
        )

        st.session_state.history[asset_id].append(processed_rec)
        current_asset_records.append(processed_rec)

        # Step 2: Predictive RUL Record
        rul_rec = predict_rul(processed_rec)
        current_rul_records.append(rul_rec)

    # Step 3: Economic Governance Rankings & Risk/Budget Allocation
    cost_table = get_asset_cost_table([r["asset_id"] for r in current_asset_records])
    ranking_records = generate_ranking_output(current_rul_records, cost_table=cost_table)
    risk_budget_records = generate_risk_budget_output(
        current_rul_records, ranking_records=ranking_records, cost_table=cost_table
    )

# Navigation Tabs for Views
tab_health, tab_ranking, tab_risk = st.tabs(
    ["🏥 Asset Health View", "📊 Priority Ranking (AHP)", "💰 Risk & Budget Allocation (CVaR)"]
)

# VIEW 1: ASSET HEALTH VIEW
with tab_health:
    st.subheader("Asset Health & Sensor Telemetry")
    health_df = pd.DataFrame(
        [
            {
                "Asset ID": r["asset_id"],
                "Cycle": r["cycle"],
                "Health (%)": r["health_pct"],
                "Data Quality": r["data_quality_flag"],
                "Anomaly Detected": "⚠️ TRUE" if r["anomaly_detected"] else "✅ OK",
                "Timestamp": r["timestamp"],
            }
            for r in current_asset_records
        ]
    )
    st.dataframe(health_df, use_container_width=True)

    st.subheader("Predictive RUL & Confidence Ranges (Section 2)")
    rul_df = pd.DataFrame(
        [
            {
                "Asset ID": r["asset_id"],
                "Estimated RUL (Cycles)": r["rul_cycles"],
                "Confidence Low": r["rul_cycles_confidence_low"],
                "Confidence High": r["rul_cycles_confidence_high"],
                "RUL Days": "null (MVP)",
            }
            for r in current_rul_records
        ]
    )
    st.dataframe(rul_df, use_container_width=True)

# VIEW 2: PRIORITY RANKING VIEW (AHP)
with tab_ranking:
    st.subheader("AHP Priority Asset Ranking (Section 3)")
    if ranking_records:
        top_weights = ranking_records[0]["weights_used"]
        cr_val = ranking_records[0]["consistency_ratio"]
        sens_pct = ranking_records[0]["metadata"]["sensitivity_threshold_pct"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Safety Weight", f"{top_weights['safety']:.4f}")
        col2.metric("Consistency Ratio (CR)", f"{cr_val:.4f}", help="Valid if CR < 0.1")
        col3.metric("Sensitivity Threshold", f"{sens_pct:.1f}%", help="Smallest shift flipping rank #1")

    rank_table_df = pd.DataFrame(
        [
            {
                "Rank": r["priority_rank"],
                "Asset ID": r["asset_id"],
                "Criticality Score": r["criticality_score"],
                "RUL (Cycles)": r["metadata"]["rul_cycles"],
            }
            for r in ranking_records
        ]
    )
    st.dataframe(rank_table_df, use_container_width=True)

    st.markdown("---")
    st.subheader("📝 Decision Audit Trail (D4)")
    for rank_rec in ranking_records:
        aid = rank_rec["asset_id"]
        rul_rec = next(r for r in current_rul_records if r["asset_id"] == aid)
        risk_rec = next(r for r in risk_budget_records if r["asset_id"] == aid)
        audit_line = generate_decision_audit_explanation(rank_rec, rul_rec, risk_rec)
        st.info(f"👉 {audit_line}")

# VIEW 3: RISK & BUDGET ALLOCATION VIEW (CVaR)
with tab_risk:
    st.subheader("Financial Risk Exposure & Budget Allocation (Section 4)")
    risk_df = pd.DataFrame(
        [
            {
                "Asset ID": r["asset_id"],
                "CVaR 95% Exposure (₹)": f"₹{r['cvar_95']:,.2f}",
                "Expected Loss (₹)": f"₹{r['expected_cost']:,.2f}",
                "Recommended Budget (₹)": f"₹{r['recommended_budget_allocation']:,.2f}",
                "Baseline Reactive Cost (₹)": f"₹{r['baseline_reactive_cost']:,.2f}",
                "Predictive Savings (₹)": f"₹{r['predictive_savings']:,.2f}",
                "Pool ID": r["budget_pool_id"],
            }
            for r in risk_budget_records
        ]
    )
    st.dataframe(risk_df, use_container_width=True)

    st.subheader("Reactive vs Predictive Monetary Savings")
    chart_data = pd.DataFrame(
        {
            "Asset ID": [r["asset_id"] for r in risk_budget_records],
            "Baseline Reactive Cost": [r["baseline_reactive_cost"] for r in risk_budget_records],
            "Predictive Savings": [r["predictive_savings"] for r in risk_budget_records],
        }
    ).set_index("Asset ID")
    st.bar_chart(chart_data)
