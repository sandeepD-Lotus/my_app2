import streamlit as st
import pandas as pd
import boto3
from io import BytesIO
from PIL import Image
from streamlit_image_zoom import image_zoom

# AWS S3 Configuration
BUCKET_NAME = "data-reference-1"
IMAGE_PREFIX = "images/"
MASK_PREFIX = "masks/"
CSV_PREFIX = "csvs/"

# # Initialize S3 Client
s3 = boto3.client("s3")



# Set page title
st.set_page_config(page_title='Defect Inspection', layout='wide', initial_sidebar_state='collapsed')

# --- Custom CSS ---
st.markdown("""
    <style>
        body {
            background-color: black !important;
            color: white !important;
        }
        .block-container {
            border-bottom: 2px solid #ccc;
            padding: 1px;
            background-color: black !important;
            color: white !important;
        }
        .section {
            border-bottom: 2px solid #aaa;
            padding: 2px;
            margin-bottom: 1px;
            background-color: #333 !important;
            color: white !important;
        }
        div[data-testid="stTextInput"] input {
            font-size: 14px !important;
            padding: 5px 8px !important;
            height: 30px !important;
            width: 200px !important;
            border-bottom: 2px solid #007BFF !important;
            background-color: #222 !important;
            color: white !important;
        }
        div[data-testid="stButton"] button {
            border-bottom: 2px solid #007BFF !important;
            background-color: #444 !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- UI Layout ---
# --- UI Layout ---
st.markdown("###  ", unsafe_allow_html=True)
#st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown("### Porosity Defect Inspection", unsafe_allow_html=True)
st.markdown('<div class="section">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([3, 1, 1])

if "block_number" not in st.session_state:
    st.session_state.block_number = ""

with col1:
    block_number = st.text_input("Enter Block Number...", key="search_input", label_visibility="collapsed")
with col2:
    search = st.button("Search")
with col3:
    status_col = st.empty()

if search and block_number:
    st.session_state.block_number = block_number

block_number = st.session_state.block_number

# Function to fetch files from S3
def fetch_s3_file(bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    except Exception:
        return None

if block_number:
    image_key = f"{IMAGE_PREFIX}{block_number}-localized.png"
    mask_key = f"{MASK_PREFIX}{block_number}-mask.png"
    csv_key = f"{CSV_PREFIX}{block_number}-report.csv"

    # Fetch CSV Report
    csv_data = fetch_s3_file(BUCKET_NAME, csv_key)
    if csv_data:
        df = pd.read_csv(BytesIO(csv_data))
        status_col.markdown("### 🔴 FAIL" if not df.empty else "### 🟢 PASS", unsafe_allow_html=True)
    else:
        status_col.markdown("### 🟢 PASS", unsafe_allow_html=True)

    col4, col5 = st.columns([0.6, 0.8])
    
    with col4:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### Defect Visualization", unsafe_allow_html=True)
        show_mask = st.toggle("Show Mask Overlay", key="mask_toggle")
        
        try:
            # Fetch Base Image
            image_data = fetch_s3_file(BUCKET_NAME, image_key)
            base_image = Image.open(BytesIO(image_data)).convert("RGBA") if image_data else None

            if not base_image:
                st.warning("Localized image not found.")
            
            # Fetch Mask Image
            mask_data = fetch_s3_file(BUCKET_NAME, mask_key)
            if show_mask and base_image and mask_data:
                mask_image = Image.open(BytesIO(mask_data)).convert("RGBA")
                mask_image = mask_image.resize(base_image.size)
                blended_image = Image.blend(base_image, mask_image, alpha=0.6)
                image_zoom(blended_image, mode="scroll", size=(700, 500), keep_aspect_ratio=True, zoom_factor=8.0, increment=0.8)
            elif base_image:
                image_zoom(base_image, mode="scroll", size=(700, 500), keep_aspect_ratio=True, zoom_factor=8.0, increment=0.8)
        except Exception as e:
            st.error(f"Error loading images: {e}")
    
    with col5:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### Defect Report", unsafe_allow_html=True)
        if csv_data:
            st.table(pd.read_csv(BytesIO(csv_data)))
        else:
            st.info("No defect report found.")
