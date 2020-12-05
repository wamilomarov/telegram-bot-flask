import pickle
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer


class NeighborFinder:
    count_vectorizer = None
    data = None
    nearest_neighbours = None
    tfidf_transformer = None

    def __init__(self):
        self.count_vectorizer = pickle.load(open("pkl/feature.pkl", "rb"))
        self.nearest_neighbours = pickle.load(open("pkl/knn.pkl", "rb"))
        self.tfidf_transformer = pickle.load(open("pkl/tfidf_transformer.pkl", "rb"))

    def get_indexes_of_neighbors(self, sentence):
        sentence_count = self.count_vectorizer.transform([sentence])
        sentence_tfidf = self.tfidf_transformer.transform(sentence_count)
        neighbors_data = self.nearest_neighbours.kneighbors(sentence_tfidf, n_neighbors=5)
        return neighbors_data[1]
