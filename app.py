import streamlit as st
import yt_dlp
import os
import base64
import whisper
import urllib.parse
import streamlit.components.v1 as components
from dotenv import load_dotenv
from google import genai
import subprocess

load_dotenv()

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

haunter_b64 = get_image_base64("haunter.png")

st.markdown("""
    <style>
    .stApp, header[data-testid="stHeader"] {
        background-color: #000000;
    }

    [data-testid="stHeader"] {
        display: none !important;
    }

    .stTextInput {
        margin-top: 15px;
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
        margin-top: 0px;
    }

    div.stButton > button, div.stDownloadButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 50px !important;
        border: none !important;
        font-weight: normal !important;
        width: 100% !important;
        height: 38px !important;
        padding: 0px 16px !important;
        font-size: 14px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
    }

    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #CCCCCC !important;
        color: #000000 !important;
    }

    /* Oculta completamente o file_uploader original */
    [data-testid="stFileUploader"] {
        display: none !important;
    }

    /* Sobe a coluna do botão de upload via layout sem cortar o topo */
    [data-testid="column"]:has([data-testid="stFileUploader"]) {
        transform: translateY(-2px);
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
        margin-bottom: 20px;
    }

    [data-testid="stSpinner"] {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-top: 10px;
    }

    [data-testid="stHeaderActionElements"], .aria-hidden, a.anchor-link {
        display: none !important;
        visibility: hidden !important;
    }

    textarea {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        resize: none !important;
    }

    .summary-expanded-box {
        margin-left: -100px;
        margin-right: -100px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
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
            try:
                os.remove(file)
            except Exception:
                pass
            return data, file
    return None, None

@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

def extract_audio_from_local_file(uploaded_file):
    ext = uploaded_file.name.rsplit('.', 1)[-1].lower()
    
    if ext == "mp3":
        return uploaded_file.getbuffer()
        
    temp_input = f"temp_uploaded_{uploaded_file.name}"
    temp_output = "temp_local_audio.mp3"
    
    with open(temp_input, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    cmd = f'ffmpeg -y -i "{temp_input}" -vn -ar 44100 -ac 2 -b:a 192k "{temp_output}"'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(temp_input):
        os.remove(temp_input)
        
    if os.path.exists(temp_output):
        with open(temp_output, "rb") as f:
            data = f.read()
        os.remove(temp_output)
        return data
    return None

def get_audio_text(url=None, uploaded_file=None):
    for file in os.listdir('.'):
        if file.startswith('temp_ai_'):
            try:
                os.remove(file)
            except Exception:
                pass

    audio_file = "temp_ai_audio.mp3"
    
    if uploaded_file:
        audio_data = extract_audio_from_local_file(uploaded_file)
        if audio_data:
            with open(audio_file, "wb") as f:
                f.write(audio_data)
    elif url:
        out_name = "temp_ai_audio"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{out_name}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        for file in os.listdir('.'):
            if file.startswith(out_name) and file.endswith('.mp3'):
                audio_file = file
                break

    if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
        return None

    model = load_whisper_model()
    result = model.transcribe(audio_file)

    try:
        os.remove(audio_file)
    except Exception:
        pass

    return result.get("text", "").strip()

def generate_summary(text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Erro: GEMINI_API_KEY não foi encontrada no seu arquivo .env."

    client = genai.Client(api_key=api_key)
    prompt = (
        "Analyze the language of the transcript below and generate a well-structured summary "
        "written ENTIRELY in the SAME LANGUAGE as the transcript.\n"
        "Organize it into clear, direct bullet points and highlight key takeaways like a guide or lesson.\n"
        "ABSOLUTE RULE: DO NOT write any intro, greeting, notice, or setup commentary "
        "(such as 'Here is a summary...', 'Based on the text...', 'Aqui está o resumo...'). "
        "Start DIRECTLY with the main title of the summary.\n\n"
        f"Transcript:\n{text}"
    )
    
    models_to_try = ['gemini-3.6-flash', 'gemini-3.7-flash']

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                continue
            return f"Erro ao gerar resumo: {str(e)}"

    return "Servidores do Gemini temporariamente congestionados. Tente novamente em alguns instantes."

left_col, center_col, right_col = st.columns([1, 4, 1])

with center_col:
    if haunter_b64:
        st.markdown(f"<div style='text-align: center;'><img src='data:image/png;base64,{haunter_b64}' style='max-width: 100%; height: auto;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 80px; margin-top: -70px;margin-bottom: 0px;'>ECHO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: -30px; letter-spacing: 7px; color: #888888;'>Extract, Convert, Hear & Organize</p>", unsafe_allow_html=True)

    input_col, upload_col = st.columns([8.8, 1.2])
    
    with input_col:
        url_input = st.text_input(label="URL", label_visibility="collapsed", placeholder="Paste your URL here...", autocomplete="off")
    
    with upload_col:
        uploaded_file = st.file_uploader("", type=["mp4", "mp3"], label_visibility="collapsed", key="file_up_hidden")
        
        components.html("""
            <style>
                body { margin: 0; padding: 0; background: transparent; overflow: hidden; display: flex; align-items: center; justify-content: center; }
                .custom-upload-btn {
                    background-color: #111111;
                    color: #FFFFFF;
                    border: 1px solid #333333;
                    border-radius: 8px;
                    height: 42px;
                    width: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    margin-top: 0px;
                    box-sizing: border-box;
                }
                .custom-upload-btn:hover {
                    border-color: #555555;
                    background-color: #1a1a1a;
                }
                .custom-upload-btn svg {
                    width: 18px;
                    height: 18px;
                    fill: #FFFFFF;
                }
            </style>
            <div class="custom-upload-btn" onclick="window.parent.document.querySelector('input[type=file]').click()">
                <svg viewBox="0 0 24 24">
                    <path d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/>
                </svg>
            </div>
        """, height=60)

    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "video_info" not in st.session_state:
        st.session_state.video_info = None
    if "is_local_file" not in st.session_state:
        st.session_state.is_local_file = False
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "transcript_text" not in st.session_state:
        st.session_state.transcript_text = None
    if "summary_text" not in st.session_state:
        st.session_state.summary_text = None

    default_btn_label = "Process Media" if uploaded_file else "Download Now"
    button_text = "Processing..." if st.session_state.is_processing else default_btn_label

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

    with btn_col2:
        if st.button(button_text):
            st.session_state.is_processing = True
            st.session_state.error_message = None
            st.session_state.transcript_text = None
            st.session_state.summary_text = None
            
            if uploaded_file:
                st.session_state.is_local_file = True
                ext = uploaded_file.name.rsplit('.', 1)[-1].lower()
                st.session_state.video_info = {
                    'title': uploaded_file.name.rsplit('.', 1)[0],
                    'file_obj': uploaded_file,
                    'file_type': ext
                }
            elif url_input:
                st.session_state.is_local_file = False
                try:
                    st.session_state.video_info = fetch_info(url_input)
                except Exception:
                    st.session_state.video_info = None
                    st.session_state.error_message = "Invalid URL or video unavailable."
            else:
                st.session_state.error_message = "Please provide a URL or upload a file."
                
            st.session_state.is_processing = False
            st.rerun()

    if st.session_state.error_message:
        st.markdown(f"<p style='color: #FF4B4B; text-align: center; margin-top: 10px;'>{st.session_state.error_message}</p>", unsafe_allow_html=True)

if st.session_state.video_info:
    info = st.session_state.video_info
    title = info.get('title', 'Media File')
    is_local = st.session_state.is_local_file

    with st.container(border=True):
        if is_local:
            st.markdown(f"<h4 style='color: #FFFFFF; margin-top: 0px;'>{title}</h4>", unsafe_allow_html=True)
            file_type = info.get('file_type', 'mp4')
            
            if file_type == "mp3":
                tabs = st.tabs(["AI Tools"])
                tab_ai = tabs[0]
            else:
                tabs = st.tabs(["Audio (MP3)", "AI Tools"])
                tab_mp3, tab_ai = tabs[0], tabs[1]
                
                with tab_mp3:
                    col_info, col_btn = st.columns([2, 2])
                    with col_info:
                        st.markdown("<p style='margin-top: 5px; color: #FFFFFF;'>mp3 (192 kbps)</p>", unsafe_allow_html=True)
                    with col_btn:
                        sub_col_msg, sub_col_btn = st.columns([0.2, 1])
                        ready_key = "ready_local_mp3"
                        if ready_key not in st.session_state:
                            with sub_col_btn:
                                btn_clicked = st.button("Convert", key="btn_local_mp3")
                            if btn_clicked:
                                with sub_col_msg:
                                    with st.spinner(""):
                                        audio_bytes = extract_audio_from_local_file(info['file_obj'])
                                        if audio_bytes:
                                            st.session_state[ready_key] = audio_bytes
                                            st.rerun()
                        else:
                            with sub_col_btn:
                                st.download_button(
                                    label="Save File",
                                    data=st.session_state[ready_key],
                                    file_name=f"{title}.mp3",
                                    mime="audio/mpeg",
                                    key="dl_local_mp3"
                                )
        else:
            formats = info.get('formats', [])
            thumbnail_url = info.get('thumbnail')

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

            col_thumb, col_content = st.columns([1, 2.5])

            with col_thumb:
                if thumbnail_url:
                    st.markdown(f"<img src='{thumbnail_url}' style='width: 100%; border-radius: 8px;'>", unsafe_allow_html=True)

            with col_content:
                st.markdown(f"<h4 style='color: #FFFFFF; margin-top: 0px;'>{title}</h4>", unsafe_allow_html=True)
                tab_mp4, tab_mp3, tab_ai = st.tabs(["Video (MP4)", "Audio (MP3)", "AI Tools"])

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

        with tab_ai:
            if "transcribing" not in st.session_state:
                st.session_state.transcribing = False
            if "summarizing" not in st.session_state:
                st.session_state.summarizing = False

            col_ai_txt, col_ai_btn = st.columns([2, 2])
            with col_ai_txt:
                st.markdown("<p style='margin-top: 5px; color: #FFFFFF;'>Transcribe Audio</p>", unsafe_allow_html=True)
            with col_ai_btn:
                sub_col_sp1, sub_col_b1 = st.columns([0.2, 1])
                with sub_col_b1:
                    btn_trans = st.button("Transcribe", key="btn_ai_transcribe")

                if btn_trans:
                    st.session_state.transcribing = True

                if st.session_state.transcribing:
                    with sub_col_sp1:
                        with st.spinner(""):
                            if is_local:
                                st.session_state.transcript_text = get_audio_text(uploaded_file=info['file_obj'])
                            else:
                                st.session_state.transcript_text = get_audio_text(url=url_input)
                            st.session_state.transcribing = False
                            st.rerun()

            col_sum_txt, col_sum_btn = st.columns([2, 2])
            with col_sum_txt:
                st.markdown("<p style='margin-top: 5px; color: #FFFFFF;'>Generate Summary</p>", unsafe_allow_html=True)
            with col_sum_btn:
                sub_col_sp2, sub_col_b2 = st.columns([0.2, 1])
                with sub_col_b2:
                    btn_sum = st.button("Summarize", key="btn_ai_summary")

                if btn_sum:
                    st.session_state.summarizing = True

                if st.session_state.summarizing:
                    with sub_col_sp2:
                        with st.spinner(""):
                            if is_local:
                                raw_text = get_audio_text(uploaded_file=info['file_obj'])
                            else:
                                raw_text = get_audio_text(url=url_input)
                                
                            if raw_text:
                                st.session_state.summary_text = generate_summary(raw_text)
                            else:
                                st.session_state.summary_text = "Error: Could not extract audio for summary."
                            st.session_state.summarizing = False
                            st.rerun()

    if st.session_state.transcript_text:
        with st.container(border=True):
            st.markdown("<h4 style='color: #FFFFFF; margin-top: 0px;'>Transcription Result</h4>", unsafe_allow_html=True)
            st.text_area("Transcription", st.session_state.transcript_text, height=200, key="txt_result_area", label_visibility="collapsed")

            col_cp, col_dl, col_empty = st.columns([1, 1, 7])

            with col_cp:
                encoded_text = urllib.parse.quote(st.session_state.transcript_text)
                components.html(f"""
                    <style>
                        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
                        .copy-btn {{
                            background-color: #FFFFFF; color: #000000; border-radius: 50px; border: none;
                            font-weight: normal !important; width: 60px; height: 38px; font-size: 14px;
                            cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                            display: flex; align-items: center; justify-content: center; box-sizing: border-box;
                        }}
                        .copy-btn:hover {{ background-color: #CCCCCC; }}
                    </style>
                    <button class="copy-btn" id="btnCopy">Copy</button>
                    <script>
                        document.getElementById('btnCopy').addEventListener('click', function() {{
                            const text = decodeURIComponent('{encoded_text}');
                            if (navigator.clipboard && window.isSecureContext) {{
                                navigator.clipboard.writeText(text).then(() => {{
                                    this.innerText = 'Copied!';
                                    setTimeout(() => {{ this.innerText = 'Copy'; }}, 2000);
                                }});
                            }} else {{
                                const el = document.createElement('textarea');
                                el.value = text;
                                document.body.appendChild(el);
                                el.select();
                                document.execCommand('copy');
                                document.body.removeChild(el);
                                this.innerText = 'Copied!';
                                setTimeout(() => {{ this.innerText = 'Copy'; }}, 2000);
                            }}
                        }});
                    </script>
                """, height=38)

            with col_dl:
                st.download_button(
                    label="Save",
                    data=st.session_state.transcript_text,
                    file_name=f"{title}_transcription.txt",
                    mime="text/plain",
                    key="dl_transcript_file"
                )

    if st.session_state.summary_text:
        st.markdown('<div class="summary-expanded-box">', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(st.session_state.summary_text)

            col_cp_s, col_dl_s, col_empty_s = st.columns([1, 1, 7])

            with col_cp_s:
                encoded_summary = urllib.parse.quote(st.session_state.summary_text)
                components.html(f"""
                    <style>
                        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
                        .copy-btn {{
                            background-color: #FFFFFF; color: #000000; border-radius: 50px; border: none;
                            font-weight: normal !important; width: 60px; height: 38px; font-size: 14px;
                            cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                            display: flex; align-items: center; justify-content: center; box-sizing: border-box;
                        }}
                        .copy-btn:hover {{ background-color: #CCCCCC; }}
                    </style>
                    <button class="copy-btn" id="btnCopySum">Copy</button>
                    <script>
                        document.getElementById('btnCopySum').addEventListener('click', function() {{
                            const text = decodeURIComponent('{encoded_summary}');
                            if (navigator.clipboard && window.isSecureContext) {{
                                navigator.clipboard.writeText(text).then(() => {{
                                    this.innerText = 'Copied!';
                                    setTimeout(() => {{ this.innerText = 'Copy'; }}, 2000);
                                }});
                            }} else {{
                                const el = document.createElement('textarea');
                                el.value = text;
                                document.body.appendChild(el);
                                el.select();
                                document.execCommand('copy');
                                document.body.removeChild(el);
                                this.innerText = 'Copied!';
                                setTimeout(() => {{ this.innerText = 'Copy'; }}, 2000);
                            }}
                        }});
                    </script>
                """, height=38)

            with col_dl_s:
                st.download_button(
                    label="Save",
                    data=st.session_state.summary_text,
                    file_name=f"{title}_summary.txt",
                    mime="text/plain",
                    key="dl_summary_file"
                )
        st.markdown('</div>', unsafe_allow_html=True)