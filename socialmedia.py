#step1
import asyncio
import os
import re
import sys
import requests
from youtube_transcript_api import YouTubeTranscriptApi

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from agents import (
    Agent,
    Runner,
    function_tool,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
)

from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List


#step 2 gemini api key and configure
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # optional: enables the web_search tool

# Steps 3

gemini_async_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL,
)

set_default_openai_client(gemini_async_client)
set_default_openai_api("chat_completions")
set_tracing_disabled(True)  # we're not using OpenAI's platform, so skip trace uploads

# Synchronous client for tools

gemini_client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL,
)

# defining tools for the agent
# Tool: Generate social media content from transcript

@function_tool
def generate_content(video_transcript: str, social_media_platform: str):
    print(f"Generating social media content for {social_media_platform}...")

    response = gemini_client.chat.completions.create(
        model="gemini-3-flash-preview",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here is a new video transcript: {video_transcript}\n\n"
                    f"Generate a social media post on ..."
                ),
            }
        ],
        max_tokens=2500
    )

    return response.choices[0].message.content


# Tool: Search the web for up-to-date information (requires TAVILY_API_KEY)
@function_tool
def web_search(query: str) -> str:
    print(f"Searching the web for: {query}")

    response = requests.post(
        "https://api.tavily.com/search",
        json={"api_key": TAVILY_API_KEY, "query": query, "max_results": 5},
        timeout=15,
    )
    response.raise_for_status()
    results = response.json().get("results", [])

    if not results:
        return "No results found."

    return "\n\n".join(
        f"{r['title']}\n{r['url']}\n{r['content']}" for r in results
    )


# step 5 - defining the agent

@dataclass
class Post:
    platform: str
    content: str


content_writer_agent = Agent(
    name="Content Writer Agent",
    instructions="""You are a talented content writer who writes engaging
    highly readable social media posts.

    You will be given a video transcript and social media
    You will generate a social media post based on the video
    and the social media platforms.

    You may search the web for up-to-date information or
    fill in some useful details if needed.
    """,
    model="gemini-3-flash-preview",
    tools=(
        [generate_content, web_search] if TAVILY_API_KEY else [generate_content]
    ),
    output_type=List[Post],
)

# step6 define helper functions

# Fetch transcript from a youtube video using the video id
def get_transcript(video_id: str, languages: list = None) -> str:
    """
    Retrieves the transcript for a YouTube video.

    Args:
        video_id (str): The YouTube video id.
        languages (list, optional): List of language codes to try, in order.
            Defaults to ["en"] if None.

    Returns:
        str: The concatenated transcript text.

    Raises:
        Exception: If transcript retrieval fails, with details about the
        ...
    """

    if languages is None:
        languages = ["en"]

    try:
        # Use the YouTube transcript API
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id, languages=languages)

        # More efficient way to concatenate all text snippets
        transcript_text = " ".join(
        snippet.text for snippet in fetched_transcript
    )

        return transcript_text

    except Exception as e:
        # Handle specific YouTube transcript API exceptions
        from youtube_transcript_api.errors import (
            CouldNotRetrieveTranscript,
            VideoUnavailable,
            InvalidVideoId,
            NoTranscriptFound,
            TranscriptsDisabled,
        )

        if isinstance(e, NoTranscriptFound):
            error_msg = f"No transcript found for video {video_id} in language(s)."
        elif isinstance(e, VideoUnavailable):
            error_msg = f"Video {video_id} is unavailable"
        elif isinstance(e, InvalidVideoId):
            error_msg = f"Invalid video ID: {video_id}"
        elif isinstance(e, TranscriptsDisabled):
            error_msg = f"Transcripts are disabled for video {video_id}"
        elif isinstance(e, CouldNotRetrieveTranscript):
            error_msg = f"Could not retrieve transcript: {str(e)}"
        else:
            error_msg = f"An unexpected error occurred: {str(e)}"

        print(f"Error: {error_msg}")
        raise Exception(error_msg) from e


_YOUTUBE_ID_RE = re.compile(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})")


def extract_video_id(video_id_or_url: str) -> str:
    """Accepts a raw YouTube video ID or a full YouTube URL and returns the video ID."""
    video_id_or_url = video_id_or_url.strip()

    match = _YOUTUBE_ID_RE.search(video_id_or_url)
    if match:
        return match.group(1)

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id_or_url):
        return video_id_or_url

    raise ValueError(f"Could not extract a YouTube video ID from: {video_id_or_url}")


# step 7 - run the agent end-to-end
async def generate_posts(video_id_or_url: str, platforms: List[str]) -> List[Post]:
    video_id = extract_video_id(video_id_or_url)
    transcript = get_transcript(video_id)

    result = await Runner.run(
        content_writer_agent,
        input=(
            f"Video transcript:\n{transcript}\n\n"
            f"Generate posts for these platforms: {', '.join(platforms)}"
        ),
    )

    return result.final_output


async def main():
    video_id_or_url = input("YouTube video ID or URL: ").strip()
    platforms_raw = input("Platforms (comma-separated, e.g. Twitter/X, LinkedIn): ").strip()
    platforms = [p.strip() for p in platforms_raw.split(",") if p.strip()]

    posts = await generate_posts(video_id_or_url, platforms)

    for post in posts:
        print(f"--- {post.platform} ---")
        print(post.content)
        print()


if __name__ == "__main__":
    asyncio.run(main())