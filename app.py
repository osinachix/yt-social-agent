import asyncio

import streamlit as st

from socialmedia import generate_posts, GEMINI_API_KEY, TAVILY_API_KEY

st.set_page_config(page_title="Social Media Agent", page_icon="📱")
st.title("📱 Social Media Agent")
st.caption("Turn a YouTube video into ready-to-post social media content.")

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY is not set. Add it to your .env file to continue.")
    st.stop()

if not TAVILY_API_KEY:
    st.info("TAVILY_API_KEY is not set — the agent will run without live web search.")

video_input = st.text_input(
    "YouTube video ID or URL",
    placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
)

platforms = st.multiselect(
    "Platforms",
    ["Twitter/X", "LinkedIn", "Instagram", "Facebook", "TikTok"],
    default=["Twitter/X", "LinkedIn"],
)

if st.button("Generate posts", type="primary", disabled=not video_input or not platforms):
    with st.spinner("Fetching transcript and generating posts..."):
        try:
            posts = asyncio.run(generate_posts(video_input, platforms))
        except Exception as e:
            st.error(f"Failed to generate posts: {e}")
        else:
            for post in posts:
                with st.container(border=True):
                    st.subheader(post.platform)
                    st.write(post.content)
