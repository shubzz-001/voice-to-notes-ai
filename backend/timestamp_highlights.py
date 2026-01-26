from typing import List, Dict
import re
from collections import Counter


def extract_key_moments(segments: List[Dict], max_highlights: int = 10) -> List[Dict]:
    """
    Extract key moments/highlights from transcript segments with timestamps

    Args:
        segments: List of dicts with 'start', 'end', 'text' keys
        max_highlights: Maximum number of highlights to return

    Returns:
        List of dicts with 'timestamp', 'text', 'importance' keys
    """
    if not segments:
        return []

    try:
        highlights = []

        for segment in segments:
            text = segment.get('text', '').strip()
            start = segment.get('start', 0)

            if not text:
                continue

            # Calculate importance score
            importance = calculate_importance(text)

            if importance > 0.3:  # Threshold for being a "highlight"
                highlights.append({
                    'timestamp': format_timestamp(start),
                    'time_seconds': start,
                    'text': text,
                    'importance': round(importance, 2)
                })

        # Sort by importance and return top highlights
        highlights.sort(key=lambda x: x['importance'], reverse=True)
        return highlights[:max_highlights]

    except Exception as e:
        print(f"Error extracting key moments: {e}")
        return []


def calculate_importance(text: str) -> float:
    """
    Calculate importance score for a text segment
    Based on various heuristics
    """
    score = 0.0

    # Length factor (moderate length preferred)
    word_count = len(text.split())
    if 10 <= word_count <= 30:
        score += 0.3
    elif word_count > 30:
        score += 0.2

    # Important phrases
    important_phrases = [
        r'\bimportant\b', r'\bkey\b', r'\bmain\b', r'\bcrucial\b',
        r'\bessential\b', r'\bsignificant\b', r'\bnote that\b',
        r'\bremember\b', r'\bfocus on\b', r'\bpay attention\b',
        r'\bin summary\b', r'\bto conclude\b', r'\bin conclusion\b',
        r'\bfirst\b', r'\bsecond\b', r'\bthird\b', r'\bfinally\b',
        r'\btherefore\b', r'\bhowever\b', r'\bmoreover\b'
    ]

    for phrase in important_phrases:
        if re.search(phrase, text, re.IGNORECASE):
            score += 0.2
            break

    # Question detection (questions are often important)
    if '?' in text:
        score += 0.15

    # Capital words (proper nouns, important terms)
    capital_words = re.findall(r'\b[A-Z][a-z]+\b', text)
    if len(capital_words) >= 2:
        score += 0.15

    # Numbers and data (often important)
    if re.search(r'\d+', text):
        score += 0.1

    # Definition patterns
    definition_patterns = [r'\bis\b', r'\bmeans\b', r'\brefers to\b', r'\bdefined as\b']
    for pattern in definition_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.2
            break

    return min(score, 1.0)  # Cap at 1.0


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to MM:SS or HH:MM:SS format
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def group_highlights_by_topic(highlights: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group highlights by detected topics/themes
    """
    if not highlights:
        return {}

    # Extract keywords from each highlight
    grouped = {"General": []}

    for highlight in highlights:
        text = highlight['text']
        # Extract capitalized terms as potential topics
        topics = re.findall(r'\b[A-Z][a-z]+\b', text)

        if topics:
            topic = topics[0]
            if topic not in grouped:
                grouped[topic] = []
            grouped[topic].append(highlight)
        else:
            grouped["General"].append(highlight)

    return grouped


def create_chapter_markers(segments: List[Dict], num_chapters: int = 5) -> List[Dict]:
    """
    Create chapter markers by identifying topic transitions
    """
    if not segments or len(segments) < num_chapters:
        return []

    chapters = []
    segment_size = len(segments) // num_chapters

    for i in range(num_chapters):
        start_idx = i * segment_size
        if start_idx >= len(segments):
            break

        segment = segments[start_idx]

        # Try to create a chapter title from the segment
        text = segment.get('text', '').strip()
        words = text.split()[:8]  # First 8 words
        title = ' '.join(words)

        if len(title) > 50:
            title = title[:47] + "..."

        chapters.append({
            'timestamp': format_timestamp(segment.get('start', 0)),
            'time_seconds': segment.get('start', 0),
            'title': title or f"Chapter {i + 1}"
        })

    return chapters


def format_highlights_for_display(highlights: List[Dict]) -> str:
    """
    Format highlights for pretty display
    """
    if not highlights:
        return "No key moments found."

    output = "# 🎯 Key Moments\n\n"

    for i, highlight in enumerate(highlights, 1):
        output += f"## [{highlight['timestamp']}] Highlight {i}\n"
        output += f"{highlight['text']}\n\n"

    return output
