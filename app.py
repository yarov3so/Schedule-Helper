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
    hide_index=True,
    column_config={
        "Ignore?": st.column_config.CheckboxColumn(
            "Ignore?",
            help="Check to ignore this row (deleting rows is not possible)",
            default=False  # ensures new rows have unchecked boxes
        ),
        "Name": st.column_config.TextColumn(
            "Name",
            help="Enter the name of the period or activity"
        ),
        "Start": st.column_config.TextColumn(
            "Start",
            help="Enter the start time HH:MM or leave blank"
        ),
        "Length (minutes)": st.column_config.NumberColumn(
            "Length (minutes)",
            help="Enter the duration of the period in minutes or leave blank"
        )
    }
)

edited_df["Name"] = edited_df["Name"].fillna("")
edited_df["Type"] = edited_df["Type"].fillna("")

df_output=edited_df[(edited_df["Ignore?"] == False) | (edited_df["Ignore?"].isnull()) ].drop(columns=["Ignore?"])
for key in df_output:
    df_output[key]=df_output[key]
st.write("### Editable Periods")
st.dataframe(df_output,hide_index=True)

def comprehend(mystring):
    
    data_list=mystring.replace(" ", "")
    data=[]
    
    try:
        data_list=mystring.split(":")
        for num in data_list:
            data.append(int(num))
    except:
        return None

    return tuple(data)

def try_int(mystring):
    try:
        return int(mystring)
    except:
        return None
    
df=df_output.copy()
df["Start"]=df["Start"].apply(comprehend)
df["End"]=df["End"].apply(comprehend)
df["Length (minutes)"]=df["Length (minutes)"].apply(try_int)

for idx in df[["Start","Length (minutes)","End"]].index:
    if df[["Start","Length (minutes)","End"]].loc[idx].isnull().all():
        st.warning("Please ensure that you have correctly specified at least one of the following for each period (row): Start, End.)
        st.stop()

st.dataframe(df)

