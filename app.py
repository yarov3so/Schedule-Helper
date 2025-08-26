import numpy as np
import pandas as pd
import re
import statistics as stat
import streamlit as st

st.title("Schedule Maker")
st.markdown("A tool for generating and tweaking schedules primarily meant to be used by teachers in Quebec.")

st.set_page_config(
    page_title="Mayer Line Calculator",
    page_icon="MHT.png", 
)

if "df_user" not in st.session_state:
    st.session_state.df_user = pd.DataFrame(columns=["Name", "Type", "Start", "Length (minutes)","End"])

# Display editable table
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",  # lets user add rows directly
    use_container_width=True,
)

# Save changes back
st.session_state.df = edited_df

st.write("### Current Data")
st.dataframe(st.session_state.df)
