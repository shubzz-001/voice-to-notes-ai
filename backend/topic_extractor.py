import spacy
from collections import Counter
import re

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("Warning: spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


def extract_topics(text: str, max_topics: int = 10):
    """
    Extract key topics from lecture text using NLP
    Returns a list of important topics/keywords
    """
    if not text or not nlp:
        return []

    try:
        # Process text
        doc = nlp(text.lower())

        # Extract noun chunks and named entities
        topics = []

        # Named entities (people, places, organizations, etc.)
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT", "PRODUCT", "LAW", "NORP"]:
                topics.append(ent.text.title())

        # Important noun phrases
        for chunk in doc.noun_chunks:
            # Filter out very short or common chunks
            if len(chunk.text.split()) >= 2 and len(chunk.text) > 5:
                # Skip if starts with common words
                if not chunk.text.startswith(("this", "that", "these", "those", "what", "which")):
                    topics.append(chunk.text.title())

        # Extract capitalized words (likely important terms)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        topics.extend(capitalized)

        # Count frequency and get most common
        topic_counts = Counter(topics)

        # Filter out very common words and get top topics
        common_words = {"The", "This", "That", "These", "Those", "What", "Which", "Who", "Where", "When"}
        filtered_topics = [
            topic for topic, count in topic_counts.most_common(max_topics * 2)
            if topic not in common_words and count > 1
        ]

        # Return unique topics
        seen = set()
        unique_topics = []
        for topic in filtered_topics:
            if topic.lower() not in seen:
                seen.add(topic.lower())
                unique_topics.append(topic)
                if len(unique_topics) >= max_topics:
                    break

        return unique_topics

    except Exception as e:
        print(f"Error extracting topics: {e}")
        return []


def extract_topics_simple(text: str, max_topics: int = 10):
    """
    Simple fallback topic extraction without spaCy
    Uses capitalized words and frequency analysis
    """
    if not text:
        return []

    # Extract capitalized multi-word terms
    topics = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)

    # Count frequencies
    topic_counts = Counter(topics)

    # Filter common words
    common = {"The", "This", "That", "These", "A", "An", "In", "On", "At", "To", "For"}
    filtered = [
        topic for topic, count in topic_counts.most_common(max_topics * 2)
        if topic not in common and count > 1 and len(topic) > 3
    ]

    return filtered[:max_topics]