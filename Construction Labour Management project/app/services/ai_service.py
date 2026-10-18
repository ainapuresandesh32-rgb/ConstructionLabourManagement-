import os, json
from dotenv import load_dotenv
load_dotenv()

def ai_available():
    return bool(os.getenv("OPENAI_API_KEY"))

def ask_ai(question, context):
    key=os.getenv("OPENAI_API_KEY")
    if not key:
        return "AI is not configured. Add OPENAI_API_KEY to your .env file. The rest of the system works without AI."
    try:
        from openai import OpenAI
        client=OpenAI(api_key=key)
        response=client.responses.create(
            model=os.getenv("OPENAI_MODEL","gpt-5-mini"),
            input=f"""You are a construction labour management assistant.
Answer concisely and practically. Use only the supplied data.
Question: {question}
Data: {json.dumps(context, default=str)}"""
        )
        return response.output_text
    except Exception as e:
        return f"AI service unavailable: {str(e)[:180]}"
