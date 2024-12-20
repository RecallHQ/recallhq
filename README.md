# Recall -- An Agentic system for Interactive Videos

## VideoIndex package

The core video indexing, knoweldge base creation and video snippet generation logic resides in a separate
git repo here: https://github.com/RecallHQ/video_index

## Youtube Demo links

3 minute recording: https://youtu.be/R3Hn2oKCfoo

Full demo video: https://youtu.be/kDMSJKXfXvI

## **Overview**
In order to help quickly understand both the visual content and spoken discussion during an event, or an MOOC such as the LLM Agents Berkeley course (which are hours long or multi-day), we want to build an assistant that leverages LLMs to summarize recordings, interpret visuals, and answer follow-up questions related to the event. This system would significantly reduce the time needed to review long events, and would event content more accessible and actionable.

## **Key Features and Functionality**
### **Event Summarization** 
- Summarizes key points from the event, including discussions, keynote presentations, and Q&A sessions.
- The LLM captures the essence of talks and discussions, extracting key themes, recommendations, and conclusions. It can also create topic-based summaries (e.g., by speaker, session, or panel).

### **Visual Content Interpretation (Language + Vision Model)**
- Interprets slides, charts, and any other visual media shared during the event.
- The LLM can relate visual elements (like infographics or data visualizations) to the topics being discussed, providing context and summary explanations.

### **Interactive Q&A System**
- Allows users to ask follow-up questions about specific sessions, speakers, or visual content after the event.
- Answers specific queries like, “What was the main takeaway from Speaker X’s session?” or “What were the key statistics shown in the slide about market trends?”

### **Session Categorization and Indexing**
- Automatically segments and categorizes different parts of the event based on topics, speakers, or themes. Given the longer duration of events, this feature would be critical to ensure smooth navigation of multi-day or multi-session events.
- The LLM organizes event content into searchable categories, making it easy for users to find specific parts of the event they are interested in (e.g., “AI in Healthcare” or “Keynote by John Doe”).

## **Tech Stack**
### Language
- Python >=3.10
- Packages are noted in the requirements.txt

## **How to run the app**
- Make sure you have Python >=3.10 installed
- Setup venv and activate it
    * `python3 -m venv .venv`
    * `source .venv/bin/activate`
- Run `pip install -r requirements.txt` to install the dependencies
- Run `streamlit run Home.py` to start the app
- To enable the Immersive Mode: Run `chainlit run immersive_chainlit.py -w --port 8080` to start the chainlit app before navigating to the immersive mode section in the sidebar. 
