import streamlit as st
import pandas as pd
import boto3
from io import BytesIO
from PIL import Image
from streamlit_image_zoom import image_zoom


# AWS Configuration
BUCKET_NAME = "inference-1"
DYNAMODB_TABLE = "data_logs"


# Initialize AWS Clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

dynamodb = boto3.resource("dynamodb",aws_access_key_id=AWS_ACCESS_KEY_ID,
aws_secret_access_key=AWS_SECRET_ACCESS_KEY,region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

def fetch_s3_file(s3_url):
    try:
        bucket, key = s3_url.replace("s3://", "").split("/", 1)
        response = s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    except Exception:
        return None

def query_dynamodb(block_id):
    table = dynamodb.Table(DYNAMODB_TABLE)
    response = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr('block_id').eq(block_id))
    return response.get("Items", [])


# Set page title
st.set_page_config(page_title='Defect Inspection', layout='wide', initial_sidebar_state='collapsed')

st.markdown("""
    <style>
        body {
            background-color: black !important;
            color: white !important;
        }
        .block-container {
            border-bottom: 2px solid #ccc;
            padding: 50px;
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

if block_number:
    items = query_dynamodb(block_number)
    if not items:
        st.warning("No data found for the given Block ID.")
    else:
        item = items[0]  # Assuming one entry per block_id
        image_url = item.get("image_url_location", "")
        mask_url = item.get("mask_url_location", "")
        localized_url = item.get("localized_url_location", "")
        report_url = item.get("report_url_location", "")
        
        csv_data = fetch_s3_file(report_url) if report_url else None
        if csv_data:
            df = pd.read_csv(BytesIO(csv_data))
            status_col.markdown("### 🔴 FAIL" if not df.empty else "### 🟢 PASS", unsafe_allow_html=True)
            st.markdown('<div class="section">', unsafe_allow_html=True)
        else:
            status_col.markdown("### 🟢 PASS", unsafe_allow_html=True)
            st.markdown('<div class="section">', unsafe_allow_html=True)

        col4, col5 = st.columns([0.6, 0.7])
        with col4:
            #st.markdown('<div class="section">', unsafe_allow_html=True)
            st.markdown("### Defect Visualization", unsafe_allow_html=True)
            #st.markdown('<div class="section">', unsafe_allow_html=True)
            show_mask = st.toggle("Show Mask Overlay", key="mask_toggle")
            try:
                image_data = fetch_s3_file(localized_url) if localized_url else None
                base_image = Image.open(BytesIO(image_data)).convert("RGBA") if image_data else None
                if base_image:
                    mask_data = fetch_s3_file(mask_url) if mask_url and show_mask else None
                    if mask_data:
                        mask_image = Image.open(BytesIO(mask_data)).convert("RGBA")
                        mask_image = mask_image.resize(base_image.size)
                        blended_image = Image.blend(base_image, mask_image, alpha=0.6)
                        image_zoom(blended_image, mode="scroll", size=(700, 500), keep_aspect_ratio=True, zoom_factor=8.0, increment=0.8)
                        # Display
                        st.image(resized_image, channels="BGR", use_column_width=True)
                        
                    else:
                        image_zoom(base_image, mode="scroll", size=(700, 500), keep_aspect_ratio=True, zoom_factor=8.0, increment=0.8)
                else:
                    st.warning("Localized image not found.")
            except Exception as e:
                st.error(f"Error loading images: {e}")
        
        with col5:
            #st.markdown('<div class="section">', unsafe_allow_html=True)
            st.markdown("### Defect Report", unsafe_allow_html=True)
            #st.markdown('<div class="section">', unsafe_allow_html=True)
            if csv_data:
                st.table(pd.read_csv(BytesIO(csv_data)))
            else:
                st.info("No defect report found.")
