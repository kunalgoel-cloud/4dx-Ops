import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from db import get_supabase_client

st.set_page_config(page_title='Operations 4DX', page_icon='📊', layout='wide')
st.markdown('''<style>.block-container{padding-top:1rem;padding-bottom:2rem;max-width:1500px}.metric-card{border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;background:#fff;min-height:145px}[data-testid="stMetricValue"]{font-size:1.8rem}</style>''', unsafe_allow_html=True)

# IMPORTANT: Production-only dashboard.
# Demo data is intentionally NOT imported or used here. Until the production
# metric engine has enough accepted/reconciled data, metrics remain unavailable.
client = get_supabase_client()
production_uploads = []
if client:
    try:
        rows = client.table('upload_runs').select('source_type,filename,status,rows_received,reporting_period_start,reporting_period_end,uploaded_at').eq('status','accepted').order('uploaded_at', desc=True).limit(100).execute().data
        production_uploads = rows or []
    except Exception:
        production_uploads = []

session_accepted = st.session_state.get('production_uploads', {})
production = bool(production_uploads or session_accepted)

metric_defs = {
    'fulfillment':'Fulfillment',
    'otif':'OTIF',
    'avg_invoice':'Average Invoice Value',
    'cost':'Cost / Shipment',
    'cost_pct':'Cost / Invoice Value',
    'order_to_ship':'Order → Ship',
    'ship_to_delivery':'Ship → Delivery',
    'delivery':'Order → Delivery',
    'material_lead_time':'Material Lead Time',
}


def unavailable(name, reason='Production metric calculation is not yet available'):
    return {
        'name': name, 'value': '—', 'delta': None, 'bad': False,
        'target': 'Configured in Settings', 'window': '—', 'coverage': '—',
        'formula': reason, 'data': pd.DataFrame(),
        'trend': pd.DataFrame(columns=['Date','Actual','Target'])
    }

m = {k: unavailable(v) for k, v in metric_defs.items()}

# There is deliberately no demo fallback. The production metric engine will
# populate m from reconciled source data in the next stage.

st.title('Operations 4DX')
if production:
    st.success('🟢 **Production data detected** — no demo data is used on this dashboard.')
    st.caption('Accepted production uploads are available. Metrics remain unavailable until the relevant source records are reconciled and the official calculation is complete.')
else:
    st.info('⚪ **No production data available** — upload valid source data from **Data Intake** to populate the dashboard. Demo data is disabled.')
    st.caption('This dashboard intentionally shows no dummy business metrics. Missing metrics remain unavailable until real data is accepted.')

# Derive the reporting period only from accepted production uploads when possible.
period_start = None
period_end = None
freshness = None
if production_uploads:
    starts = [r.get('reporting_period_start') for r in production_uploads if r.get('reporting_period_start')]
    ends = [r.get('reporting_period_end') for r in production_uploads if r.get('reporting_period_end')]
    uploaded = [r.get('uploaded_at') for r in production_uploads if r.get('uploaded_at')]
    if starts: period_start = min(starts)
    if ends: period_end = max(ends)
    if uploaded: freshness = max(uploaded)

c1,c2,c3,c4=st.columns(4)
with c1: st.info('**Reporting period**\n\n' + (f'{period_start} → {period_end}' if period_start and period_end else '—'))
with c2: st.info('**Data freshness**\n\n' + (str(freshness) if freshness else '—'))
with c3: st.info('**Accepted uploads**\n\n' + (str(len(production_uploads) or len(session_accepted)) if production else '0'))
with c4:
    st.warning('**Exceptions**\n\nReview in Data Intake')

metric_keys=list(metric_defs)
st.subheader('Lag metrics')
cols=st.columns(3)
for col,key in zip(cols*3,metric_keys):
    x=m[key]
    with col:
        st.markdown('<div class="metric-card">',unsafe_allow_html=True)
        st.metric(x['name'],x['value'],x.get('delta'),delta_color='inverse' if x.get('bad') else 'normal')
        st.caption(f"Target: {x.get('target','—')} • {x.get('window','—')} • Coverage: {x.get('coverage','—')}")
        if st.button('View calculation data →',key=f'view_{key}',use_container_width=True): st.session_state['selected_metric']=key
        st.markdown('</div>',unsafe_allow_html=True)

selected=st.session_state.get('selected_metric')
if selected:
    x=m.get(selected, unavailable(selected.replace('_',' ').title()))
    st.divider(); st.subheader(f"Calculation data — {x['name']}")
    st.caption(f"Formula: {x.get('formula','—')} • Window: {x.get('window','—')} • Coverage: {x.get('coverage','—')}")
    if x.get('data') is None or x['data'].empty:
        st.info('Calculation evidence is unavailable because the corresponding production data has not yet been reconciled.')
    else:
        st.dataframe(x['data'],use_container_width=True,hide_index=True)
    if st.button('Close calculation data',key='close_calc'):
        st.session_state.pop('selected_metric',None); st.rerun()

st.divider(); st.subheader('Metric trends vs target')
trend_tabs=st.tabs([m[k]['name'] for k in metric_keys])
for tab,key in zip(trend_tabs,metric_keys):
    with tab:
        x=m[key]; trend=x.get('trend')
        if not isinstance(trend,pd.DataFrame) or trend.empty or not {'Date','Actual','Target'}.issubset(trend.columns):
            st.info('Trend unavailable until sufficient production time-series data is reconciled.')
        else:
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=trend['Date'],y=trend['Actual'],mode='lines+markers',name='Actual'))
            fig.add_trace(go.Scatter(x=trend['Date'],y=trend['Target'],mode='lines',name='Target',line=dict(dash='dash')))
            fig.update_layout(height=280,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation='h'))
            st.plotly_chart(fig,use_container_width=True)
        st.caption(f"{x['name']} • {x.get('window','—')} • target {x.get('target','—')}")

st.divider(); st.subheader('Lead → Lag connection')
st.info('Lead-measure production trends will populate after the underlying operational data is reconciled. No demo lead measures are shown.')

st.divider(); st.subheader('Where is the problem?')
st.info('Customer / City / SKU action tables will populate from reconciled production shipment data. No dummy rankings are shown.')

st.divider(); st.subheader('SKU supply performance')
st.info('SKU supply performance will populate once PO, shipment and freight sources are reconciled.')

st.info('**4DX logic:** lead measures are controllable drivers; lag measures show the resulting fulfillment, delivery and cost outcomes. Production mode never backfills missing values with demo data.')
st.caption('— unavailable • ⚠ incomplete coverage • 0 true zero. Card positions remain unchanged when data is unavailable.')
