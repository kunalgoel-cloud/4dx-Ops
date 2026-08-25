import streamlit as st
from demo_data import get_shipments
st.set_page_config(page_title="Drilldown",page_icon="📈",layout="wide")
st.title("Operations Drill-down")
df=get_shipments()
c1,c2,c3,c4=st.columns(4)
customer=c1.multiselect("Customer",sorted(df.Customer.unique()))
city=c2.multiselect("City",sorted(df.City.unique()))
sku=c3.multiselect("SKU",sorted(df.SKU.unique()))
metric=c4.selectbox("View",["Cost","Delivery time","Fulfillment"])
f=df.copy()
if customer:f=f[f.Customer.isin(customer)]
if city:f=f[f.City.isin(city)]
if sku:f=f[f.SKU.isin(sku)]
if metric=="Cost":
    a,b,c,d=st.columns(4); a.metric("Cost / shipment",f"₹{f.Cost.mean():,.0f}"); b.metric("Cost / kg",f"₹{f.Cost.sum()/f.Weight.sum():,.1f}"); c.metric("Shipments",len(f)); d.metric("Coverage","100%")
    st.bar_chart(f.groupby("Customer").Cost.mean().sort_values(ascending=False))
elif metric=="Delivery time":
    a,b,c,d=st.columns(4); a.metric("Order → Delivery",f"{f.Order_to_Delivery.mean():.1f} d"); b.metric("Order → Ship",f"{f.Order_to_Ship.mean():.1f} d"); c.metric("Ship → Delivery",f"{f.Ship_to_Delivery.mean():.1f} d"); d.metric("OTIF",f"{100*f.OTIF.mean():.0f}%")
    st.bar_chart(f.groupby("City").Ship_to_Delivery.mean().sort_values(ascending=False))
else:
    a,b,c=st.columns(3); a.metric("Fulfillment",f"{100*f.Shipped.sum()/f.Ordered.sum():.1f}%"); b.metric("Ordered",f"{f.Ordered.sum():,.0f}"); c.metric("Shipped",f"{f.Shipped.sum():,.0f}")
    st.dataframe(f,use_container_width=True,hide_index=True)
st.divider(); st.caption("Planned drill path: Company → Customer → SKU → City → Invoice. ASK AI comes in Phase 2.")
