from transformers import pipeline

quiz_generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

def generate_quiz(text: str):
    '''Generate quiz questions from the given text.'''
    
    prompt = f"""
    Create:
    - 3 MCQs
    - 2 short answer questions
    from the following lecture.

    Lecture:
    {text}
    """

    result = quiz_generator(prompt, max_length=300)

    return result[0]["generated_text"]
