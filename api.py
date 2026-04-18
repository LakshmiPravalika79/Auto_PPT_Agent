import os
import sys
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "agent", ".env"))
from agent.core.executor import run_agent, extract_topic, generate_outline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PPTRequest(BaseModel):
    topic: str
    theme: str = "dark"
    slides: list = None

@app.post("/plan")
async def plan_ppt(req: PPTRequest):
    try:
        slides_outline = await generate_outline(req.topic)
        return {"slides": slides_outline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_ppt(req: PPTRequest):
    topic_filename = extract_topic(req.topic)
    safe_filename = "".join(c if c.isalnum() or c in " _-" else "" for c in topic_filename)
    safe_filename = safe_filename.strip().replace(" ", "_") or "output"
    file_path = f"{safe_filename}.pptx"
    
    try:
        await run_agent(req.topic, req.theme, req.slides)
        
        if os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=file_path,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        else:
            raise HTTPException(status_code=500, detail="Presentation generation failed: file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
