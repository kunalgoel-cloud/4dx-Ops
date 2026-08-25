import streamlit as st
from src.validation import validate_upload
from src.mapping import get_unmapped_demo_items

st.set_page_config(page_title="Upload Data",page_icon="📤",layout="wide")
st.title("Upload Data")
st.caption("Each tab accepts one source type. Incorrect schemas are rejected before database writes.")
tabs=st.tabs(["Sales","Inventory","Sales Orders","PO","Invoice","Outward B2B","Tracking","Freight"])
sources=["sales","inventory","sales_orders","po","invoice","outward_b2b","tracking","freight"]
for tab,source in zip(tabs,sources):
    with tab:
        st.subheader(source.replace("_"," ").title())
        f=st.file_uploader("Upload Excel / CSV",type=["xlsx","xls","csv"],key=source)
        if f:
            r=validate_upload(f,source)
            if r["ok"]: st.success(f"Schema accepted: {r['rows']} rows. UX prototype does not write to DB yet.")
            else:
                st.error(r["message"])
                if r.get("missing"): st.write("Missing columns:",r["missing"])
st.divider()
st.subheader("New mappings detected")
items=get_unmapped_demo_items()
st.warning(f"{len(items)} new source values require mapping before official metrics.") if len(items) else st.success("No new mappings detected.")
st.dataframe(items,use_container_width=True,hide_index=True)
