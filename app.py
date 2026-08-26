import streamlit as st
import yt_dlp
import os
import base64

st.set_page_config(
    page_title="Echo - Media Downloader",
    page_icon="haunter.png",
    layout="centered"
)

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

haunter_b64 = get_image_base64("haunter.jpg")

st.markdown("""
    <style>
    .stApp, header[data-testid="stHeader"] {
        background-color: #000000;
    }

    [data-testid="stHeader"] {
        display: none !important;
    }

    .stTextInput {
        margin-top: -30px;
    }

    .stTextInput div[data-baseweb="input"]:focus-within {
        border-color: #FF0000 !important;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.7) !important;
    }

    div[data-aria-hidden="true"], 
    .stTextInput div[data-testid="InputInstructions"] {
        display: none !important;
    }

    div.stButton {
        margin-top: -5px;
    }

    div.stButton > button, div.stDownloadButton > button {
        background-color: #FFFFFF;
        color: #000000;
        border-radius: 50px;
        border: none;
        font-weight: bold;
    }

    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #CCCCCC;
        color: #000000;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: flex-start;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #111111;
        color: #888888;
        border-radius: 8px 8px 0px 0px;
        padding: 8px 20px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #222222 !important;
        color: #FFFFFF !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0d0d0d;
        border: 1px solid #222222 !important;
        border-radius: 12px;
        padding: 15px;
    }

    [data-testid="stSpinner"] {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-top: 5px;
    }

    [data-testid="stHeaderActionElements"], .aria-hidden, a.anchor-link {
        display: none !important;
        visibility: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

def fetch_info(url):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def download_selected_media(url, is_audio, format_id):
    for file in os.listdir('.'):
        if file.startswith('temp_dl_'):
            try:
                os.remove(file)
            except Exception:
                pass

    out_name = f"temp_dl_{format_id}"

    if is_audio:
        ydl_opts = {
            'format': format_id,
            'outtmpl': f'{out_name}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
    else:
        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',
            'outtmpl': f'{out_name}.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for file in os.listdir('.'):
        if file.startswith(out_name):
            with open(file, "rb") as f:
                data = f.read()
            return data, file
    return None, None

left_col, center_col, right_col = st.columns([1, 4, 1])

with center_col:
    if haunter_b64:
        st.markdown(f"<div style='text-align: center;'><img src='data:image/jpeg;base64,{haunter_b64}' style='max-width: 100%; height: auto;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 80px; margin-top: -70px;margin-bottom: 0px;'>ECHO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: -30px; letter-spacing: 7px; color: #888888;'>Extract, Convert, Hear & Organize</p>", unsafe_allow_html=True)

    url_input = st.text_input(label="", placeholder="Paste your URL here...")

    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "video_info" not in st.session_state:
        st.session_state.video_info = None

    button_text = "Processing..." if st.session_state.is_processing else "Download Now"

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

    with btn_col2:
        if st.button(button_text):
            if url_input:
                st.session_state.is_processing = True
                try:
                    st.session_state.video_info = fetch_info(url_input)
                except Exception:
                    st.session_state.video_info = None
                st.session_state.is_processing = False
                st.rerun()

if st.session_state.video_info:
    info = st.session_state.video_info
    formats = info.get('formats', [])
    thumbnail_url = info.get('thumbnail')
    title = info.get('title', 'Video')

    video_formats = []
    seen_heights = set()
    for f in formats:
        h = f.get('height')
        if h and h not in seen_heights and f.get('vcodec') != 'none':
            seen_heights.add(h)
            video_formats.append({
                'res': f'{h}p',
                'id': f['format_id']
            })

    video_formats.sort(key=lambda x: int(x['res'].replace('p', '')), reverse=True)

    audio_formats = []
    seen_abrs = set()
    for f in formats:
        abr = f.get('abr')
        if abr and int(abr) not in seen_abrs and f.get('acodec') != 'none':
            seen_abrs.add(int(abr))
            audio_formats.append({
                'abr': f'{int(abr)} kbps',
                'id': f['format_id']
            })

    audio_formats.sort(key=lambda x: int(x['abr'].replace(' kbps', '')), reverse=True)

    with st.container(border=True):
        col_thumb, col_content = st.columns([1, 2])

        with col_thumb:
            if thumbnail_url:
                st.markdown(f"<img src='{thumbnail_url}' style='width: 100%; border-radius: 8px;'>", unsafe_allow_html=True)

        with col_content:
            st.markdown(f"<h4 style='color: #FFFFFF; margin-top: 0px;'>{title}</h4>", unsafe_allow_html=True)
            tab_mp4, tab_mp3 = st.tabs(["Video (MP4)", "Audio (MP3)"])

            with tab_mp4:
                for item in video_formats:
                    col_info, col_btn = st.columns([2, 2])
                    with col_info:
                        st.markdown(f"<p style='margin-top: 5px; color: #FFFFFF;'>mp4 ({item['res']})</p>", unsafe_allow_html=True)
                    with col_btn:
                        sub_col_msg, sub_col_btn = st.columns([0.2, 1])
                        btn_key = f"btn_v_{item['id']}"
                        ready_key = f"ready_v_{item['id']}"

                        if ready_key not in st.session_state:
                            with sub_col_btn:
                                btn_clicked = st.button("Download", key=btn_key)
                            if btn_clicked:
                                with sub_col_msg:
                                    with st.spinner(""):
                                        data, file_name = download_selected_media(url_input, False, item['id'])
                                        if data:
                                            st.session_state[ready_key] = (data, file_name)
                                            st.rerun()
                        else:
                            with sub_col_btn:
                                data, file_name = st.session_state[ready_key]
                                ext = file_name.split('.')[-1]
                                st.download_button(
                                    label="Save File",
                                    data=data,
                                    file_name=f"{title}_{item['res']}.{ext}",
                                    mime=f"video/{ext}",
                                    key=f"dl_v_{item['id']}"
                                )

            with tab_mp3:
                for item in audio_formats:
                    col_info, col_btn = st.columns([2, 2])
                    with col_info:
                        st.markdown(f"<p style='margin-top: 5px; color: #FFFFFF;'>mp3 ({item['abr']})</p>", unsafe_allow_html=True)
                    with col_btn:
                        sub_col_msg, sub_col_btn = st.columns([0.2, 1])
                        btn_key = f"btn_a_{item['id']}"
                        ready_key = f"ready_a_{item['id']}"

                        if ready_key not in st.session_state:
                            with sub_col_btn:
                                btn_clicked = st.button("Download", key=btn_key)
                            if btn_clicked:
                                with sub_col_msg:
                                    with st.spinner(""):
                                        data, file_name = download_selected_media(url_input, True, item['id'])
                                        if data:
                                            st.session_state[ready_key] = (data, file_name)
                                            st.rerun()
                        else:
                            with sub_col_btn:
                                data, file_name = st.session_state[ready_key]
                                st.download_button(
                                    label="Save File",
                                    data=data,
                                    file_name=f"{title}_{item['abr']}.mp3",
                                    mime="audio/mpeg",
                                    key=f"dl_a_{item['id']}"
                                )