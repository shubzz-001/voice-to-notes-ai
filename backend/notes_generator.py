from transformers import pipeline

generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

def generate_notes(transcript: str) -> str:
    prompt = f"""
    You are an expert professor.

    Convert the following lecture into:
    - Title
    - Clear headings
    - Bullet points
    - Key definitions
    - Short examples

    Keep language simple and student-friendly.

    Lecture:
    {transcript}
    """

    result = generator(
        prompt,
        max_length=500
    )

    return result[0]["generated_text"]
