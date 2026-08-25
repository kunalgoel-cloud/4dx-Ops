import streamlit as st
from src.mapping import get_unmapped_demo_items
st.set_page_config(page_title="Mapping Center",page_icon="🗺️",layout="wide")
st.title("Mapping Center")
st.caption("New source values must be mapped explicitly; the system never guesses them into official metrics.")
x=get_unmapped_demo_items(); st.warning("Action required: new source values detected.") if len(x) else st.success("No mapping actions required.")
st.dataframe(x,use_container_width=True,hide_index=True)
if len(x):
    st.selectbox("Source value",x["Source Value"].tolist())
    st.selectbox("Standard value",["MN-SAB-100","MN-PPOHA-100","MN-FARALI-37","BigBasket","Bangalore"])
    st.number_input("Conversion factor",min_value=.0001,value=1.0)
    st.selectbox("Unit",["Individual units","Bundle","Master carton"])
    st.button("Save mapping",type="primary",use_container_width=True)
