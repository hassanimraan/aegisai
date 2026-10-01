import streamlit as st

st.title("📊 AegisAI Dashboard")

st.write("Approval cases dashboard will appear here.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Cases", "0")

with col2:
    st.metric("Pending", "0")

with col3:
    st.metric("Approved", "0")

with col4:
    st.metric("Returned", "0")
