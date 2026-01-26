from transformers import pipeline
import re
from typing import List, Dict
import json

# Initialize the model
quiz_model = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)


def generate_flashcards(text: str, num_cards: int = 10) -> List[Dict[str, str]]:
    """
    Generates flashcards (Q&A pairs) from lecture text
    Returns list of dicts with 'question' and 'answer' keys
    """
    if not text or len(text) < 100:
        return []

    try:
        # Split text into chunks for better processing
        chunks = split_text_into_chunks(text, max_length=500)

        flashcards = []
        cards_per_chunk = max(2, num_cards // len(chunks))

        for chunk in chunks[:min(5, len(chunks))]:  # Limit to 5 chunks
            prompt = f"""Create {cards_per_chunk} flashcard questions and answers from this text.
Format each as:
Q: [question]
A: [answer]

Text: {chunk}"""

            result = quiz_model(prompt, max_length=300, num_return_sequences=1)
            generated = result[0]["generated_text"]

            # Parse the generated flashcards
            cards = parse_flashcards(generated)
            flashcards.extend(cards)

            if len(flashcards) >= num_cards:
                break

        return flashcards[:num_cards]

    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return generate_flashcards_simple(text, num_cards)


def generate_flashcards_simple(text: str, num_cards: int = 10) -> List[Dict[str, str]]:
    """
    Simple fallback method to generate flashcards using basic NLP
    """
    flashcards = []

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

    # Look for definition patterns
    definition_patterns = [
        r'(.+?)\s+is\s+(.+)',
        r'(.+?)\s+refers to\s+(.+)',
        r'(.+?)\s+means\s+(.+)',
        r'(.+?)\s+defined as\s+(.+)',
    ]

    for sentence in sentences[:num_cards * 2]:
        for pattern in definition_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                term = match.group(1).strip()
                definition = match.group(2).strip()

                # Clean up
                if len(term) < 50 and len(definition) < 200:
                    flashcards.append({
                        "question": f"What is {term}?",
                        "answer": definition.capitalize()
                    })
                    break

        if len(flashcards) >= num_cards:
            break

    # If not enough, create general questions from key sentences
    if len(flashcards) < num_cards:
        for sentence in sentences[len(flashcards):num_cards]:
            # Create fill-in-the-blank style questions
            words = sentence.split()
            if len(words) > 5:
                # Blank out an important word
                important_words = [w for w in words if len(w) > 5 and w[0].isupper()]
                if important_words:
                    word_to_blank = important_words[0]
                    question = sentence.replace(word_to_blank, "______")

                    flashcards.append({
                        "question": f"Fill in the blank: {question}",
                        "answer": word_to_blank
                    })

    return flashcards[:num_cards]


def parse_flashcards(text: str) -> List[Dict[str, str]]:
    """
    Parse flashcard text in Q: A: format
    """
    flashcards = []

    # Split by Q: markers
    qa_pairs = re.split(r'\n?Q:', text)

    for pair in qa_pairs[1:]:  # Skip first empty split
        parts = re.split(r'\n?A:', pair, maxsplit=1)

        if len(parts) == 2:
            question = parts[0].strip()
            answer = parts[1].strip()

            if question and answer:
                flashcards.append({
                    "question": question,
                    "answer": answer
                })

    return flashcards


def split_text_into_chunks(text: str, max_length: int = 500) -> List[str]:
    """
    Split text into manageable chunks for processing
    """
    sentences = re.split(r'[.!?]+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def format_flashcards_for_export(flashcards: List[Dict[str, str]]) -> str:
    """
    Format flashcards for display or export
    """
    output = "# Flashcards\n\n"

    for i, card in enumerate(flashcards, 1):
        output += f"## Card {i}\n\n"
        output += f"**Q:** {card['question']}\n\n"
        output += f"**A:** {card['answer']}\n\n"
        output += "---\n\n"

    return output