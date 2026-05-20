import streamlit as st
import pandas as pd
import os

# Get the current working directory
current_directory = os.getcwd()
# Define the file path
file_path = os.path.join(current_directory, 'winequality-red.csv')

# Read the CSV file into a DataFrame
df = pd.read_csv(file_path, delimiter=';')

# Display the DataFrame in an interactive table
st.write("Wine Quality Data")
st.dataframe(df)
