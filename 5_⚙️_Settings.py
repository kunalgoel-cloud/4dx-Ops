import streamlit as st
st.set_page_config(page_title="Settings",page_icon="⚙️",layout="wide")
st.title("Settings")
st.caption("Targets and metric rules will be database-backed in production.")
rows=[["Fulfillment %","≥",95,"%"],["OTIF %","≥",95,"%"],["Cost / Shipment","≤",400,"₹"],["Order → Delivery","≤",5,"days"],["Inventory Cover","range","15–45","days"],["Supplier OTIF %","≥",95,"%"]]
st.data_editor(rows,column_config={0:"Metric",1:"Direction",2:"Target",3:"Unit"},hide_index=True,use_container_width=True,num_rows="dynamic")
st.subheader("Metric rules")
for x in ["Shipment = one invoice","Fulfillment = shipped quantity / ordered quantity","Shipped quantity = Outward-B2B + Sales B2C matched to Sales Orders","DRR = units sold / calendar days represented; trailing 30-day DRR when 30+ days are available","Inventory Cover = individual units on hand / DRR","Supplier OTIF excludes POs with blank Expected Delivery Date","Multi-SKU shipment cost allocation = weight share"]: st.write("• "+x)
