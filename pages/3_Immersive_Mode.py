import streamlit as st

# URL of the Chainlit app
chainlit_url = "http://localhost:8080"

# Set Streamlit page config to have a wide layout
st.set_page_config(layout="wide")
st.markdown(
    """<style>
    #MainMenu {visibility: hidden;} /* Hides the entire menu in the top-right corner */
    header {visibility: hidden;} /* Hides the top-right Streamlit header (including the 'Deploy' button) */
       </style>""",
    unsafe_allow_html=True
)
# Hide Streamlit's default padding and margins
# Hide Streamlit's default padding and margins, and prevent scrolling
hide_streamlit_style = """
    <style>
    iframe {
        height: calc(100vh - 0px);  /* Full viewport height without any padding */
        width: 100%;   /* Full width */
        border: none;  /* No borders around the iframe */
        padding: 0 !important;
        margin: 0 !important;
        position:absolute;
        top:0;
        left:0;
        bottom:0;
        right:0; 
        overflow:hidden;
        z-index:999999
        frameborder="0"
    }
    </style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Create an iFrame to embed the Chainlit UI inside Streamlit
st.components.v1.iframe(chainlit_url)
