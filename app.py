import streamlit as st
import plotly.graph_objects as go
from demo_data import get_demo_metrics, get_shipments

st.set_page_config(page_title='Operations 4DX', page_icon='📊', layout='wide')
st.markdown('''<style>.block-container{padding-top:1rem;padding-bottom:2rem;max-width:1500px}.metric-card{border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;background:#fff;min-height:145px}.small{font-size:12px;color:#6b7280}[data-testid="stMetricValue"]{font-size:1.8rem}</style>''', unsafe_allow_html=True)

m=get_demo_metrics(); ship=get_shipments()
st.title('Operations 4DX')
st.caption('Operating cockpit • Phase 1 deterministic metric engine • Gemini ASK AI reserved for Phase 2')

c1,c2,c3,c4=st.columns(4)
with c1: st.info('**Reporting period**\n\n01 Aug → 26 Aug 2026')
with c2: st.info('**Data freshness**\n\n26 Aug 2026 • 09:30')
with c3: st.info('**Coverage**\n\n10 / 10 shipment records')
with c4: st.warning('**Exceptions**\n\n27 requiring action → Data Intake')

st.subheader('Lag metrics')
metric_keys=['fulfillment','otif','avg_invoice','cost','cost_pct','order_to_ship','ship_to_delivery','delivery','material_lead_time']
cols=st.columns(3)
for col,key in zip(cols*3,metric_keys):
    x=m.get(key, {'name': key.replace('_',' ').title(), 'value': '—', 'delta': None, 'bad': False, 'target': '—', 'window': 'Data unavailable', 'coverage': '—', 'formula': 'Source data unavailable', 'data': __import__('pandas').DataFrame(), 'trend': __import__('pandas').DataFrame(columns=['Date','Actual','Target'])})
    with col:
        st.markdown('<div class="metric-card">',unsafe_allow_html=True)
        st.metric(x['name'],x['value'],x['delta'],delta_color='inverse' if x['bad'] else 'normal')
        st.caption(f"Target: {x['target']} • {x['window']} • Coverage: {x['coverage']}")
        if st.button('View calculation data →',key=f'view_{key}',use_container_width=True): st.session_state['selected_metric']=key
        st.markdown('</div>',unsafe_allow_html=True)

selected=st.session_state.get('selected_metric')
if selected:
    st.divider(); x=m[selected]
    st.subheader(f"Calculation data — {x['name']}")
    st.caption(f"Formula: {x['formula']} • Window: {x['window']} • Coverage: {x['coverage']}")
    st.dataframe(x['data'],use_container_width=True,hide_index=True)
    if st.button('Close calculation data',key='close_calc'):
        st.session_state.pop('selected_metric',None); st.rerun()

st.divider(); st.subheader('Metric trends vs target')
trend_tabs=st.tabs([m[k]['name'] for k in metric_keys])
for tab,key in zip(trend_tabs,metric_keys):
    with tab:
        x=m.get(key, {'name': key.replace('_',' ').title(), 'value': '—', 'delta': None, 'bad': False, 'target': '—', 'window': 'Data unavailable', 'coverage': '—', 'formula': 'Source data unavailable', 'data': __import__('pandas').DataFrame(), 'trend': __import__('pandas').DataFrame(columns=['Date','Actual','Target'])}); fig=go.Figure()
        fig.add_trace(go.Scatter(x=x['trend']['Date'],y=x['trend']['Actual'],mode='lines+markers',name='Actual'))
        fig.add_trace(go.Scatter(x=x['trend']['Date'],y=x['trend']['Target'],mode='lines',name='Target',line=dict(dash='dash')))
        fig.update_layout(height=280,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation='h'))
        st.plotly_chart(fig,use_container_width=True)
        st.caption(f"{x['name']} • {x['window']} • target {x['target']}")

st.divider(); st.subheader('Lead → Lag connection')
lead_cols=st.columns(4)
for col,x in zip(lead_cols,m['lead_measures']):
    with col:
        st.markdown(f"**{x['name']}**")
        st.metric('Current',x['value'],x['delta'],delta_color='inverse' if x['bad'] else 'normal')
        st.caption(f"Target: {x['target']}"); st.progress(min(max(x['progress'],0),1)); st.caption(f"Primary lag affected: **{x['lag']}**")

st.divider(); st.subheader('Where is the problem?')
rank_tabs=st.tabs(['Customers','Cities','SKUs'])
for tab,dim in zip(rank_tabs,['Customer','City','SKU']):
    with tab:
        df=ship.groupby(dim).agg(Shipments=('Invoice','count'),Cost_per_Shipment=('Cost','mean'),Cost_pct_Invoice=('Cost','sum')).reset_index()
        inv=ship.groupby(dim)['Invoice_Value'].sum().reset_index(name='Invoice_Value'); df=df.merge(inv,on=dim); df['Cost_pct_Invoice']=df['Cost_pct_Invoice']/df['Invoice_Value']*100
        timing=ship.groupby(dim).agg(Order_to_Ship=('Order_to_Ship','mean'),Ship_to_Delivery=('Ship_to_Delivery','mean'),Fulfillment=('Fulfillment','mean')).reset_index(); df=df.merge(timing,on=dim); df['Fulfillment']*=100
        df=df.sort_values(['Cost_per_Shipment','Order_to_Ship'],ascending=False)
        st.dataframe(df.style.format({'Cost_per_Shipment':'₹{:,.0f}','Cost_pct_Invoice':'{:.1f}%','Order_to_Ship':'{:.1f} d','Ship_to_Delivery':'{:.1f} d','Fulfillment':'{:.1f}%'}),use_container_width=True,hide_index=True)

st.divider(); st.subheader('SKU supply performance')
st.caption('End-to-end SKU view: material lead time → order to ship → ship to delivery → total delivery → supply cost.')
sku=m['sku_supply'].copy().sort_values(['Material_Lead_Time','Order_to_Delivery'],ascending=False)
st.dataframe(sku.style.format({'Material_Lead_Time':'{:.1f} d','Order_to_Ship':'{:.1f} d','Ship_to_Delivery':'{:.1f} d','Order_to_Delivery':'{:.1f} d','Cost_per_Shipment':'₹{:,.0f}','Invoice_Value':'₹{:,.0f}','Cost_pct_Invoice':'{:.1f}%'}),use_container_width=True,hide_index=True)

st.info('**4DX logic:** material lead time and operating lead measures are controllable drivers. Lag measures show the resulting fulfillment, delivery and cost outcome. The Phase 1 engine calculates the evidence; Gemini in Phase 2 will interpret contribution and recommend actions.')
st.caption('— unavailable • ⚠ incomplete coverage • 0 true zero. Metric card positions remain unchanged when data is unavailable.')
