import hashlib, io, os
import pandas as pd
import streamlit as st
from validation import validate_upload
from mapping import get_unmapped_items
from db import get_supabase_client, get_existing_uploads, create_upload_run, store_raw_rows

st.set_page_config(page_title='Data Intake',page_icon='📤',layout='wide')
st.title('Data Intake & Action Center')
st.caption('Upload → validate → detect duplicates → resolve mapping → confirm treatment → publish to production metrics')

SOURCE_SPECS={'Sales':('sales','Sales / B2C daily units'),'Inventory':('inventory','Stock and inventory value'),'Sales Orders':('sales_orders','Ordered quantity and order dates'),'PO':('po','Supplier PO and expected / actual receipt'),'Invoice':('invoice','Invoice / shipment identity; one invoice = one shipment'),'Outward B2B':('outward_b2b','B2B shipped quantity'),'Tracking':('tracking','Dispatch, delivery, city, courier'),'Freight':('freight','Billing / total shipment charges')}

client=get_supabase_client()
if 'production_ready' not in st.session_state: st.session_state['production_ready']=False
if 'production_uploads' not in st.session_state: st.session_state['production_uploads']={}
if 'mapping_decisions' not in st.session_state: st.session_state['mapping_decisions']={}

st.info('**Production mode rule:** demo data is used only until at least one valid production upload is accepted. No dummy values are mixed into production metrics.')

tabs=st.tabs(list(SOURCE_SPECS))
for tab,label in zip(tabs,SOURCE_SPECS):
    source,desc=SOURCE_SPECS[label]
    with tab:
        st.markdown(f'**{desc}**')
        date_override = None
        if source == 'sales':
            st.caption("If this export has no per-row date (e.g. a \"Sales by Item\" summary report), set the reporting month below. It is only used when the file itself has no Date column.")
            mcol, ycol = st.columns(2)
            months = ['January','February','March','April','May','June','July','August','September','October','November','December']
            today = pd.Timestamp.today()
            with mcol:
                sel_month = st.selectbox('Reporting month (used only if file has no Date column)', months, index=today.month-1, key=f'sales_month_{source}')
            with ycol:
                sel_year = st.number_input('Year', min_value=2020, max_value=2035, value=int(today.year), key=f'sales_year_{source}')
            date_override = pd.Timestamp(year=int(sel_year), month=months.index(sel_month)+1, day=1)
        f=st.file_uploader(f'Upload {label} file',type=['xlsx','xls','csv'],key=f'upload_{source}')
        if f:
            raw=f.getvalue(); sha=hashlib.sha256(raw).hexdigest()
            if sha in st.session_state.get('production_uploads',{}).values():
                st.warning('This exact file has already been accepted in this session. It will not be counted again.')
                continue
            prior=get_existing_uploads(client,source,sha)
            if prior:
                st.error('Duplicate file detected: this exact file was already uploaded to the production data store.')
                st.write(pd.DataFrame(prior)[['filename','status','uploaded_at','rows_received']])
                continue
            bio=io.BytesIO(raw); bio.name=f.name
            result=validate_upload(bio,source,date_override=date_override)
            if not result['ok']:
                if result.get('missing'):
                    st.error('File rejected — required identity fields are missing.')
                    st.write('Missing:',result.get('missing',[]))
                else:
                    st.error(f"File rejected — {result.get('message','could not process file')}.")
                continue
            st.success(f"✓ Schema accepted • {result['rows']:,} rows • SHA {sha[:12]}…")
            if source == 'sales' and result.get('date_injected'):
                st.warning(f"No Date column found in this file. All {result['rows']:,} rows have been stamped with {result['date_injected_value']} (1st of the selected reporting month). This is a monthly total assigned to a single date, not real daily sales — trailing 30-day / daily-trend metrics will show this whole period's volume on one day rather than spread across days. Prefer a daily-granularity export when one is available.")
            if source == 'inventory' and result.get('sku_identity_source') == 'title':
                st.warning("No SKU column found in this file — rows are identified by Product Title instead. This upload is accepted, but Title is not the same as a coded SKU: it will NOT automatically match SKUs from Sales, PO, or Invoice uploads until mapped. Review the mapping step before publishing to production metrics.")
            if source == 'invoice' and result.get('entity_count'):
                st.info(f"Invoice file recognised as a line-item export: {result['entity_count']:,} unique invoices across {result['rows']:,} rows. Repeated Invoice Number values are expected and will NOT be treated as duplicate uploads.")
            if result.get('exact_duplicate_rows'):
                st.warning(f"⚠ {result['exact_duplicate_rows']:,} exact duplicate rows detected. These can be excluded during treatment.")
            if result.get('business_duplicate_rows') and source != 'invoice':
                st.warning(f"⚠ {result['business_duplicate_rows']:,} rows share the source business key {result.get('business_key_columns')} — review before publishing.")
            st.session_state[f'preview_{source}']=result['preview']; st.session_state[f'result_{source}']=result; st.session_state[f'file_{source}']=f.name
            st.session_state['production_uploads'][source]=sha
            st.dataframe(result['preview'].head(25),use_container_width=True,hide_index=True)
            unmapped=get_unmapped_items(source,result['preview'],result.get('mapped',{}))
            if len(unmapped):
                st.subheader('New values requiring mapping')
                st.warning(f'{len(unmapped)} source values need review before publication.')
                for i,row in unmapped.iterrows():
                    a,b,c=st.columns([1,3,2]); a.write(f"**{row['Type']}**"); b.write(f"`{row['Source Value']}`")
                    c.selectbox('Treatment',['Map','Exclude','Use historic mapping'],key=f"map_action_{source}_{i}")
            if st.button('Accept this upload into production',key=f'accept_{source}',type='primary'):
                run=create_upload_run(client,source,f.name,sha,rows=result['rows'],status='accepted')
                stored=store_raw_rows(client,run['id'],result['preview']) if run else 0
                st.session_state['production_ready']=True
                st.session_state[f'accepted_{source}']=True
                st.success(f'Production upload accepted. {stored:,} raw rows stored.' if run else 'Production upload accepted for this session. Supabase credentials/table access are required for persistent storage.')

st.divider(); st.subheader('Upload actions & data quality')
accepted=[k for k in SOURCE_SPECS if st.session_state.get(f'accepted_{SOURCE_SPECS[k][0]}')]
if accepted: st.success('Accepted in this session: ' + ', '.join(accepted))
else: st.info('No production uploads accepted yet.')

for key in list(st.session_state):
    if key.startswith('result_'):
        source=key.replace('result_',''); r=st.session_state[key]
        if r.get('exact_duplicate_rows') or (r.get('business_duplicate_rows') and source != 'invoice'):
            st.warning(f"{source}: duplicate rows require review. Exact duplicates: {r.get('exact_duplicate_rows',0)}; business-key duplicates: {r.get('business_duplicate_rows',0)}.")
        if source == 'invoice' and r.get('business_duplicate_note'):
            st.caption('Invoice identity check: ' + r['business_duplicate_note'])

st.divider(); st.subheader('Metric calculation clock')
left,right=st.columns(2)
with left:
    st.date_input('Reporting period start',pd.Timestamp('2026-03-01'),key='period_start')
    st.date_input('Reporting period end',pd.Timestamp.today(),key='period_end')
with right:
    st.caption('MRR = trailing 30-day sales run rate using available uploaded daily sales. Missing days are shown as coverage gaps, never silently treated as zero.')
    st.caption('Supplier OTIF: blank Expected Delivery Date is excluded, as approved.')
