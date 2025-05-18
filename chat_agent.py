import os
import re
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_core.language_models import LLM
from langchain_core.outputs import Generation, LLMResult
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType

# === Load environment variables from .env file ===
load_dotenv()

# === Gemini LangChain-Compatible Wrapper ===
class GeminiLLM(LLM):
    model_name: str = "gemini-1.5-flash"
    api_key: str = ""

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        return response.text.strip()

    @property
    def _llm_type(self) -> str:
        return "custom-gemini"

# === Prompt Builder ===
def build_prompt(user_input: str, language: str = "python") -> str:
    return (
        f"Write a concise {language} function to {user_input}.\n"
        f"Return ONLY the {language} code inside a ```{language}``` code block without explanation."
    )

# === Code Extractor ===
def extract_code(response: str, language: str) -> str:
    pattern = rf"```{language.lower()}(.*?)```"
    match = re.search(pattern, response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()

# === Tool Function (Python & C++ Only) ===
def generate_code(prompt: str) -> str:
    try:
        if "::" in prompt:
            task, lang = map(str.strip, prompt.split("::", 1))
            language = lang.lower()
        else:
            task = prompt
            language = "python"

        if language not in ["python", "cpp"]:
            return "❌ Only Python and C++ are supported."

        full_prompt = build_prompt(task, language)
        response = llm(full_prompt)

        code = extract_code(response, language)
        if not code:
            return "⚠️ No valid code block found."
        return f"✅ {language.upper()} Code:\n{code}"

    except Exception as e:
        return f"❌ Error during code generation: {e}"

# === Get API Key from Environment ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY environment variable not set!")

# === Instantiate Gemini LLM ===
llm = GeminiLLM(api_key=GEMINI_API_KEY)

# === Tool for LangChain Agent ===
tools = [
    Tool(
        name="CodeGenerator",
        func=generate_code,
        description="Generates Python or C++ code from a natural language prompt. Format: task :: language"
    )
]

# === Initialize LangChain Agent ===
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=5,
    max_execution_time=30
)

# === Main Loop (Optional for Local Testing) ===
if __name__ == "__main__":
    print("👋 Welcome! Use format: describe task :: language (e.g., 'generate Fibonacci :: cpp')")
    while True:
        user_input = input("\nPrompt (or type 'exit'): ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        result = agent.run(user_input)
        print("▶️ Result:", result)

