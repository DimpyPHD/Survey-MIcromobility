import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import os
import numpy as np
import json
import csv
import random
import os
from PIL import Image, UnidentifiedImageError

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def save_to_google_sheets(data_dict):
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("gcp_credentials.json", scope)
        client = gspread.authorize(creds)

        st.info("✅ Authenticated with Google Sheets")

        sheet = client.open("Micromobility Responses").sheet1
        st.info("✅ Opened Google Sheet successfully")

        header = list(data_dict.keys())
        values = list(data_dict.values())

        if sheet.row_count <= 1 and not sheet.cell(1, 1).value:
            sheet.insert_row(header, 1)
            st.info("🧾 Header added to sheet")

        sheet.append_row(values)
        st.success("✅ Response saved to Google Sheets")

    except Exception as e:
        st.error(f"❌ Google Sheets Save Failed: {e}")


# ----------- MOBILE RESPONSIVE PATCH -----------
# Custom center alignment CSS
st.markdown("""
<style>
/* General layout fix */
.option-card {
    background-color: #f9f9f9;
    padding: 12px;
    margin: 10px auto;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0px 1px 6px rgba(0,0,0,0.1);
    width: 95%;
    max-width: 400px;
}

/* Highlight selected */
.selected-row {
    background-color: #dff6ff !important;
    border: 2px solid #00bfff;
}

/* Image responsiveness */
img {
    border-radius: 8px;
    margin-bottom: 8px;
}

/* Emoji and label formatting */
.option-card p {
    margin: 4px 0;
    font-size: 16px;
}

/* Smaller screens */
@media screen and (max-width: 768px) {
    .option-card {
        width: 95%;
    }
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------

# ----------- Load Data -----------
@st.cache_data
def load_data():
    df = pd.read_csv("survey_data.csv")
    df.columns = ["Task", "Alternative", "Time", "Cost", "Wait"]
    return df

# ----------- Page State -----------
if "page" not in st.session_state:
    st.session_state.page = "intro"
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "user_id" not in st.session_state:
    st.session_state.user_id = uuid.uuid4().int % 4
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None
if "admin_access" not in st.session_state:
    st.session_state.admin_access = False
if "shuffled_tasks" not in st.session_state:
    st.session_state.shuffled_tasks = {}

# ----------- Intro Page -----------
if st.session_state.page == "intro":
    st.title("🚲 Welcome to the Survey for Micromobility Choice Modeling: Preferences for E-Rickshaws, Public Bike Sharing, and  Walking")

    st.markdown("""
Greetings Participant,  

In order to better understand urban visitors' preferences for sustainable micromobility options including e-rickshaws, public bike sharing systems (PBSS), and walking, I am conducting this survey as part of my Ph.D. research at NICMAR University, Pune. The goal of this research is to improve sustainable urban transportation networks by informing planning and policy decisions.

Your thoughts and experiences as an urban traveler are important in understanding how individuals select between various short-distance travel modes, which is why you are encouraged to take part in this study.

---

### Addressing the Survey

It should take about 5-10 minutes to complete the three brief sections that make up the survey:

**Stated Preference Option Scenarios**  
Five fictitious option scenarios will be shown to you, each of which describes a journey with three different modes of transportation (walking, PBSS, and e-rickshaw). You are asked to choose the course of action you would take in each scenario if you were in that circumstance in real life.

**Socio-Demographic Information**  
To assist put your travel interests in perspective, this part asks about your age, gender, occupation, income level, and education.

**Travel Habits**  
You will be questioned about how you usually travel, including your favorite forms of transportation, how often you travel, and how you feel about different micromobility alternatives.

---

### Consent

By continuing with the survey, you confirm that you:

- Understand the purpose of the study  
- Are aware that participation is voluntary and anonymous  
- Give consent for your responses to be used for academic research

If you have any questions about the study or how your data will be used, please feel free to contact me at **dimpy.phd1@pune.nicmar.ac.in**.

Thank you for your time and contribution to this important research on sustainable transport solutions.

Very warm regards,  
**Dimpy Rathee**  
Ph.D. Candidate  
School of Planning and Architecture  
NICMAR University, Pune
""")

    if st.button("👉 Begin Survey"):
        st.session_state.page = "survey"
        st.rerun()
#----------------------------survey
elif st.session_state.page == "survey":
    import numpy as np
    import time

    df_raw = load_data()

    # ✅ Clean up headers: remove line breaks, keep exact meaning
    df_raw.columns = [col.replace("\n", " ").replace("  ", " ").strip() for col in df_raw.columns]
    df = df_raw.copy()

    # ✅ Detect column names directly from file
    columns = list(df.columns)
    task_col = columns[0]
    alt_col = columns[1]
    time_label = columns[2]
    cost_label = columns[3]
    wait_label = columns[4]

    # ✅ Keep only valid tasks
    df = df[df[task_col].apply(lambda x: str(x).isdigit())]
    df[task_col] = df[task_col].astype(int)

    valid_tasks = df[task_col].value_counts()
    valid_tasks = valid_tasks[valid_tasks == 3].index.tolist()
    all_tasks = sorted(valid_tasks)

    # ✅ Assign tasks by user group
    blocks = np.array_split(all_tasks, 4)
    user_tasks = list(blocks[st.session_state.user_id])
    total_tasks = len(user_tasks)
    answered = len(st.session_state.responses)
# ui color , text --------------------------
    # ✅ Responsive styling
    st.markdown("""
    <style>
    .card-container {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .card-selected {
        background-color: #e0f3ff !important;
    }
    img {
        max-width: 100px !important;
        height: auto !important;
        display: block;
        margin: auto;
    }
    @media screen and (max-width: 768px) {
        .element-container .stColumns {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
        }
        .stColumn {
            flex: 1 1 auto !important;
        }
        button[kind="secondary"] {
            margin-left: auto !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # ✅ Show task or move to next page
    if answered < total_tasks:
        task_id = user_tasks[answered]

        st.subheader(f"Scenario {answered + 1} of {total_tasks}")
        st.markdown("Suppose you have just arrived from aa transit facility and have to reach your destination which is about 5 km away. What modes will you prefer?")

        subset = df[df[task_col] == task_id].copy().reset_index(drop=True)

        # Shuffle only once
        if "shuffled_tasks" not in st.session_state:
            st.session_state.shuffled_tasks = {}
        if task_id not in st.session_state.shuffled_tasks:
            st.session_state.shuffled_tasks[task_id] = subset.sample(frac=1).reset_index(drop=True)
        subset = st.session_state.shuffled_tasks[task_id]

        # Track selection
        if "selected_options" not in st.session_state:
            st.session_state.selected_options = {}
        selected_idx = st.session_state.selected_options.get(task_id, None)

        # Image map
        images = {
            "e-rickshaw": "images/E-rickshaw.jpg",
            "public bike sharing system": "images/Public Bike Sharing System.jpg",
            "walking": "images/Walking.jpg"
        }
# UIi show kaise hoga ---------------------start -----------
        # ✅ Show all 3 options
        for idx, row in subset.iterrows():
            alt = row[alt_col]
            alt_key = alt.lower().strip()
            img_path = images.get(alt_key, "images/default.jpg")
            is_selected = selected_idx == idx
            bg_color = "#e0f3ff" if is_selected else "#f9f9f9"

            with st.container():
                st.markdown(f"<div style='background-color:{bg_color}; padding: 10px; border-radius: 10px;'>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 4, 1])

                with col1:
                    if os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    else:
                        st.warning("⚠️ Image not found")

                # with col2:
                #     st.markdown(f"**{alt}**")
                #     st.markdown(f"⏱️ **{time_label}:** {row[time_label]} min")
                #     st.markdown(f"💰 **{cost_label}:** ₹{row[cost_label]}")
                #     st.markdown(f"⏳ **{wait_label}:** {row[wait_label]} min")
                with col2:
                    st.markdown(f"**{alt}**")
                
                    if "walk" in alt.lower():
                        st.markdown(f"⏱️ **Travel Time (in minutes):** {row[time_label]}")
                        st.markdown(f"💰 **Travel Cost (in INR):** ₹{row[cost_label]}")
                    else:
                        st.markdown(f"⏱️ **In-vehicle Time (in minutes):** {row[time_label]}")
                        st.markdown(f"💰 **In-vehicle Cost (in INR):** ₹{row[cost_label]}")
                
                    st.markdown(f"⏳ **Waiting Time (in minutes):** {row[wait_label]}")
                


                with col3:
                    if st.button("Select", key=f"select_{task_id}_{idx}"):
                        st.session_state.selected_options[task_id] = idx
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
# ----------------------------------------end
        # ✅ Show Next button once at the bottom
        st.markdown("---")
        if selected_idx is not None:
            selected_row = subset.loc[selected_idx]
            label = f"{selected_row[alt_col]} ({time_label}: {selected_row[time_label]} mins, {cost_label}: ₹{selected_row[cost_label]}, {wait_label}: {selected_row[wait_label]} mins)"
            if st.button("Next ➡️", key=f"next_button_enabled_{task_id}"):
                st.session_state.responses[f"Task_{task_id}"] = label
                st.rerun()
        else:
            st.button("Next ➡️", disabled=True, key=f"next_button_disabled_{task_id}_{int(time.time()*1000)}")

    else:
        st.session_state.page = "demographics"
        st.rerun()
#----------------------------------------------end kasie show --------------------


# ✅ FIX STARTS HERE
elif st.session_state.page == "demographics":
    st.header("🧾 Demographic & Travel Habits")

    # ✅ Ensure step variable exists
    if "demographic_step" not in st.session_state:
        st.session_state.demographic_step = 0
    step = st.session_state.demographic_step

    # --------- Page 1 ---------
    if step == 0:
        with st.form("demographics_page_1"):
            st.subheader("🔹 General Information")

            residence = st.text_input("🏙️ Place of current residence")

            age_group = st.selectbox("🎂 Age Group", ["-- Select --", "Up to 18", "18–24", "24–34", "34–44", "44+"])
            gender = st.radio("🧑 Gender", ["Female", "Male", "Other"])

            education = st.selectbox("🎓 Highest Education", [
                "-- Select --",
                "No formal education",
                "Higher secondary/ITI/certificate",
                "Graduate/Postgraduate/PhD/equivalent"
            ])

            occupation = st.selectbox("💼 Occupation", [
                "-- Select --", "Student/Scholar", "Employed/Self-employed", "Unemployed/Home-maker"
            ])

            income = st.selectbox("💰 Monthly Household Income (INR)", [
                "-- Select --", "Up to 25,000", "25,001–50,000", "50,001–100,000", "Above 100,000"
            ])

            next_btn = st.form_submit_button("Next ➡️")
            if next_btn and residence and age_group != "-- Select --" and education != "-- Select --" and occupation != "-- Select --" and income != "-- Select --":
                st.session_state.demographic_data = {
                    "residence": residence,
                    "age_group": age_group,
                    "gender": gender,
                    "education": education,
                    "occupation": occupation,
                    "income": income
                }
                st.session_state.demographic_step += 1
                st.rerun()
            elif next_btn:
                st.warning("Please complete all fields before continuing.")


    # --------- Page 2 ---------
    elif step == 1:
        with st.form("demographics_page_2"):
            st.subheader("🔹 Travel Habits")

            cars_owned = st.selectbox("🚗 Cars owned by household", ["-- Select --", "0", "1", "2", "3 or more"])
            bicycles = st.selectbox("🚲 Bicycles owned by household", ["-- Select --", "0", "1", "2 or more"])
            public_transport_usage = st.radio("🚌 Frequency of Public Transport usage ", [
                "Never", "Every day", "A few times a week", "A few times a month"
            ])

            st.subheader(" what is the frequency of usage of the following for Last-mile travel?")
            e_rickshaw = st.selectbox("E-rickshaw", ["-- Select --", "Never", "Every day", "Few times/week", "Few times/month or less"])
            pbss = st.selectbox("Public Bike Sharing System", ["-- Select --", "Never", "Every day", "Few times/week", "Few times/month or less"])
            walking = st.selectbox("Walking", ["-- Select --", "Never", "Every day", "Few times/week", "Few times/month or less"])

            submit_btn = st.form_submit_button("✅ Submit Survey")

            if (
                submit_btn and
                cars_owned != "-- Select --" and
                bicycles != "-- Select --" and
                e_rickshaw != "-- Select --" and
                pbss != "-- Select --" and
                walking != "-- Select --"
            ):
                st.session_state.demographic_data.update({
                    "cars_owned": cars_owned,
                    "bicycles_owned": bicycles,
                    "public_transport_usage": public_transport_usage,
                    "last_mile_e_rickshaw": e_rickshaw,
                    "last_mile_pbss": pbss,
                    "last_mile_walking": walking
                })

                # Save logic here...
                data = {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat()
                }
                data.update(st.session_state.demographic_data)
                data.update(st.session_state.responses)

             # Save to JSON
                with open(f"responses_{data['id']}.json", "w") as f:
                    json.dump(data, f)

                # Save to CSV
                csv_file = "responses.csv"
                write_header = not os.path.exists(csv_file)
                with open(csv_file, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=data.keys())
                    if write_header:
                        writer.writeheader()
                    writer.writerow(data)

                # ✅ Save to Google Sheets
# ✅ Save to Google Sheets
                save_to_google_sheets(data)        

                st.session_state.page = "thankyou"
                st.rerun()
            elif submit_btn:
                st.warning("Please complete all fields before submitting.")


# ----------- Thank You Page -----------
elif st.session_state.page == "thankyou":
    st.balloons()
    st.title("🎉 Thank you for completing the survey!")
    st.success("Your responses have been successfully submitted.")
    st.markdown("""
We sincerely appreciate your time and participation.  
Your feedback will contribute to valuable research in improving micromobility and urban transport solutions.

If you have any questions or would like to learn more about this study, feel free to reach out to:

📩 **Dimpy Rathee**  
Research Scholar, NICMAR University  
✉️ [dimpy.phd1@pune.nicmar.ac.in](mailto:dimpy.phd1@pune.nicmar.ac.in)
""")
