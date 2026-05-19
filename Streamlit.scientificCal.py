import streamlit as st

# Title
st.title("Basic Web Calculator")

# Input fields
num1 = st.number_input("Enter first number", value=0.0)
num2 = st.number_input("Enter second number", value=0.0)

# Operation selection
operation = st.selectbox("Choose operation", ["Add", "Subtract", "Multiply", "Divide"])

# Calculate
if st.button("Calculate"):
    if operation == "Add":
        result = num1 + num2
    elif operation == "Subtract":
        result = num1 - num2
    elif operation == "Multiply":
        result = num1 * num2
    elif operation == "Divide":
        result = num1 / num2 if num2 != 0 else "Error: Division by zero"

    st.success(f"Result: {result}")


import math

st.header("Scientific Functions")
operation_sci = st.selectbox("Choose scientific operation", ["Square Root", "Power", "Sin", "Cos", "Tan"])

value = st.number_input("Enter value", value=0.0)
power = st.number_input("Enter power (if applicable)", value=2.0)

if st.button("Calculate Scientific"):
    if operation_sci == "Square Root":
        result = math.sqrt(value)
    elif operation_sci == "Power":
        result = math.pow(value, power)
    elif operation_sci == "Sin":
        result = math.sin(math.radians(value))
    elif operation_sci == "Cos":
        result = math.cos(math.radians(value))
    elif operation_sci == "Tan":
        result = math.tan(math.radians(value))

    st.success(f"Result: {result}")
