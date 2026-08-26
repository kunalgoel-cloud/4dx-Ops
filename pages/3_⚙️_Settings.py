import streamlit as st
st.set_page_config(page_title='Settings',page_icon='⚙️',layout='wide')
st.title('4DX Settings & Definitions')
st.caption('Targets and metric definitions are configurable. Calculations remain deterministic and auditable.')

st.subheader('Metric targets')
settings=[('Fulfillment','95','%','Higher is better'),('OTIF','95','%','Higher is better'),('Cost / Shipment','400','INR','Lower is better'),('Order → Ship','5','days','Lower is better'),('Ship → Delivery','2','days','Lower is better'),('Order → Delivery','5','days','Lower is better'),('Supplier OTIF','95','%','Higher is better')]
for name,val,unit,direction in settings:
    a,b,c,d=st.columns([2,1,1,2])
    a.write(f'**{name}**'); b.number_input('Target',value=float(val),key=f't_{name}'); c.write(unit); d.write(direction)

st.divider()
st.subheader('Approved metric definitions')
st.code('''Shipment = one invoice number\nFulfillment = shipped quantity / ordered quantity\nShipped quantity = Outward B2B + Sales B2C reconstructed and matched to Sales Orders\nMRR = trailing 30-day sales run rate when data is uploaded\nInventory cover = stock units / daily run rate\nOrder → Ship = dispatch date − order date\nShip → Delivery = delivery date − dispatch date\nOrder → Delivery = delivery date − order date\nShipment cost = Total Charges (Billing)\nMulti-SKU cost allocation = chargeable-weight share\nSupplier OTIF = exclude POs where Expected Delivery Date is blank''',language='text')

st.divider()
st.subheader('4DX causal links')
links={'Fulfillment':['Inventory availability','Pending to Ship','Dispatch SLA','Supplier OTIF'],'Order → Delivery':['Order → Ship','Ship → Delivery'],'Order → Ship':['Pending to Ship','Dispatch SLA'],'Cost / Shipment':['Chargeable weight','Customer mix','City mix','SKU mix']}
for lag,leads in links.items(): st.write(f'**{lag} ←** ' + ' • '.join(leads))
