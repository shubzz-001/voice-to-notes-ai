from transformers import pipeline

model = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    max_new_tokens=256
)

def generate_notes(text: str):
    prompt = f"""
Convert the lecture into clear study notes.

Return:
- Key points
- Definitions
- Examples

Lecture:
{text}
"""
    out = model(prompt)[0]["generated_text"]
    return out
