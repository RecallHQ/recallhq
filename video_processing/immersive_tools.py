
import chainlit as cl
import random 
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rags.text_rag import search_knowledge_base, create_new_index, get_llm_response, get_mm_llm_response, get_media_indices, get_llm_tts_response
from video_processing.immersive_server import manager

def update_video_message():
    apex_message = cl.user_session.get("apex_message")
    if cl.user_session.get("event_video"):
      video = cl.user_session.get("event_video")
    else:
        video = cl.Video(name="output_video.mp4", path="./recall_immersive_video/output_video.mp4", display="inline")
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
    json_message = recallws_fast_forward_msg(delta_time)
    if web_socket:
        await manager.send_message(json.dumps(json_message), web_socket)
    else:
        print(f"Error: websocket doesnt exist. Could not fast forward to: {delta_time}")
        await manager.broadcast(json.dumps(json_message))

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

### Lookup Events in Knowledge Base Tool:
lookup_events_in_kb_def =  {
    "name": "lookup_events_in_kb",
    "description": "Lookup events in the knowledge base. This tool is used when the knowledge base needs to be looked up for existing events.",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
}

async def lookup_events_in_kb_handler():
    events = []
    response_str = "Here are the list of events currently in the knowledge base. Would you like to know more about a particular event?"
    system_prompt = f"The user is being shown a list of events. Read out the following response to the user:\n {response_str}"

    for media_label, event_data in cl.user_session.get("knowledge_base").items():
        if event_data.get("title_image"):
            image_path = os.path.join(os.getcwd(), event_data.get("title_image"))
        else:
            image_path = f"https://via.placeholder.com/150?text={media_label.replace(' ', '+')}"
        image = cl.Image(
          path=image_path, name=media_label, display="inline")

        await cl.Message(
          content=media_label, elements=[image]
        ).send()
        events.append(media_label)
    return system_prompt
    
    
    
lookup_events_in_kb = (lookup_events_in_kb_def, lookup_events_in_kb_handler)


# Select event tool
select_event_def =  {
    "name": "select_event",
    "description": "Select an event from the knowledge base to find more information about the event. This tool is used when the user selects an event from the knowledge.",
    "parameters": {
      "type": "object",
      "properties": {
        "media_label": {
          "type": "string",
          "description": "The name of the event."
        },
      },
      "required": ["media_label",]
    }
}

async def select_event_handler(media_label: str):

    event_data = cl.user_session.get("knowledge_base")[media_label]
    response_str = f"How can I help you answer your questions about {media_label}?"
    system_prompt = f"The user is being shown a select event. Read out the following response to the user:\n {response_str}"

    cl.user_session.set("media_label", media_label)
    print(f"Setting media label: {media_label} for further queries")

    if event_data.get("title_image"):
        image_path = os.path.join(os.getcwd(), event_data.get("title_image"))
    else:
        image_path = f"https://via.placeholder.com/150?text={media_label.replace(' ', '+')}"
    image = cl.Image(
        path=image_path, name=media_label, display="inline")

    await cl.Message(
        content=media_label, elements=[image]
    ).send()

    return system_prompt

select_event = (select_event_def, select_event_handler)

### Query event tool:
query_event_def =  {
    "name": "query_event",
    "description": "User's query as a sentence. This tool is used when information from an event is needed to answer the user's questions.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The actual user's query."
        },
        "event_name": {
          "type": "string",
          "description": "The event name user's query applies to."
        },
      },
      "required": ["query",]
    }
}

async def query_event_handler(query: str, event_name: str):
    media_label = cl.user_session.get("media_label")
    indexes = cl.user_session.get("indexes") 

    print(f"Processing query: {query} for media_label: {media_label} or event_name: {event_name}")
    if not media_label:
        media_label = event_name
    
    img_docs, text_docs = search_knowledge_base(query, media_label, indexes)
    
    tp_executor = ThreadPoolExecutor(max_workers=1)
    future = tp_executor.submit(get_media_indices, query, text_docs, img_docs, media_label, indexes)
    response_container = cl.Message("")
    response_text, function_data  = await get_mm_llm_response(query, text_docs, img_docs, media_label, cl.user_session.get("indexes"), response_container, is_chainlit=True)
    img_results, text_results = future.result()
    tp_executor.shutdown()

    system_prompt_text = f"Here is the response to the query to be conveyed to the user: {response_text}. Read out the response to the user"
    
    if text_results:
        new_video_path = './temp/video_clips'
        for doc in text_results[:1]:
            text_path = doc['file_path']
            video_path = os.path.join(os.getcwd(), 'temp', 'video_data', Path(text_path).parent.name+'.mp4')
            start_time = doc['timestamps'][0][0]
            end_time = doc['timestamps'][-1][-1]

            #video_data = [{'video_file': video_path, 'timestamps': [start_time, end_time]}]
            #clips, clip_paths = generate_videoclips(new_video_path, video_data)
            #st.video(clip_paths[0])
            if os.path.exists(video_path):
                print(f"Adding video: {video_path} from {start_time} to {end_time}")
                video = cl.Video(name=media_label, url=f"/recall_immersive_video/{video_path}", display="inline")
                await cl.Message(
                    content=media_label, elements=[video]
                ).send()
        system_prompt_video = f"Here is the response to the query to be conveyed to the user: {response_text}. After the response has been read out, use the tool calling to play the video for interval {start_time} to {end_time}."
        return system_prompt_video
    elif img_results:
        img_count = 0
        for doc in img_results:
            relative_img_path = doc.metadata["file_path"].split('events_kb/', 1)[1]
            new_img_path = os.path.join('events_kb', relative_img_path)
            if os.path.exists(new_img_path):
                image = cl.Image(
                    path=new_img_path, name=media_label, display="inline")
                await cl.Message(
                    content=media_label, elements=[image]
                ).send()
                img_count += 1
        system_prompt_image = system_prompt_text + f"The user is also being shown {img_count} image(s). Mention that there are some images to view once the response has been read out."
        return system_prompt_image

    return system_prompt_text

query_event = (query_event_def, query_event_handler)


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

tools = [play_video_for_interval, pause_video, play_video,
         set_fullscreen_video, unset_fullscreen_video, fast_forward_video,
         lookup_events_in_kb, select_event, query_event]

#tools = [play_video_for_interval, query_video, pause_video, play_video]


