# Process a video by extracting knowledge from it into a rag.
# Currently just converts into a text file.

from pytubefix import YouTube
from pytubefix.cli import on_progress
from pathlib import Path
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import random
import string
import os
import re
import argparse

# SET CONFIG
_example_video_url = "https://www.youtube.com/watch?v=d_qvLDhkg00"
_example_output_folder = "./temp/video_data/"

def replace_non_alphanumeric(input_string, rep_string):
    # Replace all non-alphabetic and non-numeric characters with a space
    return re.sub(r'[^a-zA-Z0-9]', rep_string, input_string)

def generate_random_string(length):
    # Generate a random string of specified length using letters and digits
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def generate_filename(title, random_str, ext="mp4"):
    title_0 = replace_non_alphanumeric(title, "_")
    title_1=  '_'.join(title_0.strip().split())
    return f"{title_1}_{random_str}.{ext}"

def generate_subtitlesfilename(title, random_str):
    title_0 = replace_non_alphanumeric(title, "_")
    title_1=  '_'.join(title_0.strip().split())
    return f"{title_1}_{random_str}_subtitles.srt"

def get_audio_outfile(video_outfile, ext="mp4"):
    return video_outfile.replace(ext, "wav")

def get_text_outfile(video_outfile, ext="mp4"):
    return video_outfile.replace(ext, "txt")  

def make_tempdirs(folder_path):
    Path(folder_path).mkdir(parents=True, exist_ok=True)


def download_video(url, output_path):
    """
    Download a video from a given url and save it to the output path.

    Parameters:
    url (str): The url of the video to download.
    output_path (str): The path to save the video to.

    Returns:
    dict: A dictionary containing the metadata of the video.
    """

    yt = YouTube(url, on_progress_callback=on_progress)
    metadata = {"Author": yt.author, "Title": yt.title, "Views": yt.views}
    rnd_str = generate_random_string(10)
    outfilename = generate_filename(yt.title, rnd_str)
    print(f"Saving video as {outfilename}")
    yt.streams.get_highest_resolution().download(
        output_path=output_path, filename=outfilename
    )
    subtitles_outfile = generate_subtitlesfilename(yt.title, rnd_str)
    if subtitles_outfile is not None:
        caption = yt.captions.get_by_language_code('en')
        if caption is not None:
            caption.save_captions(subtitles_outfile)
    return (metadata, outfilename)



def extract_audio(video_path, output_audio_path):
    """
    Convert a video to audio and save it to the output path.

    Parameters:
    video_path (str): The path to the video file.
    output_audio_path (str): The path to save the audio to.

    """
    print("Extracting audio ..")
    clip = VideoFileClip(video_path)
    audio = clip.audio
    audio.write_audiofile(output_audio_path)

def extract_text(audio_path, text_outfile):
    """
    Extracts text from an audio file using whisper speech recognition (for English only)
    """
    print("Extracting text ..")
    recognizer = sr.Recognizer()
    audio = sr.AudioFile(audio_path)

    with audio as source:
        # Record the audio data
        audio_data = recognizer.record(source)

        try:
            # Recognize the speech
            text = recognizer.recognize_whisper(audio_data)
        except sr.UnknownValueError:
            print("Speech recognition could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from service; {e}")

    return text


def process_video(url, output_folder=_example_output_folder):
    """
      Downloads video from the given YouTube URL, extracts audio and text.
      Returns:
         (video filepath, audio filepath, text filepath)
    """
    make_tempdirs(output_folder)
    (_, video_outfile) = download_video(url, output_folder)
    video_path = f"{output_folder}/{video_outfile}"
    audio_path = get_audio_outfile(video_path)
    text_path = get_text_outfile(video_path)
    extract_audio(video_path, audio_path)
    text = extract_text(audio_path, text_path)
    # Save text to file
    with open(text_path, 'w') as file:
        file.write(text)
    print(f"Video transcript saved as {text_path}")
    return (video_path, audio_path, text_path)

def get_file_parts(file):
    """
    Get the file name and extension of a file.

    Returns:
        (file_name, file_extension)
    """
    file_parts = os.path.splitext(file.name)
    return file_parts[0].lower(), file_parts[1].lower()[1:]

def save_uploaded_media(uploaded_media, output_folder=_example_output_folder):
    """
    Save uploaded media file (video or audio) to the output folder.
    
    Returns:
        (media filepath)
    """
    make_tempdirs(output_folder)
    rnd_str = generate_random_string(10)
    file_name, file_ext = get_file_parts(uploaded_media)
    media_outfile = generate_filename(f'{file_name}', rnd_str, file_ext)
    print(f"Saving media as {media_outfile}")
    media_path = f"{output_folder}/{media_outfile}"
    with open(media_path, "wb") as f:
        f.write(uploaded_media.getvalue())
    return media_path, file_name, file_ext

def process_uploaded_media(uploaded_media, output_folder=_example_output_folder):
    """
    Process uploaded media file (video or audio) and extracts text.
    Returns:
        (media filepath, text filepath)
    """
    media_path, file_name, file_ext = save_uploaded_media(uploaded_media, output_folder)
    if file_ext == "mp4":
        audio_path = get_audio_outfile(media_path)
        extract_audio(media_path, audio_path)
    else:
        audio_path = media_path

    text_path = get_text_outfile(media_path, file_ext)
    text = extract_text(audio_path, text_path)
    # Save text to file
    with open(text_path, 'w') as file:
        file.write(text)
    print(f"Media transcript saved as {text_path}")
    return (media_path, audio_path, text_path)

def run_main():
    parser = argparse.ArgumentParser(description="Process a YouTube video.")

    parser.add_argument('-y', '--youtube_url', type=str, nargs='?',
                        default=_example_video_url, help=f"A YouTube url to process, default: {_example_video_url}")

    parser.add_argument('-o', '--output_folder', type=str, nargs='?', default=_example_output_folder, 
                        help=f"Output folder (default: {_example_output_folder})")

    args = parser.parse_args()

    print("YouTube url:", args.youtube_url)
    print("Output folder: ", args.output_folder)
    (v, a, t) = process_video(args.youtube_url, args.output_folder)
    print(f"Video saved as {v}, audio as {a}, text as {t}")

if __name__ == "__main__":
    run_main()