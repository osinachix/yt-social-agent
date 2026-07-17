# Social Media Agent

Turns a YouTube video into ready-to-post social media content. Fetches the
video's transcript, then runs it through a Gemini-powered agent (built with
the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)) that
writes a tailored post per platform.

## Setup

1. Create/activate the virtual environment and install dependencies:

   ```
   virtual-env\Scripts\activate
   pip install -r requirements.txt
   ```

2. Add your Gemini API key to `.env`:

   ```
   GEMINI_API_KEY=your-key-here
   ```

   Get a key at https://aistudio.google.com/apikey.

3. (Optional) Enable live web search by adding a
   [Tavily](https://tavily.com) key:

   ```
   TAVILY_API_KEY=your-key-here
   ```

   Without this, the agent still works, just without web search.

## Usage

**Streamlit app** (paste a video URL, pick platforms, click generate):

```
virtual-env\Scripts\streamlit run app.py
```

**Command line**:

```
virtual-env\Scripts\python socialmedia.py
```

You'll be prompted for a YouTube video ID or URL and a comma-separated list
of platforms (e.g. `Twitter/X, LinkedIn`).

## Project structure

- `socialmedia.py` — core logic: transcript fetching, the Gemini agent, its
  tools, and the CLI entry point.
- `app.py` — Streamlit UI built on top of `socialmedia.py`.
- `requirements.txt` — pinned dependencies.
