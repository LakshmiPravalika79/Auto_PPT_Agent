"""
llm.py  —  Groq LLM wrapper (free tier, TPM-aware)

Rate limits for llama-3.3-70b-versatile (free):
  - 6,000 tokens per minute (TPM)  ← the limit we keep hitting
  - 100,000 tokens per day  (TPD)

With a ~800-token base prompt and max_tokens=300, each call costs ~1,100 tokens.
At 6,000 TPM that allows ~5 calls/minute safely.

CALL_INTERVAL_SEC = 12 guarantees we never exceed 5 calls/minute regardless
of prompt size growth as the scratchpad accumulates.

If we still hit 429, we parse Groq's "try again in Xs" and sleep that long.
"""

import os
import re
import time
import asyncio
from typing import Any, List, Optional

from groq import AsyncGroq, RateLimitError
from dotenv import load_dotenv

from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun

# Load .env relative to this file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MAX_RETRIES    = 2
DEFAULT_WAIT   = 15        # seconds if we can't parse the retry-after header
CALL_INTERVAL  = 5       # minimum seconds between successive LLM calls

_last_call_time: float = 0.0   # module-level so it persists across calls


def _parse_wait_seconds(error_message: str) -> float:
    m = re.search(r"try again in(?: (\d+)m)? (\d+(?:\.\d+)?)s", str(error_message))
    if m:
        return int(m.group(1) or 0) * 60 + float(m.group(2))
    return DEFAULT_WAIT


class HF_LLM(LLM):

    model: str = "llama-3.3-70b-versatile"

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("[DEBUG] Initializing Groq LLM (llama-3.1-8b-instant)...")
        object.__setattr__(self, "_client", AsyncGroq(
            api_key=os.getenv("GROQ_API_KEY")
        ))

    @property
    def _llm_type(self) -> str:
        return "groq"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        # Fallback to sync call (not recommended in async env like FastAPI)
        return asyncio.run(self._acall(prompt, stop, None, **kwargs))

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        global _last_call_time

        # ── Rate-limit pacing: enforce minimum gap between calls ─────────
        elapsed = time.time() - _last_call_time
        if elapsed < CALL_INTERVAL:
            wait = CALL_INTERVAL - elapsed
            print(f"[DEBUG] Pacing: sleeping {wait:.1f}s to stay under TPM limit...")
            await asyncio.sleep(wait)

        print("\n[DEBUG] LLM INVOKE STARTED")
        print(f"[DEBUG] Prompt length: {len(prompt)} chars")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"[DEBUG] Groq API call (attempt {attempt}/{MAX_RETRIES})")
                response = await self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2500,
                    temperature=0.2,
                    stop=stop or None,
                    response_format={"type": "json_object"}
                )
                _last_call_time = time.time()
                result = response.choices[0].message.content
                print("[DEBUG] LLM RESPONSE RECEIVED")
                print("[DEBUG] Response preview:", result[:200])
                return result

            except RateLimitError as e:
                wait = min(_parse_wait_seconds(str(e)), 20)  # cap at 20s
                print(f"[DEBUG] 429 — capped wait {wait:.1f}s (attempt {attempt}/{MAX_RETRIES})...")
                await asyncio.sleep(wait + 1)
                if attempt == MAX_RETRIES:
                    raise

            except Exception as e:
                print("[LLM ERROR]:", e)
                raise