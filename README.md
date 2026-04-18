# Auto-PPT Agent: 🚀

Auto-PPT Agent is a professional-grade, automated presentation generation platform. It leverages state-of-the-art LLMs, Model Context Protocol (MCP), and generative AI imagery to transform a single text prompt into a fully-structured, visually stunning PowerPoint presentation in seconds.

## 🌟 Key Features
- **Gamma-Style Magic**: Single-click generation with professional aesthetics.
- **AI Image Generation**: Built-in integration with Pollinations.ai for context-aware, high-fidelity visuals.
- **Deep Intelligence**: Powered by `Llama-3.3-70B-Versatile` for high-density, informative content.
- **Dynamic Layout Engine**: Procedural slide assembly with varying geometric layouts (Image Left, Image Right, Center).
- **Modern UI**: Sleek React-based frontend with a premium "Slate-900" dark mode.

---

## 🏗️ Architecture Overhaul

The project follows a modular, scalable architecture split into three core layers:

### 1. Frontend (React + Vite)
- **Tech Stack**: React, Vanilla CSS3 (Custom Design System).
- **Functionality**: Minimalist "Magic Input" interface. Communicates with the FastAPI backend to trigger the generation pipeline and handle direct `.pptx` downloads.

### 2. Backend API (FastAPI)
- **Endpoints**:
  - `POST /generate`: The primary orchestration entry point.
- **Orchestrator**: The backend manages the lifecycle of the Agent and ensures clean communication between the LLM and the MCP servers.

### 3. Agent Core (LangChain + Groq)
- **Model**: `Llama-3.3-70B-Versatile` via Groq for sub-second reasoning.
- **Logic**: Uses a two-phase "Plan-then-Assemble" procedural logic. 
  - **Plan**: The LLM generates a structured JSON outline of 5-7 slides with detailed bullet points and descriptive image prompts.
  - **Assemble**: A procedural worker iterates through the plan, calling MCP tools to physically build the slides.

---

## 🔌 Model Context Protocol (MCP) Tools

We chose **FastMCP** for its high-level abstraction and ease of integration. The system runs two dedicated local MCP servers:

### A. PPT Server (`ppt_server.py`)
- **Tools**:
  - `create_presentation(theme)`: Initializes a new `.pptx` object with custom color palettes (Dark, Light, Blue).
  - `add_slide()`: Creates a new blank slide with a themed background.
  - `write_text(title, bullets, layout)`: Implements complex geometric positioning, font-scaling, and typography constraints.
  - `add_image(url, layout)`: Downloads and embeds images with automatic aspect-ratio preservation and decorative borders.
  - `save_presentation(filename)`: Finalizes and flushes the file to disk.

### B. Search Server (`web_search_server.py`)
- **Tools**:
  - `search_image(query)`: Uses a cascading strategy:
    1. **Pollinations AI**: Generates a custom AI illustration based on the LLM's descriptive prompt.
    2. **DuckDuckGo/Wikimedia**: Fallbacks for specific factual diagram requirements.
  - `search_web(query)`: Fetches real-time factual snippets if the LLM requires more context for a niche topic.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js & npm
- [Groq API Key](https://console.groq.com/) (Set as `GROQ_API_KEY` in your environment)

### Installation
1. **Clone the Repo**:
   ```bash
   git clone https://github.com/LakshmiPravalika79/Auto_PPT_Agent.git
   cd Auto_PPT_Agent
   ```
2. **Backend Setup**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   pip install -r requirements.txt
   python api.py
   ```
3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🛠️ Implementation Rationale
- **Why FastMCP?**: It allowed us to decouple the PowerPoint manipulation logic from the AI's reasoning, making the system "tool-agnostic" and extremely easy to debug.
- **Why Llama-3.3-70B?**: We transitioned from 8B to 70B to ensure that bullet points were informative explanatory sentences rather than simple keywords.
- **Generative vs Scraping**: We moved to generative AI images to eliminate "irrelevant profile pictures" commonly found in generic web searches, ensuring every slide looks like professional concept art.

---

Designed with ❤️ as part of the Calibo AI Academy training.
