import streamlit as st

# Title and Header
st.title("Retail Business Dashboard")
st.header("Manager Input Section")

# Instruction
st.write("Please enter the monthly sales target and select the region.")

# Number input for sales target
sales_target = st.number_input("Enter Monthly Sales Target (in USD):", min_value=0, value=50000)

# Dropdown for region selection
region = st.selectbox("Select Region:", ["North", "South", "East", "West"])

# Submit button
if st.button("Submit"):
    # Display entered values
    st.write(f"Sales Target: ${sales_target}")
    st.write(f"Region Selected: {region}")
    
    # Success message
    st.success("Dashboard updated successfully!")
    
    # Extra message for ambitious target
    if sales_target > 100000:
        st.write("Great! You have set an ambitious target!")
