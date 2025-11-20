import streamlit as st
from sqlalchemy import create_engine

# Load secure DB URL from Streamlit secrets
DATABASE_URL = st.secrets["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
