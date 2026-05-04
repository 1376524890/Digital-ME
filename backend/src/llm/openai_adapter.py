import json
from collections.abc import AsyncIterator
from typing import TypeVar, get_origin

T = TypeVar("T")

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.llm.base import BaseLLM


class OpenAIAdapter(BaseLLM):
    def __init__(self, base_url: str, api_key: str, model: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def _build_messages(
        self, system_prompt: str, messages: list[dict]
    ) -> list[dict]:
        return [{"role": "system", "content": system_prompt}, *messages]

    def _parse_json_content(self, content: str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re

            match = re.search(r"\{.*\}|\[.*\]", content, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group())

    def _strip_thought(self, content: str) -> str:
        if not content:
            return ""
        import re
        
        # 1. First pass: Remove <think>...</think> blocks as they are standard
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        
        # 2. Define markers
        # Blocks to discard (thinking / reasoning process)
        thought_markers = [
            # English markers
            r"Analyze User Input:",
            r"Analyze the User's Input:",
            r"Analyze Persona Profile:",
            r"Analyze the Persona/Goal:",
            r"Determine Goal & Strategy:",
            r"Determine the Next Step:",
            r"Determine Response Structure:",
            r"Strategy & Goal:",
            r"Strategy Guidance:",
            r"Thinking Process:",
            r"Here's a thinking process",
            r"Mental Draft:",
            r"Thought Trace:",
            r"Thought:",
            r"Reasoning:",
            r"Guidelines:",
            r"Role:",
            r"Goal:",
            r"Constraints:",
            r"Identify Key Constraints:",
            r"Draft Construction \(Mental Refinement in Chinese\):",
            r"Draft \(Mental Refinement in Chinese\):",
            r"Draft \(mental\):",
            # Chinese markers (DeepSeek often thinks in Chinese)
            r"我的实际输出是",
            r"确定回复结构",
            r"确定回复结构：",
            r"草稿（中文思维优化）：",
            r"草稿\（中文思维优化\）：",
            r"思考过程：",
            r"推理：",
        ]

        # Possible starts for the actual response
        response_markers = [
            r"Draft Construction:",
            r"Final Response:",
            r"Response:",
            r"Suggested Response:",
            r"AI:",
            r"最终回复：",
            r"回复：",
        ]

        # 3. Collect ALL marker positions
        found_markers = []
        for m in thought_markers:
            for match in re.finditer(m, content, re.IGNORECASE):
                found_markers.append({'start': match.start(), 'end': match.end(), 'type': 'thought'})
        for m in response_markers:
            for match in re.finditer(m, content, re.IGNORECASE):
                found_markers.append({'start': match.start(), 'end': match.end(), 'type': 'response'})
        
        # Sort by start position
        found_markers.sort(key=lambda x: x['start'])

        # 4. Extract content chunks that are marked as 'response'
        # Or if no markers, the whole content
        if not found_markers:
            best_content = content
        else:
            best_content = ""
            for i, marker in enumerate(found_markers):
                if marker['type'] == 'response':
                    # Content starts after this marker
                    start_pos = marker['end']
                    # Ends at the next marker (of any type)
                    end_pos = found_markers[i+1]['start'] if i+1 < len(found_markers) else len(content)
                    chunk = content[start_pos:end_pos].strip()
                    if chunk:
                        best_content += chunk + "\n\n"
            
            # If no response marker was ever found, but thought markers WERE,
            # take the content BEFORE the first thought marker or AFTER the last one
            if not best_content:
                # Try taking the chunk BEFORE the first marker if it's substantial
                first_chunk = content[0:found_markers[0]['start']].strip()
                if len(first_chunk) > 20:
                    best_content = first_chunk
                else:
                    # Collect all blocks between/before/after thought markers
                    last_end = 0
                    blocks = []
                    for marker in found_markers:
                        if marker['start'] > last_end:
                            blocks.append(content[last_end:marker['start']])
                        last_end = marker['end']
                    if last_end < len(content):
                        blocks.append(content[last_end:])

                    if blocks:
                        blocks = [b.strip() for b in blocks if len(b.strip()) > 10]
                        if blocks:
                            # Prefer blocks with Chinese characters (actual response)
                            cn_blocks = [b for b in blocks if any('一' <= c <= '鿿' for c in b)]
                            if cn_blocks:
                                # Pick the LAST block with Chinese (response comes after thinking)
                                best_content = cn_blocks[-1]
                            else:
                                best_content = blocks[-1]

        # 5. Clean up internal labels and specific phrases
        internal_labels = [
            r"^Introduction:\s*",
            r"^Opening question:\s*",
            r"^Greeting:\s*",
            r"^Response:\s*",
            r"^AI:\s*",
            r"^简介：\s*",
            r"^开放式问题：\s*",
            r"^问候语：\s*",
            r"^回复：\s*",
        ]
        
        lines = best_content.split('\n')
        final_lines = []
        for line in lines:
            cleaned_line = line.strip()
            # Special case for the "leads to suggested response" phrase if it leaked in
            if "thinking process" in cleaned_line.lower() and "suggested response" in cleaned_line.lower():
                continue
                
            for label in internal_labels:
                cleaned_line = re.sub(label, "", cleaned_line, flags=re.IGNORECASE)
            
            if cleaned_line:
                final_lines.append(cleaned_line)
        
        best_content = "\n\n".join(final_lines)

        return best_content.strip()

    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(system_prompt, messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return self._strip_thought(content)

    async def generate_stream(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(system_prompt, messages),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        in_think_block = False
        buffer = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                continue

            content = delta.content
            if not content:
                continue

            buffer += content
            
            while buffer:
                if not in_think_block:
                    if "<think>" in buffer:
                        start_idx = buffer.find("<think>")
                        if start_idx > 0:
                            yield buffer[:start_idx]
                        buffer = buffer[start_idx + 7:]
                        in_think_block = True
                    else:
                        # No <think> tag, but check for partial tag at end
                        # "<think>" is 7 chars. Keep last 6 chars.
                        if len(buffer) > 6:
                            yield buffer[:-6]
                            buffer = buffer[-6:]
                        else:
                            # Not enough to be a tag, but wait for more
                            break
                        
                        # If we yielded everything except the possible partial tag, 
                        # and no more came, we'd be stuck. 
                        # But this is a loop, so we'll yield the rest at the end.
                        break
                else:
                    if "</think>" in buffer:
                        end_idx = buffer.find("</think>")
                        buffer = buffer[end_idx + 8:]
                        in_think_block = False
                    else:
                        # Still in think block, discard buffer unless it might have a partial </think>
                        if len(buffer) > 8:
                            buffer = buffer[-8:] # Keep potential partial </think>
                        break
        
        # Yield remaining buffer if not in think block
        if not in_think_block and buffer:
            # Check if buffer was just a partial tag that never completed
            if buffer not in ["<think>", "</think>"] and not buffer.startswith("<think") and not buffer.startswith("</think"):
                yield buffer

    async def generate_structured(
        self,
        system_prompt: str,
        messages: list[dict],
        output_schema: type[T],
        temperature: float = 0.3,
    ) -> T:
        """Generate structured output using instructor for Pydantic models,
        falling back to JSON mode for dict/list types."""
        # Try instructor first for Pydantic models
        if isinstance(output_schema, type) and issubclass(output_schema, BaseModel):
            try:
                import instructor
                client = instructor.from_openai(self.client)
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=self._build_messages(system_prompt, messages),
                    temperature=temperature,
                    response_model=output_schema,
                )
                return response
            except Exception:
                pass  # Fall through to JSON mode

        origin = get_origin(output_schema)
        expects_dict = output_schema is dict or origin is dict
        expects_list = output_schema is list or origin is list

        # JSON mode fallback for dict/list schemas or if instructor fails
        json_system = system_prompt + "\n\nRespond ONLY with valid JSON. No other text."
        request_kwargs = {
            "model": self.model,
            "messages": self._build_messages(json_system, messages),
            "temperature": temperature,
            "max_tokens": 2048,
        }
        if expects_dict:
            request_kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(
            **request_kwargs,
        )
        content = response.choices[0].message.content or ("[]" if expects_list else "{}")
        try:
            parsed = self._parse_json_content(content)
        except json.JSONDecodeError:
            return {} if expects_dict else []

        if expects_list:
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for key in ["items", "results", "data"]:
                    value = parsed.get(key)
                    if isinstance(value, list):
                        return value
            return []

        if expects_dict and isinstance(parsed, dict):
            return parsed

        return parsed
