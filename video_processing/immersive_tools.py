
import chainlit as cl
import random

def update_video_message():
    apex_message = cl.user_session.get("apex_message")
    if cl.user_session.get("event_video"):
      video = cl.user_session.get("event_video")
    else:
        video = cl.Video(name="output_video.mp4", path="./output_video.mp4", display="inline")
        cl.user_session.set("event_video", video)
    video.player_config = {"playing": True}
    elements = [
          video,
      ]
    apex_message.elements = elements


async def update_apex_message():
    apex_message = cl.user_session.get("apex_message")
    await apex_message.update()


query_video_def =  {
    "name": "query_video",
    "description": "User's query as a sentence. This tool is used when information from the video is needed to answer the user's questions.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The actual user's query."
        },
      },
      "required": ["query",]
    }
}

async def query_video_handler(query: str):
    random_start = random.uniform(0.0, 10.0)
    random_delta = random.uniform(0.0, 20.0)
    random_end = random_start + random_delta

    await cl.Message("Querying video.").send()
    return f"The query result is in the video snippet. Use tool calling to play video from {random_start} to {random_end}."

query_video = (query_video_def, query_video_handler)

play_video_def =  {
    "name": "play_video",
    "description": "Play the video from a start time interval until an end time interval.",
    "parameters": {
      "type": "object",
      "properties": {
        "start": {
          "type": "number",
          "description": "The start time in seconds. Use floating number system to indicate fractional values."
        },
        "end": {
          "type": "number",
          "description": "The end time in seconds. Use floating number system to indicate fractional values."
        },
      },
      "required": ["start","end"]
    }
}

async def play_video_handler(start: float, end: float):
    msg = f"playing from start = {start} until end = {end}"
    print(msg)
    update_video_message()
    await update_apex_message()

    return msg

play_video = (play_video_def, play_video_handler)

tools = [play_video, query_video]


