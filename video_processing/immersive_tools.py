
import chainlit as cl
import random 
from immersive_server import manager
import json

def update_video_message():
    apex_message = cl.user_session.get("apex_message")
    if cl.user_session.get("event_video"):
      video = cl.user_session.get("event_video")
    else:
        video = cl.Video(name="output_video.mp4", path="./recall_immersive_video", display="inline")
        cl.user_session.set("event_video", video)
    video.player_config = {"playing": True}
    elements = [
          video,
      ]
    apex_message.elements = elements

"""
Recall websocket protocol messages:
"""

def recallws_update_video_interval_msg(start_time, end_time):
    msg = {'type': 'updateVideoInterval', 'start': start_time, 'end': end_time}
    return msg

def recallws_fast_forward_msg(delta_time):
    msg = {'type': 'fastForward', 'delta': delta_time}
    return msg

def recallws_set_video_fullscreen_msg():
    return {'type': 'setVideoFullscreen'}

def recallws_unset_video_fullscreen_msg():
    return {'type': 'unsetVideoFullscreen'}

def recallws_play_video_msg():
    return {'type': 'playVideo'}

def recallws_pause_video_msg():
    return {'type': 'pauseVideo'}

async def recallws_update_onscreen_video(start_time, end_time):
    web_socket = cl.user_session.get("recall_websocket", None)
    if web_socket:
        json_message = recallws_update_video_interval_msg(start_time, end_time)
        await manager.send_message(json.dumps(json_message), web_socket)

async def recallws_fast_forward_onscreen_video(delta_time):
    web_socket = cl.user_session.get("recall_websocket", None)
    if web_socket:
        json_message = recallws_fast_forward_msg(delta_time)
        await manager.send_message(json.dumps(json_message), web_socket)

async def recallws_play_video():
    web_socket = cl.user_session.get("recall_websocket", None)
    if web_socket:
        json_message = recallws_play_video_msg()
        await manager.send_message(json.dumps(json_message), web_socket)

async def recallws_pause_video():
    web_socket = cl.user_session.get("recall_websocket", None)
    if web_socket:
        json_message = recallws_pause_video_msg()
        await manager.send_message(json.dumps(json_message), web_socket)

async def recallws_set_fullscreen():
    web_socket = cl.user_session.get("recall_websocket", None)
    if web_socket:
        json_message = recallws_set_video_fullscreen_msg()
        await manager.send_message(json.dumps(json_message), web_socket)

async def recallws_unset_fullscreen():
    web_socket = cl.user_session.get("recall_websocket", None)
    if web_socket:
        json_message = recallws_unset_video_fullscreen_msg()
        await manager.send_message(json.dumps(json_message), web_socket)


######        

async def update_apex_message():
    apex_message = cl.user_session.get("apex_message")
    await apex_message.update()

"""
Recall tools to be called using the OpenAI realtime api:
"""

### Query video tool:
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

### Play video tool:
play_video_for_interval_def =  {
    "name": "play_video_for_interval",
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

async def play_video_for_interval_handler(start: float, end: float):
    msg = f"playing from start = {start} until end = {end}"
    print(msg)
    #update_video_message()
    await recallws_update_onscreen_video(start, end)
    #await update_apex_message()

    return msg

play_video_for_interval = (play_video_for_interval_def, play_video_for_interval_handler)

### Pause video tool:
pause_video_def =  {
    "name": "pause_video",
    "description": "Pause the currently playing video.",
    "parameters": {}
}

async def pause_video_handler():
    await recallws_pause_video()

pause_video = (pause_video_def, pause_video_handler)

### Play video tool:
play_video_def =  {
    "name": "play_video",
    "description": "Play the current video.",
    "parameters": {}
}

async def play_video_handler():
    await recallws_play_video()

play_video = (play_video_def, play_video_handler)

### Set full screen video tool:
set_fullscreen_video_def =  {
    "name": "set_fullscreen_for_video",
    "description": "Set the current video to full screen mode.",
    "parameters": {}
}

async def set_fullscreen_video_handler():
    await recallws_set_fullscreen()

set_fullscreen_video = (set_fullscreen_video_def, set_fullscreen_video_handler)

### Unset full screen video tool:
unset_fullscreen_video_def =  {
    "name": "unset_fullscreen_for_video",
    "description": "Set the current video to regular mode, or in other words, exit the fullscreen mode.",
    "parameters": {}
}

async def unset_fullscreen_video_handler():
    await recallws_unset_fullscreen()

unset_fullscreen_video = (unset_fullscreen_video_def, unset_fullscreen_video_handler)

### Fast forward full screen video tool:
fast_forward_video_def =  {
    "name": "fast_forward_video",
    "description": "Skip ahead or fast forward the current video by the user provided time interval in seconds.",
    "parameters": {
      "type": "object",
      "properties": {
        "time_delta": {
          "type": "number",
          "description": "The interval offset or time delta by with to fast forward or advance the video."
        },
      },
      "required": ["time_delta"]
    }
}

async def fast_forward_video_handler(time_delta):
    await recallws_fast_forward_onscreen_video(time_delta)

fast_forward_video = (fast_forward_video_def, fast_forward_video_handler)

tools = [play_video_for_interval, query_video, pause_video,
          play_video, set_fullscreen_video, unset_fullscreen_video, fast_forward_video]

#tools = [play_video_for_interval, query_video, pause_video, play_video]


