import streamlit as st
import time

# Title
st.title("Business Dashboard with Streamlit Layouts")

# Objective
st.write("Objective: To demonstrate the usage of columns, tabs, and dynamic containers in a business dashboard.")

# Columns Layout
col1, col2, col3 = st.columns(3)
with col1:
    st.header("Q1 2024")
    st.write("Revenue: $1.2M")
with col2:
    st.header("Q2 2024")
    st.write("Revenue: $1.5M")
with col3:
    st.header("Q3 2024")
    st.write("Revenue: $1.3M")

# Tabs Layout
tab1, tab2, tab3 = st.tabs(["Sales Data", "Customer Insights", "Market Trends"])
with tab1:
    st.write("Content for Sales Data")
    sales_data = {
        "Q1 2024": "$1.2M",
        "Q2 2024": "$1.5M",
        "Q3 2024": "$1.3M",
        "Q4 2024": "$1.6M"
    }
    for quarter, revenue in sales_data.items():
        st.write(f"{quarter}: {revenue}")
with tab2:
    st.write("Content for Customer Insights")
    customer_feedback = [
        "Great service!",
        "Very satisfied with the product quality.",
        "Quick delivery and excellent support."
    ]
    for feedback in customer_feedback:
        st.write(f"- {feedback}")
with tab3:
    st.write("Content for Market Trends")
    market_trends = {
        "Eco-friendly products": "Increasing demand",
        "Online shopping": "Continued growth",
        "Subscription services": "Rising popularity"
    }
    for trend, status in market_trends.items():
        st.write(f"{trend}: {status}")

with st.expander("More Information"):
    st.write("Additional details on data collection methods.")
    st.write("Data was collected through surveys and sales reports.")

# Dynamic Containers
placeholder = st.empty()

# Simulate loading data and updating the placeholder
for i in range(5):
    placeholder.write(f"Loading data... {i*20}% complete")
    time.sleep(1)

# Once loading is complete, display the final message
placeholder.write("Data loading complete. Displaying business insights.")

# Display dynamic business insights
business_insights = [
    "Revenue increased by 15% in Q1 2024.",
    "Customer satisfaction improved by 10%.",
    "Market trends show a growing demand for eco-friendly products."
]
for insight in business_insights:
    placeholder.write(insight)
    time.sleep(2)