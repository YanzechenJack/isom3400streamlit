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
