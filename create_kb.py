import os
import re
import argparse

from constants import KNOWLEDGE_BASE_PATH
from recall_utils import update_state
from video_index.rags.text_rag import save_processed_document, generate_tags_and_images
from video_index.video_processing.ingest_video import save_uploaded_media, Video
from dotenv import load_dotenv
load_dotenv()

session_state = {}
def provide_post_process_info(media_label, media_paths):
    file_content = {'media_label': f"{media_label}", 'content': media_paths}
    print(f'file_content: {file_content}')

def update_knowledge_base(media_label, media_paths):
    global session_state
    if "knowledge_base" not in session_state:
        session_state["knowledge_base"] = {}
    if "indexes" not in session_state:
        session_state["indexes"] = {}
    session_state["knowledge_base"].setdefault(media_label, {})
    for media_type, paths in media_paths.items():
        session_state["knowledge_base"][media_label].setdefault(media_type, []).extend(paths)
    save_processed_document(media_label, media_paths["video_paths"], session_state["indexes"])
    tags_and_imgs = generate_tags_and_images(media_label, session_state["indexes"])
    session_state["knowledge_base"][media_label]["tags"] = tags_and_imgs["tags"]
    session_state["knowledge_base"][media_label]["title_image"] = tags_and_imgs["title_image"]
    update_state(KNOWLEDGE_BASE_PATH, session_state["knowledge_base"])

def process_content(is_youtube_link, media_label, content):
    storage_root_path='./events_kb'
    media_label_path = re.sub(r'[^a-zA-Z0-9]', '_', media_label)
    storage_path = os.path.join(storage_root_path, media_label_path)
    video_paths = []
    audio_paths = []
    text_paths = []
    video_urls = []
    
    if is_youtube_link:
        youtube_links = content.split(',')

        for youtube_link in youtube_links:
            video = Video.from_url(youtube_link.strip())
            try:
                video.download()
            except Exception as e:
                print(f"Failed to download video: {e}: {youtube_link}")
                continue
            video_path, audio_path, text_path = video.process_video_with_index(storage_path)
            video.extract_images_with_index(storage_path)

            video_paths.append(video_path)
            audio_paths.append(audio_path)
            text_paths.append(text_path)
            video_urls.append(youtube_link.strip())
    else:
        media_path, file_name, file_ext = save_uploaded_media(content)
        if file_ext not in {"mp4"}:
            print("Failed to process the uploaded media. Please make sure the media is in a supported format.")
            return
        video = Video.from_file(media_path)
        video_path, audio_path, text_path = video.process_video_with_index(storage_path)
        video.extract_images_with_index(storage_path)
        
        video_paths.append(video_path)
        audio_paths.append(audio_path)
        text_paths.append(text_path)

    media_paths = {
        "text_paths": text_paths
    }
    if audio_paths != video_paths:
        media_paths["video_paths"] = video_paths
        media_paths["video_urls"] = video_urls
    if text_paths != audio_paths:
        media_paths["audio_paths"] = audio_paths
    provide_post_process_info(media_label, media_paths)
    update_knowledge_base(media_label, media_paths)

if __name__ == "__main__":
    print("Processing content...")
    parser = argparse.ArgumentParser()
    parser.add_argument("--is_youtube_link", type=bool, default=True)
    parser.add_argument("--media_label", type=str, required=True)
    parser.add_argument("--content", type=str, required=True)
    args = parser.parse_args()
    process_content(is_youtube_link=args.is_youtube_link, media_label=args.media_label, content=args.content)
    