import streamlit as st
import pandas as pd
import polars as pl
from io import BytesIO
from sqlalchemy import create_engine
import base64
import os
import sys
from utils.data_processing import (
    get_data,
    decrypt_dataframe,
    get_unique_kommuner,
    filter_dataframe_by_choice,
    generate_organization_links,
    filter_df_by_search,
    fix_column_types_and_sort,
    format_number_european,
    round_to_million,
    get_ai_text,
)
from utils.plots import create_pie_chart
from config import set_pandas_options, set_streamlit_options

# Apply the settings
set_pandas_options()
set_streamlit_options()

# Function to load and inject CSS into the Streamlit app
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("webapp/style.css")

if "df_pl" not in st.session_state:
    with st.spinner("Henter data..."):
        df_retrieved = get_data()
        # Optional: load environment variables from the .env file
        # load_dotenv()

        encoded_key = os.getenv("ENCRYPTION_KEY")

        if encoded_key is None:
            raise ValueError("ENCRYPTION_KEY is not set in the environment variables.")

        encryption_key = base64.b64decode(encoded_key)

        col_list = ["Kommune", "ISIN kode", "Værdipapirets navn"]
        st.session_state.df_pl = decrypt_dataframe(df_retrieved, encryption_key, col_list)


st.title("Top 10")

col1, col2 = st.columns([0.3, 0.7])
with col1:
    search_query = st.text_input("Søg i tabellen:", "")

# Filter the dataframe to include rows where 'Priority' is either 2 or 3
filtered_df = st.session_state.df_pl.filter(st.session_state.df_pl["Priority"].is_in([2, 3]))

filtered_df = filter_df_by_search(filtered_df, search_query)

filtered_df = fix_column_types_and_sort(filtered_df)

# Function to filter for 'Alkohol' and get value counts and sum for 'Kommune'
def get_top_10_sum(filtered_df, top_n=10):
    kommune_summary = (
        filtered_df.group_by('Kommune')
        .agg([
            pl.sum('Markedsværdi (DKK)').alias('Total Markedsværdi (DKK)'),
            pl.len().alias('Antal investeringer')
        ])
        .sort('Total Markedsværdi (DKK)', descending=True)
    )
    # Display the dataframe below the three columns
    display_df_sum = kommune_summary.with_columns(
        pl.col('Total Markedsværdi (DKK)')
        .map_elements(round_to_million, return_dtype=pl.Utf8)
        .alias('Total Markedsværdi (DKK)'),
    )
    return display_df_sum.head(top_n)

# Function to filter for 'Alkohol' and get value counts and sum for 'Kommune'
def get_top_10_count(filtered_df, top_n=10):
    kommune_summary = (
        filtered_df.group_by('Kommune')
        .agg([
            pl.len().alias('Antal investeringer'),
            pl.sum('Markedsværdi (DKK)').alias('Total Markedsværdi (DKK)'),
        ])
        .sort('Antal investeringer', descending=True)
    )
    # Display the dataframe below the three columns
    display_df_count = kommune_summary.with_columns(
        pl.col('Total Markedsværdi (DKK)')
        .map_elements(round_to_million, return_dtype=pl.Utf8)
        .alias('Total Markedsværdi (DKK)'),
    )
    return display_df_count.head(top_n)

# Streamlit app
if search_query:
    st.subheader(f"Top 10 for '{search_query}':")
else: 
    st.subheader("Kommuner med flest problematiske investeringer:")

col_sum, col_count = st.columns(2)
with col_sum:
    # Get top 10 municipalities for 'Alkohol'
    top_10_kommune = get_top_10_sum(filtered_df)
    top_10_kommuner_list = top_10_kommune['Kommune'].to_list()

    # Filter the original dataframe based on the top 10 municipalities
    filtered_df_top_10 = filtered_df.filter(pl.col('Kommune').is_in(top_10_kommuner_list))

    # Display the result in the Streamlit app
    st.write("Top 10 kommuner med den største sum af problematiske investeringer:")
    st.dataframe(top_10_kommune)

    # Display the result in the Streamlit app
    st.write("Data til grund for top 10:")
    st.dataframe(filtered_df_top_10)

with col_count:
    # Get top 10 municipalities for 'Alkohol'
    top_10_kommune_count = get_top_10_count(filtered_df)
    top_10_kommuner_count_list = top_10_kommune_count['Kommune'].to_list()

    # Filter the original dataframe based on the top 10 municipalities
    filtered_df_top_10_count = filtered_df.filter(pl.col('Kommune').is_in(top_10_kommuner_count_list))

    # Display the result in the Streamlit app
    st.write("Top 10 kommuner med det største antal af problematiske investeringer:")
    st.dataframe(top_10_kommune_count)

    # Display the result in the Streamlit app
    st.write("Data til grund for top 10:")
    st.dataframe(filtered_df_top_10_count)

