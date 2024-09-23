import asyncio
import streamlit as st

from constants import KNOWLEDGE_BASE_PATH
from utils import update_state
from rags.text_rag import save_processed_document
from video_processing.ingest_video import process_video, process_uploaded_media


def provide_post_process_info(media_label, media_paths):
    file_content = {'media_label': f"{media_label}", 'content': media_paths}
    print(f'file_content: {file_content}')
    st.success("Media uploaded successfully!")
    st.info("You can now go to the knowledge base and ask questions about the media.")

def update_knowledge_base(media_label, media_paths):
    if "knowledge_base" not in st.session_state:
        st.session_state.knowledge_base = {}
    st.session_state.knowledge_base.setdefault(media_label, {})
    for media_type, paths in media_paths.items():
        st.session_state.knowledge_base[media_label].setdefault(media_type, []).extend(paths)
    update_state(KNOWLEDGE_BASE_PATH, st.session_state.knowledge_base)
    save_processed_document(media_label, media_paths["text_paths"])


def process_content(is_youtube_link, media_label, content):
    if is_youtube_link:
        video_path, audio_path, text_path = process_video(content)
    else:
        video_path, audio_path, text_path = process_uploaded_media(content)

    media_paths = {
        "audio_paths": [audio_path],
        "text_paths": [text_path]
    }
    if audio_path != video_path:
        media_paths["video_paths"] = [video_path]

    provide_post_process_info(media_label, media_paths)
    update_knowledge_base(media_label, media_paths)

def setup_media_processor_page():
    app_header = st.container()
    file_handler = st.form(key='file_handler')

    with app_header:
        st.title("📝 Media Processor ")
        st.markdown("##### Extract text from video and audio files")
        
    with file_handler:
        media_label = st.text_input(label="Media Tag", placeholder="Enter a required label or tag to identify the media")
        youtube_link = st.text_input(label="🔗 YouTube Link",
                                                    placeholder="Enter your YouTube link to download the video and extract the audio")
        uploaded_media = st.file_uploader("📁 Upload your file", type=['mp4', 'wav'])
        submit_button = st.form_submit_button(label="Process Media")

        if media_label and submit_button and (youtube_link or uploaded_media):
            if youtube_link and uploaded_media:
                st.warning("Either enter a YouTube link or upload a file, not both.")
            elif youtube_link:
                print(f'media_label: {media_label}')
                print(f'youtube_link: {youtube_link}')
                with st.spinner("🔍 Extracting transcript...(might take a while)"):
                    process_content(is_youtube_link=True, media_label=media_label, content=youtube_link)
            else:
                with st.spinner("🔍 Reading file... (might take a while)"):
                    process_content(is_youtube_link=False, media_label=media_label, content=uploaded_media)
setup_media_processor_page()
