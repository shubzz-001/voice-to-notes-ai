from transformers import pipeline
import json

# Models
segmenter = pipeline(
    "text2text-generation",
    model="google/flan-t5-large",
    max_length=1024
)

notes_model = pipeline(
    "text2text-generation",
    model="google/flan-t5-large",
    max_length=1024
)

# ---------------- TOPIC SEGMENTATION ----------------
def segment_topics(transcript: str):
    """
    Split a lecture transcript into logical topics.
    """

    prompt = f"""
You are a university professor.

Split the following lecture transcript into logical topics.

Return ONLY valid JSON.

FORMAT:
[
  {{
    "topic_title": "Topic Name",
    "content": "Transcript content of this topic"
  }}
]

LECTURE TRANSCRIPT:
{transcript}
"""

    result = segmenter(prompt)[0]["generated_text"]

    try:
        topics = json.loads(result)
    except json.JSONDecodeError:
        topics = [
            {
                "topic_title": "Full Lecture",
                "content": transcript
            }
        ]

    return topics


# ---------------- STRUCTURED NOTES ----------------
def generate_notes(transcript: str):
    """
    Generate structured notes from transcript.
    """

    prompt = f"""
You are an expert professor.

Convert the following lecture content into structured exam-ready notes.

Return ONLY valid JSON.

FORMAT:
{{
  "title": "<Topic>",
  "key_points": ["point1", "point2"],
  "definitions": [
    {{"term": "Term", "definition": "Explanation"}}
  ],
  "examples": ["example1", "example2"],
  "exam_tips": ["tip1", "tip2"]
}}

LECTURE CONTENT:
{transcript}
"""

    result = notes_model(prompt)[0]["generated_text"]

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {
            "title": "Notes",
            "raw_output": result
        }


# ---------------- MASTER FUNCTION ----------------
def generate_topic_wise_notes(transcript: str):
    """
    Full pipeline:
    Transcript → Topics → Notes per topic
    """

    topics = segment_topics(transcript)

    final_notes = []

    for topic in topics:
        notes = generate_notes(topic["content"])
        notes["topic_title"] = topic["topic_title"]
        final_notes.append(notes)

    return final_notes

def attach_timestamps(topics, segments):
    """
    Attach approximate timestamps to topics based on segment matching
    """

    enriched_topics = []

    for topic in topics:
        topic_text = topic["content"].lower()
        matched_segment = None

        for seg in segments:
            if topic_text[:50] in seg["text"].lower():
                matched_segment = seg
                break

        if matched_segment:
            topic["start_time"] = matched_segment["start"]
            topic["end_time"] = matched_segment["end"]
        else:
            topic["start_time"] = None
            topic["end_time"] = None

        enriched_topics.append(topic)

    return enriched_topics

