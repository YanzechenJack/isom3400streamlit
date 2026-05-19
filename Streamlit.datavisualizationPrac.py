# Step 1: Install Streamlit (run in terminal: pip install streamlit)

# Step 2: Import Necessary Libraries
import streamlit as st
import numpy as np
import pandas as pd

# Step 3: Generate Random Sales Data
sales_data = np.random.rand(100) * 1000

# Step 4: Create a DataFrame
products = ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']
sales = np.random.rand(5) * 1000
customers = np.random.randint(1, 100, size=5)

df = pd.DataFrame({
    'Product': products,
    'Sales': sales,
    'Customers': customers
})

# Step 5: Visualize Sales Data

# Display DataFrame using st.dataframe
st.markdown("### Product Sales and Customer Data")
st.dataframe(df)  # Interactive table with sorting and resizing

# Line Chart - Sales Over Time
st.markdown("### Sales Over Time")
st.line_chart(sales_data)

# Area Chart - Cumulative Sales
st.markdown("### Cumulative Sales")
st.area_chart(sales_data)

# Bar Chart - Sales by Product
st.markdown("### Sales by Product")
st.bar_chart(df[['Product', 'Sales']].set_index('Product'))

# Scatter Chart - Customer Engagement by Product
st.markdown("### Customer Engagement by Product")
st.scatter_chart(df[['Product', 'Customers']].set_index('Product'))

# Step 6: Run the Streamlit App (run in terminal: streamlit run app.py)