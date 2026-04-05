import sys
import io
import requests
import tempfile
import os
from mcp.server.fastmcp import FastMCP

from pptx import Presentation
from pptx.util import Inches, Emu
from pptx.util import Inches, Pt

mcp = FastMCP("ppt-server")

presentation = None
slide = None


@mcp.tool()
def create_presentation() -> str:
    """Create a new PowerPoint presentation."""
    global presentation
    print("[PPT] create", file=sys.stderr)
    presentation = Presentation()
    return "created"


@mcp.tool()
def add_slide() -> str:
    """Add a new slide to the current presentation."""
    global presentation, slide
    print("[PPT] slide", file=sys.stderr)
    layout = presentation.slide_layouts[6]  # blank layout
    slide = presentation.slides.add_slide(layout)
    return "added"



@mcp.tool()
def write_text(title: str, bullets: list[str]) -> str:
    global slide
    print("[PPT] write", file=sys.stderr)

    # Title (top)
    title_box = slide.shapes.add_textbox(
        left=Inches(1),
        top=Inches(0.5),
        width=Inches(8),
        height=Inches(1)
    )
    title_tf = title_box.text_frame
    title_tf.text = title
    title_tf.paragraphs[0].font.size = Pt(36)

    # Bullet text (left side)
    textbox = slide.shapes.add_textbox(
        left=Inches(1),
        top=Inches(1.8),
        width=Inches(4.5),
        height=Inches(4)
    )

    tf = textbox.text_frame
    tf.clear()

    for b in bullets:
        p = tf.add_paragraph()
        p.text = b
        p.level = 0
        p.font.size = Pt(18)

    return "written"


@mcp.tool()
def add_image(url: str) -> str:
    """Download an image from a URL and add it to the current slide."""
    global slide
    print(f"[PPT] add_image: {url}", file=sys.stderr)

    try:
        # Download the image
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Save to a temp file so python-pptx can read it
        suffix = ".jpg"
        content_type = response.headers.get("Content-Type", "")
        if "png" in content_type:
            suffix = ".png"
        elif "gif" in content_type:
            suffix = ".gif"
        elif "webp" in content_type:
            suffix = ".webp"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        # Get slide dimensions
        slide_width = presentation.slide_width
        slide_height = presentation.slide_height

        # Place image in the right half of the slide, vertically centered
        img_width = Inches(4)
        img_height = Inches(3)
        left = Inches(5.5)   # fixed right-side placement
        top = Inches(2)

        slide.shapes.add_picture(tmp_path, left, top, img_width, img_height)
        os.unlink(tmp_path)

        print("[PPT] image added successfully", file=sys.stderr)
        return "image added"

    except Exception as e:
        print(f"[PPT] add_image failed: {e}", file=sys.stderr)
        return f"image failed: {e}"


@mcp.tool()
def save_presentation(filename: str = "output") -> str:
    """Save the presentation. Pass a short filename (no extension) based on the topic."""
    global presentation
    safe = "".join(c if c.isalnum() or c in " _-" else "" for c in filename)
    safe = safe.strip().replace(" ", "_") or "output"
    path = f"{safe}.pptx"
    print(f"[PPT] save -> {path}", file=sys.stderr)
    presentation.save(path)
    return f"saved as {path}"


if __name__ == "__main__":
    print("[PPT SERVER] running...", file=sys.stderr)
    mcp.run()