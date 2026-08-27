import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from demo_data import get_demo_metrics, get_shipments
from db import get_supabase_client

st.set_page_config(page_title='Operations 4DX', page_icon='📊', layout='wide')
st.markdown('''<style>.block-container{padding-top:1rem;padding-bottom:2rem;max-width:1500px}.metric-card{border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;background:#fff;min-height:145px}[data-testid="stMetricValue"]{font-size:1.8rem}</style>''', unsafe_allow_html=True)

# Production data is never mixed with demo data. The intake page sets this flag
# after an accepted upload; persistent upload_runs can also be used when Supabase is connected.
production = bool(st.session_state.get('production_ready', False))
client = get_supabase_client()
if not production and client:
    try:
        rows = client.table('upload_runs').select('id').eq('status','accepted').limit(1).execute().data
        production = bool(rows)
    except Exception:
        pass

st.title('Operations 4DX')
if production:
    st.success('🟢 **Production data mode** — dashboard will not use demo values.')
    m = {k: {'name': n, 'value':'—', 'delta':None, 'bad':False, 'target':'Configured in Settings', 'window':'Awaiting production calculation engine', 'coverage':'—', 'formula':'Production source data', 'data':pd.DataFrame(), 'trend':pd.DataFrame(columns=['Date','Actual','Target'])} for k,n in {
        'fulfillment':'Fulfillment','otif':'OTIF','avg_invoice':'Average Invoice Value','cost':'Cost / Shipment','cost_pct':'Cost / Invoice Value','order_to_ship':'Order → Ship','ship_to_delivery':'Ship → Delivery','delivery':'Order → Delivery','material_lead_time':'Material Lead Time'}.items()}
    ship = pd.DataFrame()
    st.caption('Real uploads are accepted and stored/staged, but a metric is shown as unavailable until the corresponding source data is successfully reconciled. No dummy values are substituted.')
else:
    st.info('🟡 **Demo / Preview mode** — upload valid production data from **Data Intake** to switch automatically to production.')
    m = get_demo_metrics(); ship = get_shipments()

c1,c2,c3,c4=st.columns(4)
with c1: st.info('**Reporting period**\n\n' + ('Production upload period' if production else '01 Aug → 26 Aug 2026'))
with c2: st.info('**Data freshness**\n\n' + ('Production data' if production else '26 Aug 2026 • 09:30'))
with c3: st.info('**Coverage**\n\n' + ('—' if production else '10 / 10 shipment records'))
with c4: st.warning('**Exceptions**\n\nReview in Data Intake')

metric_keys=['fulfillment','otif','avg_invoice','cost','cost_pct','order_to_ship','ship_to_delivery','delivery','material_lead_time']

def safe_metric(key):
    return m.get(key, {'name':key.replace('_',' ').title(),'value':'—','delta':None,'bad':False,'target':'—','window':'Data unavailable','coverage':'—','formula':'Source data unavailable','data':pd.DataFrame(),'trend':pd.DataFrame(columns=['Date','Actual','Target'])})

st.subheader('Lag metrics')
cols=st.columns(3)
for col,key in zip(cols*3,metric_keys):
    x=safe_metric(key)
    with col:
        st.markdown('<div class="metric-card">',unsafe_allow_html=True)
        st.metric(x['name'],x['value'],x.get('delta'),delta_color='inverse' if x.get('bad') else 'normal')
        st.caption(f"Target: {x.get('target','—')} • {x.get('window','—')} • Coverage: {x.get('coverage','—')}")
        if st.button('View calculation data →',key=f'view_{key}',use_container_width=True): st.session_state['selected_metric']=key
        st.markdown('</div>',unsafe_allow_html=True)

selected=st.session_state.get('selected_metric')
if selected:
    x=safe_metric(selected); st.divider(); st.subheader(f"Calculation data — {x['name']}")
    st.caption(f"Formula: {x.get('formula','—')} • Window: {x.get('window','—')} • Coverage: {x.get('coverage','—')}")
    if getattr(x.get('data'), 'empty', True): st.info('Calculation data is unavailable for this metric in the current production dataset.')
    else: st.dataframe(x['data'],use_container_width=True,hide_index=True)
    if st.button('Close calculation data',key='close_calc'): st.session_state.pop('selected_metric',None); st.rerun()

st.divider(); st.subheader('Metric trends vs target')
trend_tabs=st.tabs([safe_metric(k)['name'] for k in metric_keys])
for tab,key in zip(trend_tabs,metric_keys):
    with tab:
        x=safe_metric(key); trend=x.get('trend')
        if not isinstance(trend,pd.DataFrame) or trend.empty or not {'Date','Actual','Target'}.issubset(trend.columns): st.info('Trend unavailable until sufficient production time-series data is reconciled.')
        else:
            fig=go.Figure(); fig.add_trace(go.Scatter(x=trend['Date'],y=trend['Actual'],mode='lines+markers',name='Actual')); fig.add_trace(go.Scatter(x=trend['Date'],y=trend['Target'],mode='lines',name='Target',line=dict(dash='dash'))); fig.update_layout(height=280,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation='h')); st.plotly_chart(fig,use_container_width=True)
        st.caption(f"{x['name']} • {x.get('window','—')} • target {x.get('target','—')}")

st.divider(); st.subheader('Lead → Lag connection')
leads=m.get('lead_measures',[]) if not production else []
if leads:
    for col,x in zip(st.columns(min(4,len(leads))),leads):
        with col: st.markdown(f"**{x['name']}**"); st.metric('Current',x['value'],x.get('delta'),delta_color='inverse' if x.get('bad') else 'normal'); st.caption(f"Target: {x.get('target','—')} • Primary lag affected: **{x.get('lag','—')}**"); st.progress(min(max(x.get('progress',0),0),1))
else: st.info('Lead-measure production trend will populate after real source data is reconciled.')

st.divider(); st.subheader('Where is the problem?')
if ship.empty: st.info('Customer / City / SKU drilldown will populate from reconciled production shipments.')
else:
    for tab,dim in zip(st.tabs(['Customers','Cities','SKUs']),['Customer','City','SKU']):
        with tab:
            df=ship.groupby(dim).agg(Shipments=('Invoice','count'),Cost_per_Shipment=('Cost','mean'),Total_Cost=('Cost','sum'),Invoice_Value=('Invoice_Value','sum')).reset_index(); df['Cost_pct_Invoice']=df['Total_Cost']/df['Invoice_Value']*100; t=ship.groupby(dim).agg(Order_to_Ship=('Order_to_Ship','mean'),Ship_to_Delivery=('Ship_to_Delivery','mean'),Fulfillment=('Fulfillment','mean')).reset_index(); df=df.merge(t,on=dim); df['Fulfillment']*=100; df=df.sort_values(['Cost_per_Shipment','Order_to_Ship'],ascending=False); st.dataframe(df,use_container_width=True,hide_index=True)

st.divider(); st.subheader('SKU supply performance')
if production: st.info('SKU supply performance will populate once PO, shipment and freight sources are reconciled.')
else: st.dataframe(m['sku_supply'],use_container_width=True,hide_index=True)
st.info('**4DX logic:** lead measures are controllable drivers; lag measures show the resulting fulfillment, delivery and cost outcomes. Production mode never backfills missing values with demo data.')
st.caption('— unavailable • ⚠ incomplete coverage • 0 true zero. Card positions remain unchanged when data is unavailable.')
