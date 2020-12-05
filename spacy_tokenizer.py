import string
from spacy.lang.en.stop_words import STOP_WORDS
from spacy.lang.en import English


class SpacyTokenizer:
    punctuations = None
    parser = None

    def __init__(self):
        self.punctuations = string.punctuation
        self.parser = English()

    def tokenize(self, sentence):
        parsed_sentence = self.parser(sentence)

        items = [word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_ for word in parsed_sentence]

        words = [word for word in items if word not in STOP_WORDS and word not in self.punctuations]

        return " ".join(words)
