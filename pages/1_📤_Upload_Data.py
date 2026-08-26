import hashlib
import io
import pandas as pd
import streamlit as st
from validation import validate_upload
from mapping import get_unmapped_demo_items

st.set_page_config(page_title='Data Intake',page_icon='📤',layout='wide')
st.title('Data Intake & Exceptions')
st.caption('Upload → validate → resolve exceptions → confirm treatment → calculate official metrics')

SOURCE_SPECS={
 'Sales':('sales','Sales / B2C daily units'),
 'Inventory':('inventory','Stock and inventory value'),
 'Sales Orders':('sales_orders','Ordered quantity and order dates'),
 'PO':('po','Supplier PO and expected / actual receipt'),
 'Invoice':('invoice','Invoice / shipment identity; one invoice = one shipment'),
 'Outward B2B':('outward_b2b','B2B shipped quantity'),
 'Tracking':('tracking','Dispatch, delivery, city, courier'),
 'Freight':('freight','Billing / total shipment charges')}

tabs=st.tabs(list(SOURCE_SPECS))
for tab,label in zip(tabs,SOURCE_SPECS):
    source,desc=SOURCE_SPECS[label]
    with tab:
        st.markdown(f'**{desc}**')
        f=st.file_uploader(f'Upload {label} file',type=['xlsx','xls','csv'],key=f'upload_{source}')
        if f:
            raw=f.getvalue(); sha=hashlib.sha256(raw).hexdigest()
            result=validate_upload(io.BytesIO(raw),source)
            if result['ok']:
                st.success(f'✓ Schema accepted • {result["rows"]:,} rows • SHA {sha[:12]}…')
                st.session_state[f'preview_{source}']=result.get('preview')
                st.session_state[f'file_{source}']=f.name
                st.caption('No official metric is updated until all exceptions below are resolved or explicitly treated.')
                if result.get('preview') is not None: st.dataframe(result['preview'].head(25),use_container_width=True,hide_index=True)
            else:
                st.error('File rejected — schema does not match the selected source type.')
                if result.get('missing'): st.write('Missing required columns:',result['missing'])
                if result.get('extra'): st.write('Unexpected columns:',result['extra'])

st.divider()
st.subheader('Exceptions requiring a decision')
items=get_unmapped_demo_items()
if len(items):
    st.warning(f'{len(items)} new source values require explicit treatment before they enter official metrics.')
    for i,row in items.iterrows():
        with st.container(border=True):
            a,b,c,d=st.columns([1.3,2.2,2.2,1.2])
            a.write(f"**{row['Type']}**")
            b.write(f"Source: `{row['Source Value']}`")
            action=c.selectbox('Treatment', ['Map to standard value','Exclude from official metrics','Assume from historic mapping'],key=f'action_{i}')
            d.button('Save',key=f'save_{i}',type='primary')
            if action=='Map to standard value':
                st.selectbox('Standard value',['MN-SAB-100','MN-PPOHA-100','MN-FARALI-37','BigBasket','Bangalore','Gurugram'],key=f'map_{i}')
                st.number_input('Conversion factor',min_value=0.0001,value=1.0,key=f'conv_{i}')
                st.selectbox('Unit',['Individual units','Bundle','Master carton'],key=f'unit_{i}')
else: st.success('No mapping exceptions detected.')

st.divider()
st.subheader('Treatment policy')
policy=st.radio('For unresolved records, official metrics should:', ['Exclude them and show the coverage impact','Use an approved historic value','Hold calculation until resolved'],horizontal=True)
st.session_state['unresolved_policy']=policy
st.info('Every decision will be written to the data-quality audit trail in Supabase in the production implementation.')

st.divider()
st.subheader('Metric calculation clock')
left,right=st.columns(2)
with left:
    st.date_input('Reporting period start',pd.Timestamp('2026-08-01'))
    st.date_input('Reporting period end',pd.Timestamp('2026-08-26'))
with right:
    st.caption('Sales / MRR: trailing 30-day run rate using available uploaded daily sales. Coverage is shown explicitly; missing days are never silently treated as zero.')
    st.caption('Supplier OTIF: blank Expected Delivery Date is excluded, as approved.')
