"""
agent_core.py

Final ReAct agent with:
- Explicit planning
- Tool usage
- Logging
- Graceful fallback
"""

import json
from agent.llm import LLM
from agent.logger import logger
from agent.utils import retry


class PPTAgent:

    def __init__(self):
        self.llm = LLM()

    def call_llm(self, prompt):
        """LLM call with retry"""
        return retry(lambda: self.llm.generate(prompt))

    def execute_tool(self, name, args):
        """Execute MCP tool"""
        return retry(lambda: TOOLS[name](**args))

    def generate_plan(self, user_input):
        prompt = f"""
        Create a presentation outline for:
        {user_input}

        Return JSON list
        """

        response = self.call_llm(prompt)

        if not response:
           return [
            "Introduction",
            "Main Concept",
            "Stages",
            "Examples",
            "Conclusion"
           ]

        try:
            import json
            return json.loads(response)
        except:
            return [
            "Introduction",
            "Main Concept",
            "Stages",
            "Examples",
            "Conclusion"
           ]
        
    def generate_plan(self, user_input):
        prompt = f"""
        Create a presentation outline for:
        {user_input}

        Return JSON list
        """

        response = self.call_llm(prompt)

        if not response:
            return [
            "Introduction",
            "Main Concept",
            "Stages",
            "Examples",
            "Conclusion"
           ]

        try:
            import json
            return json.loads(response)
        except:
            return [
            "Introduction",
            "Main Concept",
            "Stages",
            "Examples",
            "Conclusion"
            ]

    def run(self, user_input):
        """
        Full execution pipeline
        """

        logger.info("Starting agent...")

        #  STEP 1: PLAN (explicit)
        logger.info("Planning slides...")
        slides = self.generate_plan(user_input)

        # Tool call (for MCP compliance)
        self.execute_tool("plan_slides", {"user_input": user_input})

        #  STEP 2: CREATE PPT
        self.execute_tool("create_presentation", {})

        #  STEP 3: LOOP THROUGH SLIDES
        for title in slides:
            logger.info(f"Processing: {title}")

            self.execute_tool("add_slide", {})

            bullets = self.generate_content(title)

            self.execute_tool("write_text", {
                "title": title,
                "bullets": bullets
            })

        #  STEP 4: SAVE
        self.execute_tool("save_presentation", {})

        logger.info("Presentation generated successfully!")