import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwJQvf7vIjUdqajyzqCoOdNET233DNCpi5B3II_tvsbtUWnNzUoh2nr3HvB5O4hiYjbgQ/exec"
BG_COLOR = "#001432" # DGS Navy Blue
ACCENT_COLOR = "#FFFFFF"

# Must be the first Streamlit command
st.set_page_config(page_title="T.O.R.E.E.", layout="wide", initial_sidebar_state="collapsed")

# --- Initialize Session State for Easter Egg ---
if 'horse_mode' not in st.session_state:
    st.session_state.horse_mode = False

# --- Easter Egg Screen ---
if st.session_state.horse_mode:
    # Full screen pink override
    st.markdown("""
        <style>
        .stApp { background-color: #FF69B4 !important; }
        .horse-text {
            font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
            font-size: 8rem;
            color: white;
            text-align: center;
            margin-top: 20vh;
        }
        header { visibility: hidden; }
        </style>
        <div class="horse-text">Horse</div>
    """, unsafe_allow_html=True)
    
    # Button to go back
    if st.button("Return to T.O.R.E.E."):
        st.session_state.horse_mode = False
        st.rerun()
    st.stop() # Stops rendering the rest of the app

# --- Custom CSS Styling ---
st.markdown(f"""
    <style>
    /* DGS Theme */
    .stApp {{ background-color: {BG_COLOR}; color: {ACCENT_COLOR}; }}
    
    /* Overriding text colors for inputs and tables to ensure readability */
    h1, h2, h3, p, label {{ color: {ACCENT_COLOR} !important; }}
    
    /* Master Log Retro Font */
    .retro-log {{
        background-color: black;
        color: #33ff33;
        font-family: 'Courier New', Courier, monospace; /* Closest web-safe equivalent to Apple 1 */
        padding: 10px;
        border-radius: 5px;
        height: 600px;
        overflow-y: auto;
        white-space: pre-wrap;
    }}
    
    /* Vertical separator line */
    .vertical-line {{
        border-left: 2px solid gray;
        height: 100%;
        min-height: 800px;
    }}

    /* Tiny invisible button in top right */
    .hidden-btn-container {{
        position: absolute;
        top: 0px;
        right: 0px;
        z-index: 99999;
    }}
    /* Target the streamlit button inside the container */
    .hidden-btn-container button {{
        opacity: 0;
        width: 10px !important;
        height: 10px !important;
        padding: 0 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Easter Egg Button Trigger ---
# This injects a tiny invisible container at the absolute top right
col_egg = st.container()
with col_egg:
    st.markdown('<div class="hidden-btn-container">', unsafe_allow_html=True)
    if st.button(" "): # Invisible button
        st.session_state.horse_mode = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- Data Fetching & Updating Functions ---
@st.cache_data(ttl=10) # Caches for 10 seconds to avoid spamming Google API, adjust as needed
def fetch_data():
    try:
        response = requests.get(APPS_SCRIPT_URL)
        return response.json()
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")
        return {"inventory": [], "logs": []}

def update_item(dept, item_id, item_name, status, loc):
    payload = {
        "department": dept,
        "item_id": item_id,
        "item_name": item_name,
        "status": status,
        "location": loc
    }
    try:
        requests.post(APPS_SCRIPT_URL, json=payload)
        st.cache_data.clear() # Force refresh data on next load
        st.rerun()
    except Exception as e:
        st.error(f"Failed to update item: {e}")


# --- Main Application Layout ---
data = fetch_data()
inventory = data.get("inventory", [])
logs = data.get("logs", [])

# Layout columns: Left (6 parts), Separator (0.1 parts), Right (3 parts)
col_main, col_line, col_log = st.columns([6, 0.1, 3])

# --- LEFT COLUMN: Main List & Editor ---
with col_main:
    st.title("T.O.R.E.E. INVENTORY")
    
    # Search functionality
    search_term = st.text_input("🔍 Search Inventory", "")
    
    # Filter data based on search
    if search_term:
        filtered_inv = [item for item in inventory if search_term.lower() in str(item.values()).lower()]
    else:
        filtered_inv = inventory

    # Display Data Table
    if filtered_inv:
        df = pd.DataFrame(filtered_inv)
        # Rename columns for cleaner display
        df = df.rename(columns={
            "department": "Dept", "item_id": "ID", "item_name": "Name", 
            "status": "Status", "location": "Location", "original_location": "Orig. Loc"
        })
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("No items found.")

    st.markdown("---")
    st.subheader("Update Item")
    
    if inventory:
        # Create a dictionary mapping a readable string to the actual item dictionary
        item_options = {f"[{item['department']}] {item['item_id']} - {item['item_name']}": item for item in inventory}
        
        selected_item_str = st.selectbox("Select Item to Update", options=list(item_options.keys()))
        selected_item = item_options[selected_item_str]

        # Update Form
        with st.form("update_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                # Pre-fill with current status
                current_status_idx = ["in use", "inactive", "unknown"].index(selected_item["status"]) if selected_item["status"] in ["in use", "inactive", "unknown"] else 0
                new_status = st.selectbox("Status", ["in use", "inactive", "unknown"], index=current_status_idx)
            with col_f2:
                # Pre-fill with current location
                loc_list = ["Mainstage", "Studio Theater", "Supply Closet", "Elsewhere"]
                current_loc_idx = loc_list.index(selected_item["location"]) if selected_item["location"] in loc_list else 0
                new_loc = st.selectbox("Location", loc_list, index=current_loc_idx)
            
            submit = st.form_submit_button("Update Item")
            if submit:
                update_item(
                    selected_item["department"], 
                    selected_item["item_id"], 
                    selected_item["item_name"], 
                    new_status, 
                    new_loc
                )

# --- SEPARATOR COLUMN ---
with col_line:
    st.markdown('<div class="vertical-line"></div>', unsafe_allow_html=True)

# --- RIGHT COLUMN: Master Log ---
with col_log:
    st.title("MASTER LOG")
    
    # Format logs (newest at top)
    log_text = "\n".join(reversed(logs)) if logs else "No logs available."
    
    # Display in retro style
    st.markdown(f'<div class="retro-log">{log_text}</div>', unsafe_allow_html=True)
    
    if st.button("Refresh Live Data"):
        st.cache_data.clear()
        st.rerun()
