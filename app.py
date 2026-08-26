import streamlit as st

st.markdown("""
    <style>
    .stApp, header[data-testid="stHeader"] {
        background-color: #000000;
    }

    .stTextInput {
        margin-top: -30px;
    }

    div.stButton {
        margin-top: -5px;
    }

    div.stButton > button {
        background-color: #FFFFFF;
        color: #000000;
        border-radius: 50px;
        border: none;
        font-weight: bold;

    }

    div.stButton > button:hover {
        background-color: #CCCCCC;
        color: #000000;
    }
    </style>
""", unsafe_allow_html=True)

left_col, center_col, right_col = st.columns([1, 4, 1])

with center_col:
    st.image("haunter.jpg")
    st.markdown("<h1 style='text-align: center; font-size: 80px; margin-top: -80px;margin-bottom: 0px;'>ECHO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: -30px; letter-spacing: 7px; color: #888888;'>Extract, Convert, Hear & Organize</p>", unsafe_allow_html=True)

    url_input = st.text_input(label="", placeholder="Paste your URL here...")
    
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    
    with btn_col2:
        if st.button("Download Now"):
            st.write("Processing link:", url_input)