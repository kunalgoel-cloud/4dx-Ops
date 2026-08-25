import streamlit as st
from src.demo_data import get_demo_metrics

st.set_page_config(page_title="Operations 4DX", page_icon="📊", layout="wide")
st.markdown("<style>.block-container{padding-top:1.2rem}.metric-card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:white}</style>", unsafe_allow_html=True)
st.title("Operations 4DX")
st.caption("Phase 1 UX prototype — deterministic metrics first; Gemini ASK AI will be added in Phase 2.")

m = get_demo_metrics()
c1,c2,c3,c4 = st.columns(4)
for col,key in zip((c1,c2,c3,c4),("fulfillment","otif","cost","delivery")):
    x=m[key]; col.metric(x["name"],x["value"],x["delta"]); col.caption(f'Target: {x["target"]} • {x["coverage"]}')

st.divider()
left,right=st.columns([2.1,1])
with left:
    st.subheader("4DX Weekly Scorecard")
    st.dataframe(m["scorecard"],use_container_width=True,hide_index=True)
with right:
    st.subheader("This week's focus")
    st.info("🔴 OTIF is the largest gap in this prototype. Use Delivery drill-down to identify customer × city × courier concentration.")
    st.button("ASK AI — Phase 2",disabled=True,use_container_width=True)

st.subheader("Performance trend")
st.line_chart(m["trend"].set_index("Date")[["Fulfillment %","OTIF %","Cost / Shipment"]],height=300)
st.subheader("Lead measures")
cols=st.columns(3)
for col,x in zip(cols,m["lead_measures"]):
    col.metric(x["name"],x["value"],x["delta"]); col.caption(f'Target: {x["target"]} • {x["coverage"]}')
st.divider()
st.caption("— = unavailable • ⚠ = incomplete coverage • 0 = true zero. Card positions remain unchanged.")
