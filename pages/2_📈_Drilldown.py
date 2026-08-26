import streamlit as st
from demo_data import get_shipments

st.set_page_config(page_title='Drilldown',page_icon='📈',layout='wide')
st.title('Operational Drilldown')
st.caption('Ranked views identify where the metric gap is concentrated. Sort by contribution to the problem.')
df=get_shipments()
metric=st.selectbox('Metric',['Cost / Shipment','Order → Ship','Ship → Delivery','Fulfillment'])
dim=st.selectbox('Dimension',['Customer','City','SKU'])
if metric=='Cost / Shipment':
    out=df.groupby(dim).agg(Shipments=('Invoice','count'),Cost_per_Shipment=('Cost','mean'),Total_Cost=('Cost','sum')).reset_index().sort_values('Cost_per_Shipment',ascending=False)
elif metric=='Order → Ship':
    out=df.groupby(dim).agg(Shipments=('Invoice','count'),Avg_Days=('Order_to_Ship','mean')).reset_index().sort_values('Avg_Days',ascending=False)
elif metric=='Ship → Delivery':
    out=df.groupby(dim).agg(Shipments=('Invoice','count'),Avg_Days=('Ship_to_Delivery','mean')).reset_index().sort_values('Avg_Days',ascending=False)
else:
    out=df.groupby(dim).agg(Orders=('Invoice','count'),Fulfillment=('Fulfillment','mean')).reset_index().sort_values('Fulfillment')
if 'Cost_per_Shipment' in out: st.dataframe(out.style.format({'Cost_per_Shipment':'₹{:,.0f}','Total_Cost':'₹{:,.0f}'}),use_container_width=True,hide_index=True)
elif 'Avg_Days' in out: st.dataframe(out.style.format({'Avg_Days':'{:.1f} d'}),use_container_width=True,hide_index=True)
else:
    out['Fulfillment']=out['Fulfillment']*100
    st.dataframe(out.style.format({'Fulfillment':'{:.1f}%'}),use_container_width=True,hide_index=True)
st.divider()
st.subheader('Shipment-level evidence')
st.dataframe(df,use_container_width=True,hide_index=True)
