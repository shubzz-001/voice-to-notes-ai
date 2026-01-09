import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("Hello, world! This is a test sentence.")

print("Model working")