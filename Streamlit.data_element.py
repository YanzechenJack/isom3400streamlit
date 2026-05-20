import streamlit as st
import pandas as pd

data = {'Product': ['A', 'B', 'C'], 
        'Sales': [1200, 850, 950], 
        'Customers': [300, 400, 350]}

df = pd.DataFrame(data)

st.dataframe(df)
st.data_editor(df)
st.table(df)

st.dataframe(df.style.format({"Sales": "${:,.0f}", "Customer": "{:,.0f}"}))