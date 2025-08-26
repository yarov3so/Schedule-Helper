import numpy as np
import pandas as pd
import re
import statistics as stat
import streamlit as st

st.title("Schedule Maker")
st.markdown("A tool for generating and tweaking schedules primarily meant to be used by teachers in Quebec.")

st.set_page_config(
    page_title="Schedule Maker",
    page_icon="MHT.png", 
)

if "df_user" not in st.session_state:
    st.session_state.df_user = pd.DataFrame(columns=["Name", "Type", "Start", "Length (minutes)","End","Ignore?"])

st.session_state.df_user["Ignore?"] = False

# Display editable table
edited_df = st.data_editor(
    st.session_state.df_user,
    num_rows="dynamic",  # lets user add rows directly
    use_container_width=True,
    hide_index=True
)

df_output=edited_df[edited_df["Ignore?"] == False].drop(columns=["Ignore?"])
st.write("### Editable Periods")
st.dataframe(df_output,hide_index=True)
