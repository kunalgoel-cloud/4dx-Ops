import streamlit as st
from demo_data import get_shipments, get_sku_supply

st.set_page_config(page_title='Drilldown',page_icon='📈',layout='wide')
st.title('Operational Drilldown')
st.caption('Ranked views identify where the metric gap is concentrated.')
df=get_shipments()
metric=st.selectbox('Metric',['Cost / Shipment','Cost / Invoice Value','Order → Ship','Ship → Delivery','Order → Delivery','Fulfillment'])
dim=st.selectbox('Dimension',['Customer','City','SKU'])
if metric=='Cost / Shipment':
    out=df.groupby(dim).agg(Shipments=('Invoice','count'),Cost_per_Shipment=('Cost','mean'),Total_Cost=('Cost','sum')).reset_index().sort_values('Cost_per_Shipment',ascending=False)
elif metric=='Cost / Invoice Value':
    out=df.groupby(dim).agg(Total_Cost=('Cost','sum'),Invoice_Value=('Invoice_Value','sum')).reset_index(); out['Cost_pct_Invoice']=out['Total_Cost']/out['Invoice_Value']*100; out=out.sort_values('Cost_pct_Invoice',ascending=False)
else:
    col={'Order → Ship':'Order_to_Ship','Ship → Delivery':'Ship_to_Delivery','Order → Delivery':'Order_to_Delivery','Fulfillment':'Fulfillment'}[metric]
    out=df.groupby(dim).agg(Shipments=('Invoice','count'),Metric=(col,'mean')).reset_index(); out=out.sort_values('Metric',ascending=(metric=='Fulfillment'))
    if metric=='Fulfillment': out['Metric']*=100
if 'Cost_per_Shipment' in out: st.dataframe(out.style.format({'Cost_per_Shipment':'₹{:,.0f}','Total_Cost':'₹{:,.0f}'}),use_container_width=True,hide_index=True)
elif 'Cost_pct_Invoice' in out: st.dataframe(out.style.format({'Total_Cost':'₹{:,.0f}','Invoice_Value':'₹{:,.0f}','Cost_pct_Invoice':'{:.1f}%'}),use_container_width=True,hide_index=True)
else: st.dataframe(out.style.format({'Metric':'{:.1f}%'} if metric=='Fulfillment' else {'Metric':'{:.1f} d'}),use_container_width=True,hide_index=True)

st.divider(); st.subheader('SKU supply performance')
st.caption('Supplier material lead time through final delivery and supply cost.')
sku=get_sku_supply()
st.dataframe(sku.style.format({'Material_Lead_Time':'{:.1f} d','Order_to_Ship':'{:.1f} d','Ship_to_Delivery':'{:.1f} d','Order_to_Delivery':'{:.1f} d','Cost_per_Shipment':'₹{:,.0f}','Invoice_Value':'₹{:,.0f}','Cost_pct_Invoice':'{:.1f}%'}),use_container_width=True,hide_index=True)

st.divider(); st.subheader('Shipment-level calculation evidence')
st.caption('Invoice date, ship date and delivery date are retained explicitly for auditability.')
st.dataframe(df,use_container_width=True,hide_index=True)
