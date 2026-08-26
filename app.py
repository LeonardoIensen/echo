import streamlit as st

st.markdown("""
    <style>
    .stApp, header[data-testid="stHeader"] {
        background-color: #000000;
    }
    </style>
""", unsafe_allow_html=True)

left_col, center_col, right_col = st.columns([1, 4, 1])

with center_col:
    st.image("haunter.jpg")
    st.markdown("<h1 style='text-align: center; font-size: 80px; margin-top: -80px;margin-bottom: 0px;'>ECHO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: -40px; letter-spacing: 7px; color: #888888;'>Extract, Convert, Hear & Organize</p>", unsafe_allow_html=True)