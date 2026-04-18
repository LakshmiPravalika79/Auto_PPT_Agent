"""
executor.py  —  ReAct agent (TPM-optimised)

Changes from previous version:
  - REACT_PROMPT slimmed from ~900 tokens to ~400 tokens base.
    With 7 tool descriptions (~300 tokens) the total base prompt is ~700 tokens.
    At max_tokens=300 that's ~1000 tokens per call — fits 6 calls/minute under
    Groq's 6,000 TPM free limit.
  - _extract() strips MCP object noise from observations (same as before).
  - create_presentation guard (same as before).
"""

import asyncio
import sys
import re
import json

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain.prompts import PromptTemplate

from agent.llm import HF_LLM

import re

def extract_topic(user_input: str) -> str:
    text = user_input.lower()

    # remove common prompt prefixes
    patterns = [
        r"create (a )?\d*\s*-?\s*slide(s)? presentation (on|about)",
        r"make (a )?\d*\s*-?\s*slide(s)? presentation (on|about)",
        r"generate (a )?\d*\s*-?\s*slide(s)? presentation (on|about)",
        r"presentation (on|about)",
    ]

    for p in patterns:
        text = re.sub(p, "", text)

    # remove extra words
    text = re.sub(r"for .*", "", text)   # remove audience part
    text = re.sub(r"[^a-zA-Z0-9 ]", "", text)

    words = [w for w in text.strip().split() if w]

    return "_".join(words[:4]) or "presentation"

def _extract(mcp_result) -> str:
    """Return just the plain text from an MCP tool result, nothing else."""
    try:
        if hasattr(mcp_result, "content") and mcp_result.content:
            text = mcp_result.content[0].text
            return text if text not in (None, "", "None") else "done"
    except Exception:
        pass
    return "done"


# Keep this prompt SHORT — every token here is paid on every single LLM call.
REACT_PROMPT = PromptTemplate.from_template("""
You are a Presentation Agent that builds PowerPoint slides for ANY topic.

User request: {input}

OBJECTIVE:
- Create a clear, structured presentation based on the user's topic.
- If the user specifies number of slides, follow it.
- Otherwise, default to 5 slides.

WORKFLOW RULES:
1. Call create_presentation ONCE at the start.
2. For EACH slide, follow EXACT order:
   add_slide → write_text → search_image → add_image
3. After completing all slides → call save_presentation and STOP.

STRICT RULES:
- NEVER call create_presentation more than once.
- NEVER restart or redo the presentation.
- NEVER skip add_image.
- Perform ONLY ONE action at a time.
- Wait for observation before next step.
- Do NOT output explanations — only tool actions.
- NEVER call write_text more than once per slide.
- Do NOT modify completed slides.

CONTENT RULES:
- Generate slide titles and bullet points based on the topic.
- Each slide must have:
  - A clear title
  - 3–5 bullet points
- Content should be appropriate for the audience (if specified).

HALLUCINATION HANDLING:
- Use search_web ONLY if:
  - The topic is unknown, complex, or unclear
  - You are unsure about factual accuracy
- Otherwise:
  - Generate content using your own knowledge

IMAGE RULES:
- Use simple search queries based on slide topic.
- Always use the FIRST image URL returned.
- If no valid image is found → skip image gracefully.
- If image fails twice → use fallback:
  https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/NGC_4414_%28NASA-med%29.jpg/800px-NGC_4414_%28NASA-med%29.jpg

SLIDE PLANNING:
- First, mentally plan all slide topics based on the user request.
- Then execute slides ONE BY ONE in order.
- Do NOT revisit or change previous slides.

Typical structure (adapt dynamically):
- Slide 1: Introduction / Overview
- Slide 2–(n-1): Key concepts / stages / components
- Final Slide: Summary / Conclusion

TOOLS:
{tools}

Tool names: {tool_names}

FORMAT (STRICT — MUST FOLLOW):

You must output EXACTLY ONE action per response.

Correct format:

Thought: <short reasoning>
Action: <tool_name>
Action Input: <input>

STOP after this.

DO NOT:
- Output multiple actions
- Add extra text after Action Input
- Continue thinking after action

FINAL RULE:
- You MUST call save_presentation at the end.
- The task is NOT complete until the presentation is saved.

{agent_scratchpad}
""")


async def generate_outline(user_input: str) -> list:
    print("[DEBUG] Generating Outline...")
    llm = HF_LLM()
    prompt = PromptTemplate.from_template("""You are an expert Presentation Generator and structural planner.
Topic: {input}

CRITICAL RULES FOR CONTENT:
1. "bullets" MUST contain highly informative, detailed explanatory sentences (15-25 words each). Do NOT just output short highlight words. Provide real, valuable knowledge, data, and context.
2. "image_search_query" MUST be a highly descriptive, visual string meant for a stock-photo search engine. Describe exactly what the photo should intuitively contain (e.g., "glowing futuristic processor chip abstract" or "corporate business people handshaking architecture"). Do NOT just use the slide title as the query!

Return ONLY a valid JSON object. NO markdown blocks, NO explanations.
The JSON object must contain EXACTLY ONE key named "slides" which is an array of 5 slide objects.
Format:
{{
  "slides": [
    {{
      "title": "Clear Engaging Slide Title", 
      "bullets": ["Detailed, professional sentence explaining a key concept comprehensively.", "Another comprehensive elaboration packed with actual knowledge and insight.", "A final concluding data-point or analytical observation relevant to the topic."], 
      "image_search_query": "highly descriptive visual scene stock photo"
    }}
  ]
}}""").format(input=user_input)
    response = await llm._acall(prompt)
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            raw_json = match.group(0)
            return json.loads(raw_json).get("slides", [])
        return json.loads(response).get("slides", [])
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON outline: {e}")
        return [
            {"title": "Overview", "bullets": ["Point 1", "Point 2"], "image_search_query": "universe presentation background"}
        ]

async def run_agent(user_input: str, theme: str = "dark", provided_slides: list = None):

    topic_filename = extract_topic(user_input)

    print("\n[DEBUG] ===== AGENT START =====")
    print("[DEBUG] Step 1: Preparing MCP parameters...")

    ppt_params = StdioServerParameters(
        command=sys.executable, args=["mcp/servers/ppt_server.py"]
    )
    search_params = StdioServerParameters(
        command=sys.executable, args=["mcp/servers/web_search_server.py"]
    )

    try:
        async with stdio_client(ppt_params) as (ppt_r, ppt_w), \
                   stdio_client(search_params) as (search_r, search_w):

            async with ClientSession(ppt_r, ppt_w) as ppt, \
                       ClientSession(search_r, search_w) as search:

                await ppt.initialize()
                await search.initialize()

                def extract_url(text: str) -> str:
                    match = re.search(r'https?://[^\s]+', text)
                    return match.group(0) if match else ""

                async def create_presentation(theme: str) -> str:
                    return _extract(await ppt.call_tool("create_presentation", {"theme": theme}))

                async def add_slide(_: str) -> str:
                    return _extract(await ppt.call_tool("add_slide", {}))

                async def write_text(title: str, bullets: list, layout: str) -> str:
                    args = {"title": title, "bullets": bullets, "layout": layout}
                    return _extract(await ppt.call_tool("write_text", args))

                async def search_image(x: str) -> str:
                    raw = _extract(await search.call_tool("search_image", {"query": x}))
                    url = extract_url(raw)
                    return url if url else ""

                async def add_image(url: str, layout: str) -> str:
                    if not url:
                        return "error"
                    return _extract(await ppt.call_tool("add_image", {"url": url, "layout": layout}))

                async def save_presentation(_: str) -> str:
                    return _extract(await ppt.call_tool("save_presentation", {"filename": topic_filename}))

                if provided_slides:
                    slides = provided_slides
                else:
                    slides = await generate_outline(user_input)

                print("[DEBUG] Step 9: Assembling presentation procedurally...")
                
                import random
                await create_presentation(theme)
                
                for i, slide in enumerate(slides):
                    print(f"[PROCEDURAL] Building Slide: {slide.get('title')}")
                    await add_slide("")
                    
                    layouts = ["image_right", "image_left"]
                    if i == 0: layouts = ["center"]  # Always center title
                    layout_choice = random.choice(layouts)
                    
                    await write_text(slide.get("title", ""), slide.get("bullets", []), layout_choice)
                    
                    if layout_choice != "center":
                        img_url = await search_image(slide.get("image_search_query", user_input))
                        if img_url and "error" not in img_url:
                            await add_image(img_url, layout_choice)

                result = await save_presentation("")
                print("[DEBUG] Presentation completed procedurally.")
                return result

    except Exception as e:
        print("\n[ERROR] Something failed:", e)
        raise