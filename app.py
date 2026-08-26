import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from demo_data import get_demo_metrics, get_shipments, get_quality

st.set_page_config(page_title='Operations 4DX', page_icon='📊', layout='wide')

st.markdown('''
<style>
.block-container{padding-top:1rem;padding-bottom:2rem;max-width:1500px}
.metric-card{border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;background:#fff;min-height:150px}
.small{font-size:12px;color:#6b7280}.gap{font-weight:700}.section{margin-top:8px}
[data-testid="stMetricValue"]{font-size:1.8rem}
</style>
''', unsafe_allow_html=True)

m = get_demo_metrics()
ship = get_shipments()

st.title('Operations 4DX')
st.caption('Operating cockpit • deterministic metric engine in Phase 1 • Gemini ASK AI reserved for Phase 2')

c1,c2,c3,c4 = st.columns([1.2,1.2,1.2,1.2])
with c1: st.info('**Period**\n\n01 Aug → 26 Aug 2026')
with c2: st.info('**Data freshness**\n\n26 Aug 2026 • 09:30')
with c3: st.info('**Data coverage**\n\n18 / 30 days • 60% sales coverage')
with c4: st.warning('**Exceptions**\n\n27 requiring action')

st.subheader('Lag metrics')
metric_keys = ['fulfillment','otif','cost','order_to_ship','ship_to_delivery','delivery']
cols = st.columns(3)
for col,key in zip(cols*2, metric_keys):
    x=m[key]
    with col:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(x['name'], x['value'], x['delta'], delta_color='inverse' if x['bad'] else 'normal')
        st.caption(f"Target: {x['target']} • {x['window']} • Coverage: {x['coverage']}")
        if st.button('View calculation data →', key=f'view_{key}', use_container_width=True):
            st.session_state['selected_metric'] = key
        st.markdown('</div>', unsafe_allow_html=True)

selected = st.session_state.get('selected_metric')
if selected:
    st.divider()
    x=m[selected]
    st.subheader(f"Calculation data — {x['name']}")
    st.caption(f"Formula: {x['formula']} • Window: {x['window']} • Coverage: {x['coverage']}")
    st.dataframe(x['data'], use_container_width=True, hide_index=True)
    if st.button('Close calculation data', key='close_calc'):
        st.session_state.pop('selected_metric', None)
        st.rerun()

st.divider()
st.subheader('Metric trends vs target')
trend_tabs = st.tabs(['Fulfillment','OTIF','Cost / Shipment','Order → Ship','Ship → Delivery','Order → Delivery'])
for tab,key in zip(trend_tabs, metric_keys):
    with tab:
        x=m[key]
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=x['trend']['Date'], y=x['trend']['Actual'], mode='lines+markers', name='Actual'))
        fig.add_trace(go.Scatter(x=x['trend']['Date'], y=x['trend']['Target'], mode='lines', name='Target', line=dict(dash='dash')))
        fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), legend=dict(orientation='h'))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{x['name']} • {x['window']} • target {x['target']}")

st.divider()
st.subheader('Lead → Lag connection')
lead_cols=st.columns(3)
for col,x in zip(lead_cols,m['lead_measures']):
    with col:
        st.markdown(f"**{x['name']}**")
        st.metric('Current',x['value'],x['delta'],delta_color='inverse' if x['bad'] else 'normal')
        st.caption(f"Target: {x['target']}")
        st.progress(min(max(x['progress'],0),1))
        st.caption(f"Primary lag affected: **{x['lag']}**")

st.markdown('''
**How to read this:** the lag metric tells us *what outcome is off target*. Lead measures tell the team *which controllable operating behaviour is moving that outcome*. The Phase 1 engine will quantify contribution from the available data; Gemini in Phase 2 will explain the pattern and recommend actions.
''')

st.divider()
st.subheader('Where is the problem?')
rank_tabs=st.tabs(['Customers','Cities','SKUs'])
for tab,dim in zip(rank_tabs,['Customer','City','SKU']):
    with tab:
        df=ship.groupby(dim).agg(Shipments=('Invoice','count'),Cost_per_Shipment=('Cost','mean'),Order_to_Ship=('Order_to_Ship','mean'),Ship_to_Delivery=('Ship_to_Delivery','mean'),Fulfillment=('Fulfillment','mean')).reset_index()
        df['Fulfillment']=df['Fulfillment']*100
        df=df.sort_values(['Cost_per_Shipment','Order_to_Ship'],ascending=False)
        st.dataframe(df.style.format({'Cost_per_Shipment':'₹{:,.0f}','Order_to_Ship':'{:.1f} d','Ship_to_Delivery':'{:.1f} d','Fulfillment':'{:.1f}%'}),use_container_width=True,hide_index=True)

st.divider()
st.subheader('Data & action center')
q=get_quality()
q1,q2=st.columns([3,1])
with q1:
    st.dataframe(q,use_container_width=True,hide_index=True)
with q2:
    st.warning('27 exceptions')
    st.page_link('pages/1_📤_Upload_Data.py', label='Open Data Intake →')
    st.page_link('pages/3_⚙️_Settings.py', label='Open Settings →')

st.caption('— unavailable • ⚠ incomplete coverage • 0 true zero. Metric card positions remain unchanged when data is unavailable.')
