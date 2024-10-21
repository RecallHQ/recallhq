import os
import asyncio
from openai import AsyncOpenAI

import chainlit as cl
from uuid import uuid4
from chainlit.logger import logger
from video_processing.immersive_tools import update_video_message
from video_processing.immersive_server import manager
from recall_utils import load_state
from rags.text_rag import create_new_index
from constants import KNOWLEDGE_BASE_PATH, immersive_demo_labels
import sys


# REQUIRES: pip install chainlit==2.0.dev0
# Uses "output_video.mp4" as the video file.

from video_processing.realtime import RealtimeClient
from video_processing.immersive_tools import tools

from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI()    

async def setup_openai_realtime():
    """Instantiate and configure the OpenAI Realtime Client"""
    openai_realtime = RealtimeClient(api_key=os.getenv("OPENAI_API_KEY_REALTIME"))
    cl.user_session.set("track_id", str(uuid4()))
    async def handle_conversation_updated(event):
        item = event.get("item")
        delta = event.get("delta")
        """Currently used to stream audio back to the client."""
        if delta:
            # Only one of the following will be populated for any given event
            if 'audio' in delta:
                audio = delta['audio']  # Int16Array, audio added
                await cl.context.emitter.send_audio_chunk(cl.OutputAudioChunk(mimeType="pcm16", data=audio, track=cl.user_session.get("track_id")))
            if 'transcript' in delta:
                transcript = delta['transcript']  # string, transcript added
                print("Debug>>transcript =", transcript)
                pass
            if 'arguments' in delta:
                arguments = delta['arguments']  # string, function arguments added
                pass
            
    async def handle_item_completed(item):
        """Used to populate the chat context with transcription once an item is completed."""
        # print(item) # TODO
        pass
    
    async def handle_conversation_interrupt(event):
        """Used to cancel the client previous audio playback."""
        cl.user_session.set("track_id", str(uuid4()))
        await cl.context.emitter.send_audio_interrupt()
        
    async def handle_error(event):
        logger.error(event)
        
    
    openai_realtime.on('conversation.updated', handle_conversation_updated)
    openai_realtime.on('conversation.item.completed', handle_item_completed)
    openai_realtime.on('conversation.interrupted', handle_conversation_interrupt)
    openai_realtime.on('error', handle_error)

    cl.user_session.set("openai_realtime", openai_realtime)
    coros = [openai_realtime.add_tool(tool_def, tool_handler) for tool_def, tool_handler in tools]
    print("coros = ", coros)
    await asyncio.gather(*coros)


@cl.on_chat_start
async def start():
    await cl.Message(
        content="Lets try out the new (Realtime) speech-to-speech experience together!"
    ).send()
    # apex_message = cl.Message("")
    # video = cl.Video(name="output_video", url="/recall_immersive_video/video_processing/output_video.mp4", display="inline")
    # elements = [
    #       video,
    #   ]
    # apex_message.elements = elements
    # cl.user_session.set("apex_message", apex_message)
    # await apex_message.send()
    await setup_openai_realtime()

    if not cl.user_session.get("knowledge_base"):
        cl.user_session.set("knowledge_base", load_state(KNOWLEDGE_BASE_PATH))
    if not cl.user_session.get("indexes"):
        cl.user_session.set("indexes", {})
    if not cl.user_session.get("futures"):
        cl.user_session.set("futures", {})

    media_labels = []

    for media_label in immersive_demo_labels:
        if media_label not in cl.user_session.get("indexes"):
            # TODO: Remove the following if block after the Demo
            print(f"Index for {media_label} does not exist. Need to create or load one.")
            cl.user_session.get("indexes")[media_label] = create_new_index(media_label)
        else:
            print(f"Index for {media_label} exists in future or index")

@cl.on_message
async def on_message(message: cl.Message):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
    
        # TODO: Try image processing with message.elements
        await openai_realtime.send_user_message_content([{ "type": 'input_text', "text": message.content }])
    else:
        await cl.Message(content="Please activate voice mode before sending messages!").send()

@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("recall_websocket", manager.latest_socket)
    try:
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        await openai_realtime.connect()
        logger.info("Connected to OpenAI realtime")
        # TODO: might want to recreate items to restore context
        # openai_realtime.create_conversation_item(item)
        return True
    except Exception as e:
        await cl.ErrorMessage(content=f"Failed to connect to OpenAI realtime: {e}").send()
        return False

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")            
    if openai_realtime.is_connected():
        await openai_realtime.append_input_audio(chunk.data)
    else:
        logger.info("RealtimeClient is not connected")

@cl.on_audio_end
@cl.on_chat_end
@cl.on_stop
async def on_end():
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.disconnect()