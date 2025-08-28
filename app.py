import pandas as pd
import streamlit as st
from datetime import time

def timesum(time1,time2):
    hrsum=(time1[0]+time2[0]) % 24
    minsum=time1[1]+time2[1]
    if minsum >= 60:
        hrsum+=minsum//60
    return (hrsum%24,minsum%60)

def timediff(time1,time2):
    hrdiff=time1[0]-time2[0]
    mindiff=time1[1]-time2[1]
    if mindiff<0:
        hrs_in_mindiff=-mindiff//60
        hrdiff-=1+hrs_in_mindiff
        mindiff=60-(-mindiff)%60
    if hrdiff<0:
        hrdiff+=1
        mindiff = -(60-mindiff)
    return (hrdiff,mindiff)

def minutes(time):
    return(time[1]+60*time[0])

def overlap(inv1,inv2):

    if all([num>=0 for num in timediff(inv1[0],inv2[0])]):
        if any([num<0 for num in timediff(inv1[0],inv2[1])]):
            return True
    if all([num>=0 for num in timediff(inv2[0],inv1[0])]):
        if any([num<0 for num in timediff(inv2[0],inv1[1])]):
            return True

    return False    

def first_period(sched): # Periods must be non-overlapping!

    min_index_hr=min([period["start"][0] for period in sched])
    sched_min_hr=[]
    for period in sched:
        if period["start"][0]==min_index_hr:
            sched_min_hr.append(period)
    min_index_min=min([period["start"][1] for period in sched_min_hr])
    for period in sched_min_hr:
        if period["start"][1]==min_index_min:
            return period

marker=True

def fill_blanks(reqs,sched): 

    global marker

    sched_filled=[]

    for typ in reqs:
        
        sched_typ=[]
        
        for period in sched:
            
            if period["type"]==typ:
                sched_typ.append(period.copy())
                
        for period in sched_typ:
            
            if period["start"]!=None and period["length"]==None and period["end"]!=None:
                period["length"]=minutes(timediff(period["end"],period["start"]))
            if period["start"]!=None and period["length"]!=None and period["end"]==None:
                period["end"]=timesum(period["start"],(0,period["length"]))
            if period["start"]==None and period["length"]!=None and period["end"]!=None:
                period["start"]=timediff(period["end"],(0,period["length"]))

        rem_req=reqs[typ]
        j=0
        for period in sched_typ:
            if period["length"]!=None:
                rem_req-=period["length"]
                j+=1
                
        if rem_req<0:
            marker=False
            st.error(f"Too many minutes allocated to the periods of type \'{typ}\'! Allocate {-rem_req} fewer minutes to periods of this type.")
            st.stop()

        split_rest=False
        if len(sched_typ) - j != 0 and rem_req>=0:
            split_rest=True
            length_rem_each=rem_req//(len(sched_typ) - j)
            length_rem_diff=rem_req-length_rem_each*(len(sched_typ) - j)

            if length_rem_diff==0 and rem_req>0:
                allocation=[period["name"] for period in sched_typ if (period["start"]==None and period["length"]==None) or (period["end"]==None and period["length"]==None)]
                allocation_str=""
                for per in allocation:
                    allocation_str+=(per+", ")
                allocation_str=allocation_str[:-2]
                st.success(f"Allocating the remaining {rem_req} minutes of period type \'{typ}\' evenly to the following periods: {allocation_str}")
            
            if length_rem_diff!=0 and rem_req>0:
                allocation=[period["name"] for period in sched_typ if (period["start"]==None and period["length"]==None) or (period["end"]==None and period["length"]==None)]
                allocation_str=""
                for per in allocation:
                    allocation_str+=(per+", ")
                allocation_str=allocation_str[:-2]
                st.success(f"Allocating the remaining {rem_req} minutes of period type \'{typ}\' almost evenly to the following periods: {allocation_str}")

            #Need to create a list of these flexible periods...
            sched_typ_flex=[period for period in sched_typ if (period["start"]==None and period["length"]==None) or (period["end"]==None and period["length"]==None)]
            for period in sched_typ_flex:
                if period["start"]==None and period["length"]==None:
                    period["length"]=0
                    period["start"]= period["end"]
                    period["init"]="end"
                if period["end"]==None and period["length"]==None:
                    period["length"]=0
                    period["end"]= period["start"]
                    period["init"]="start"

            for i in range(rem_req):

                if sched_typ_flex[i%len(sched_typ_flex)]["init"]=="start":
                    sched_typ_flex[i%len(sched_typ_flex)]["length"]+=1
                    sched_typ_flex[i%len(sched_typ_flex)]["end"]=timesum(sched_typ_flex[i%len(sched_typ_flex)]["end"],(0,1))

                if sched_typ_flex[i%len(sched_typ_flex)]["init"]=="end":
                    sched_typ_flex[i%len(sched_typ_flex)]["length"]+=1
                    sched_typ_flex[i%len(sched_typ_flex)]["start"]=timediff(sched_typ_flex[i%len(sched_typ_flex)]["start"],(0,1))

        if split_rest==False and rem_req>0:
            marker=False
            st.warning(f"Could not allocate the remaining {rem_req} minutes of period type \'{typ}\'! Add more periods of this type, or make more room for existing ones.")
            
        sched_filled+=sched_typ[:]


    for period in sched_filled:
        if "init" in period:
            del period["init"]

    return sched_filled

                
def validate(reqs,sched):

    global marker

    badperiods=[]
    aps=set()
    gaps=[]
    sched_with_gaps=[]

    # Check for badly formulated periods
    for i in range(len(sched)):
        try:
            if any([j<0 for j in timediff( sched[i]["end"],sched[i]["start"] ) ]):
                badperiods.append(sched[i]["name"])
        except:
            continue
    if len(badperiods)!=0:
        badperiods_str=""
        for bp in badperiods:
            badperiods_str+=(bp+", ")
        badperiods_str=badperiods_str[:-2]
        st.error(f"The following periods end before they start: {badperiods_str}. Please correct their start/end times before continuing.")
        st.stop()


    # Logically fill blanks
    sched_test=fill_blanks(reqs,sched[:])
    if sched_test!=None:
        sched=sched_test[:]
    else:
        return None

    # Check for overlaps
    #overlaps=set()
    #overlaps=[]
    overlaps=set()
    for i in range (len(sched)):
        for j in range(len(sched)):
            if j!=i and overlap((sched[i]["start"],sched[i]["end"]),(sched[j]["start"],sched[j]["end"])):
                #overlaps=overlaps.union(set({sched[i]["name"]}.union({sched[j]["name"]})))
                overlaps=overlaps.union([tuple(sorted([sched[i]["name"],sched[j]["name"]]))])
    overlaps=list(overlaps)
    
    if len(overlaps)!=0:

        overlaps_str=""
        for olap in overlaps:
            overlaps_str+=(olap[0]+" with "+olap[1]+", ")
        overlaps_str=overlaps_str[:-2]
        st.warning(f"Overlaps detected: {overlaps_str}")
        marker=False

    # Sort periods
    sched_sorted=[]

    while len(sched)!=0:
        sched_sorted.append(first_period(sched))
        sched.remove(first_period(sched))

    sched=sched_sorted[:]

    # Add gaps (if any), display overlaps (if any)
    j=1
    k=1
    for i in range(len(sched)):
        sched_with_gaps.append(sched[i])
        if i<len(sched)-1 and sched[i+1]["start"]!=sched[i]["end"]:
            gaps.append((sched[i]["end"],sched[i+1]["end"])) #
            new_gap={"name":"Gap "+str(j),"type":"gap","start":sched[i]["end"],"length":60*timediff(sched[i+1]["start"],sched[i]["end"])[0]+timediff(sched[i+1]["start"],sched[i]["end"])[1],"end":sched[i+1]["start"]}
            
            if new_gap["length"]<0:
                new_gap["name"]="Overlap "+str(k)
                new_gap["type"]="overlap"
                new_gap["start"]=sched[i+1]["start"]
                new_gap["end"]=sched[i]["end"]
                new_gap["length"]=-(60*timediff(sched[i+1]["start"],sched[i]["end"])[0]+timediff(sched[i+1]["start"],sched[i]["end"])[1])
                j-=1
                k+=1
                
            sched_with_gaps_old=sched_with_gaps[:]
            sched_with_gaps.append(new_gap)
            
            j+=1

    if sched_with_gaps!=sched:
        marker=False
        return sched_with_gaps
    #else:
        #st.markdown("##### The current schedule is valid and optimal. ^^")
        
    return sched




st.title("Schedule Helper")
st.markdown("A tool for generating and tweaking schedules primarily meant to be used by teachers in Quebec.")
st.text("")

st.set_page_config(
    page_title="Schedule Helper",
    page_icon="MHT.png", 
)

def try_int(mystring):
    try:
        return int(mystring)
    except:
        return None

reqs={}

st.session_state.clear()

if "df_reqs" not in st.session_state:
    st.session_state.df_reqs = pd.DataFrame([{
        "Type of period": "",
        "Total required time (minutes)": "",
        # "Ignore?": False
    }])

st.markdown("Enter the types of periods that will appear in your schedule (e.g. teaching, duty, lunch, etc.) in the table below. Be sure to avoid using \"gap\" and \"overlap\" as names for period types.")
    
edited_df_reqs = st.data_editor(
    st.session_state.df_reqs,
    num_rows="dynamic",  # lets user add rows directly
    width="stretch",
    hide_index=True,
    # column_config={
    #     "Ignore?": st.column_config.CheckboxColumn(
    #         "Ignore?",
    #         help="Check to ignore this type of period (deleting rows is not possible)",
    #         default=False  # ensures new rows have unchecked boxes
    #     )
    # }
)


if len(edited_df_reqs.index)!=len(set(edited_df_reqs["Type of period"])):
    st.error("Duplicate types of period detected! Please specify each type of period only once.")
    st.stop()

#reqs=dict(zip(edited_df_reqs[edited_df_reqs["Ignore?"]==False]["Type of period"],edited_df_reqs[edited_df_reqs["Ignore?"]==False]["Total required time (minutes)"]))
reqs=dict(zip(edited_df_reqs["Type of period"],edited_df_reqs["Total required time (minutes)"]))


if len(reqs)==0:
    st.stop()
    
if "" in reqs.keys():
    st.stop()

if "" in reqs.values() or None in reqs.values():
    st.stop()


for el in reqs:
    try:
        reqs[el]=try_int(reqs[el].replace(" ",""))
        if type(reqs[el])!=int:
            st.warning("Use only whole numbers in the 'Total time required (minutes)' column!")
            st.stop()
    except:
        st.stop()

if "df_user" not in st.session_state:
    st.session_state.df_user = pd.DataFrame(columns=["Name", "Type", "Start", "Length (minutes)","End","Ignore?"])
    st.session_state.df_user["Ignore?"] = False

st.text("")
st.markdown("Use the table below to fill in your schedule to the best of your knowledge and ability. Note that you only need to specify ONE of Start/End for each period, but may choose to specify all three of Start/Length/End. Be sure to only use 24-hour time in Start/End columns (avoid the 12-hour clock system).")
st.markdown("*The algorithm uses even allocation, meaning it distributes the required hours as evenly as possible across the flexible periods (those for which only one of Start/Length/End has been specified), while respecting the schedule constraints specified by the user.*")

# Display editable table
edited_df = st.data_editor(
    st.session_state.df_user,
    num_rows="dynamic",  # lets user add rows directly
    width="stretch",
    hide_index=True,
    column_config={
        "Type": st.column_config.SelectboxColumn(
            "Type",
            options=list(reqs.keys()),  # only allow valid period types
            help="Select the type of period"
        ),
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

if df_output.empty:
    #st.warning("Please ensure that you have correctly specified at least one of the following for each period (row): Start, End.")
    st.stop()

# if "" in df_output["Type"]:
#     st.stop()

# if set(df_output["Type"]).issubset(set(reqs.keys()))==False:
#     #st.warning("Only use the active period types you specified in the beginning!")
#     st.stop()


#st.dataframe(df_output,hide_index=True)

def comprehend(mystring):
    data=[]
    try:
        data_list=mystring.replace(" ", "")
        data_list=mystring.split(":")
        for num in data_list:
            data.append(int(num))
    except:
        return None
    return tuple(data)
    
df=df_output.copy()
df["Start"]=df["Start"].apply(comprehend)
df["End"]=df["End"].apply(comprehend)
df["Length (minutes)"]=df["Length (minutes)"].apply(try_int)



for idx in df[["Start","Length (minutes)","End"]].index: #df[["Start","Length (minutes)","End"]].loc[idx].isnull().all() or (
    if df[["Start","Length (minutes)","End"]].loc[idx][0]==None and df[["Start","Length (minutes)","End"]].loc[idx][2]==None :
        st.warning("Please ensure that you have correctly specified at least one of the following for each period (row): Start, End.")
        st.stop()

for el in df["Type"]:
    if el not in reqs.keys():
        st.warning("Please remember to specify the type of each period listed above.")
        st.stop()

if set(df_output["Type"]).issubset(set(reqs.keys()))==False:
    #st.warning("Only use the active period types you specified in the beginning!")
    st.stop()

st.text("")
st.markdown("### Proposed Schedule")

df.columns=["name","type","start","length","end"]

schedule=validate(reqs,df.to_dict(orient="records"))

def highlight_row_condition(row):
    
        if row['Type'] == "gap":
            return ['background-color: rgba(0, 0, 255, 0.1)'] * len(row)
        elif row['Type'] == "overlap":
            return ['background-color: rgba(255, 0, 0, 0.1)'] * len(row)
        else:
            return [''] * len(row) # 

if type(schedule)==list:
    df=pd.DataFrame(schedule)
    df.start=df.start.apply(lambda t: time(t[0], t[1])).apply(lambda t: t.strftime("%H:%M"))
    df.end=df.end.apply(lambda t: time(t[0], t[1])).apply(lambda t: t.strftime("%H:%M"))
    df.length=df.length.astype(str)

    df.columns=["Name","Type","Start","Length (minutes)","End"]
    df=df.style.apply(highlight_row_condition, axis=1)
    st.dataframe(df,hide_index=True)

if marker==True:
    st.success("**The current schedule is valid and optimal. ^^**")


st.text("")
st.markdown("""*Crafted by yarov3so*   
<a href="https://www.buymeacoffee.com/yarov3so" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="width: 9em; height: auto; padding-top: 0.7em; padding-bottom: 1em" ></a>  
See my other [Math Help Tools](https://mathh3lptools.streamlit.app)""",unsafe_allow_html=True)
