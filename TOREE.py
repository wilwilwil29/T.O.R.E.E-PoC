import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="T.O.R.E.E. Command Center", page_icon="🎭", layout="wide")

SHEET_ID = "1p4d1G0eTo2I_nixCTMiX1zBqdG2wt3fXIGXRPfkxOR8"

@st.cache_data(ttl=2)
def load_sheet_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

# Stream 1: Master Inventory (MASTER LIST tab - gid 1930217683)
inventory_data = load_sheet_data("1930217683")

if not inventory_data.empty and "Item Name" in inventory_data.columns and "Item ID" in inventory_data.columns:
    item_dict = dict(zip(inventory_data["Item Name"], inventory_data["Item ID"]))
    item_names_list = [str(name) for name in item_dict.keys() if str(name).strip() != "nan" and str(name).strip() != ""]
else:
    item_names_list = ["-- No Items Available --"]
    item_dict = {}

# Stream 2: Live Operations Log (MASTER LOG tab - gid 0)
log_data = load_sheet_data("0")
if not log_data.empty:
    log_data = log_data.dropna(how="all")

st.title("T.O.R.E.E.")
st.caption("Theater Operational Resource & Equipment Engine")

mode = st.sidebar.radio("Select System Access Level:", ["Crew Member", "Administrator"])

if mode == "Crew Member":
    st.header("📋 Equipment Movement Log")
    
    with st.form("crew_log_form", clear_on_submit=True):
        crew_name = st.text_input("1. Crew Member Name")
        selected_item_name = st.selectbox("2. Select Equipment", options=["-- Select Item --"] + item_names_list)
        
        # Location Selection Matrix matching Admin Filters
        location_option = st.selectbox(
            "3. Select Destination", 
            options=["-- Select Destination --", "Mainstage", "Studio Theater", "Sound Closet", "Elsewhere"]
        )
        custom_location = st.text_input("If Elsewhere, specify exact location:")
        
        submit = st.form_submit_button("Log Equipment Movement")
        
        if submit:
            # Resolve destination selection
            final_location = ""
            if location_option == "Elsewhere":
                final_location = custom_location.strip()
            elif location_option != "-- Select Destination --":
                final_location = location_option

            if crew_name and selected_item_name != "-- Select Item --" and final_location:
                item_id = item_dict.get(selected_item_name, "UNKNOWN_ID")
                webhook_url = "https://script.google.com/macros/s/AKfycbxFe_VvMIoCXehcDVA-WKY01Prt-KZW7c7GKK1LJBzH4_MiTkKNVcfio90aTk3xenMwFg/exec"
                payload = {"crew_name": crew_name, "item_name": selected_item_name, "item_id": item_id, "location": final_location}
                
                try:
                    response = requests.post(webhook_url, data=payload)
                    if response.status_code == 200:
                        st.success(f"Transmission successful: **{selected_item_name}** relocated to **{final_location}** by **{crew_name}**.")
                        st.info("💡 Refresh page to view live update across database.")
                    else:
                        st.warning("Cloud returned unexpected response.")
                except Exception as e:
                    st.error(f"Transmission failed: {e}")
            else:
                st.error("Please complete all required fields (including specific destination if Elsewhere).")

elif mode == "Administrator":
    st.header("🛡️ Tactical Command & Operations")
    admin_pass = st.sidebar.text_input("Admin Key", type="password")
    
    if admin_pass == "stagecraft":
        tab_list, tab_log, tab_info = st.tabs(["🗃️ Master List", "🕒 Master Log", "ℹ️ Master Info"])
        
        with tab_list:
            st.subheader("Inventory Master List")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                loc_filter = st.selectbox("Location Filter", ["All Locations", "Mainstage", "Studio Theater", "Sound Closet", "Elsewhere"])
            with col2:
                search_query = st.text_input("Search Equipment", placeholder="e.g., SM58, Pack...")
            with col3:
                st.write("")
                st.write("")
                st.link_button("Open Master Sheet ↗", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=1930217683")
            
            if not inventory_data.empty:
                filtered_df = inventory_data.copy()
                std_locations = ["Mainstage", "Studio Theater", "Sound Closet"]
                
                if loc_filter != "All Locations":
                    if loc_filter == "Elsewhere":
                        if "Current Location" in filtered_df.columns:
                            filtered_df = filtered_df[~filtered_df["Current Location"].isin(std_locations)]
                    else:
                        if "Current Location" in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df["Current Location"] == loc_filter]
                
                if search_query and "Item Name" in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df["Item Name"].str.contains(search_query, case=False, na=False)]
                
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Master list database offline.")
                
        with tab_log:
            st.subheader("Equipment Movement Audit Log")
            
            if not log_data.empty:
                log_search = st.text_input("Filter Log History", placeholder="Search by crew name, item, or destination...")
                
                display_log = log_data.copy()
                if log_search:
                    mask = display_log.astype(str).apply(lambda row: row.str.contains(log_search, case=False).any(), axis=1)
                    display_log = display_log[mask]
                
                st.dataframe(display_log, use_container_width=True, hide_index=True)
            else:
                st.info("No movement logs recorded yet.")
            
        with tab_info:
            st.subheader("System Information & Architecture")
            st.markdown("""
            **T.O.R.E.E. Engine Status:** Operational  
            **Active Subsystem:** Sound Department Equipment Tracking  
            **Database Syncing:** Direct Google Sheets CSV API  
            """)
    else:
        if admin_pass:
            st.error("Invalid Admin Key.")
