import nltk
import gensim

from enum import Enum
from client.client import Client
from nltk.tokenize import word_tokenize
from nltk.stem import LancasterStemmer

uri = "https://sandbox-authservice.priaid.ch/login"
api_key = "alexander.cristurean@yahoo.com"
secret_key = "q2TXc6s7HWi8t4FRr"
healthServiceUrl = "https://sandbox-healthservice.priaid.ch"
language = "en-gb"
Gender = Enum('Gender', 'Male Female')

SelectorStatus = Enum('SelectorStatus', 'Man Woman Boy Girl')

nltk.download('wordnet')
nltk.download('punkt')
nltk.download('stopwords')
lemmer = nltk.WordNetLemmatizer()
lancaster = LancasterStemmer()
english_stopwords = set(nltk.corpus.stopwords.words('english'))


class Bot:

    def __init__(self, client):
        self._client = client
        raw_documents = self._client.loadSymptoms()
        self._symptoms = []
        self._ids = []
        for r in raw_documents:
            self._symptoms.append(r.get("Name"))
            self._ids.append(r.get("ID"))
        gen_docs = [self._get_tokens(text.lower()) for text in self._symptoms]
        stem_docs = self.stem_words(gen_docs)
        self._plain_dictionary = gensim.corpora.Dictionary(gen_docs)
        self._dictionary = gensim.corpora.Dictionary(stem_docs)
        self._corpus = [self._dictionary.doc2bow(gen_doc) for gen_doc in stem_docs]
        self._tf_idf = gensim.models.TfidfModel(self._corpus)
        self._sims = gensim.similarities.Similarity("C:\\TextMining\\", self._tf_idf[self._corpus],
                                                    num_features=len(self._dictionary))

    def _get_tokens(self, text):
        tokens = word_tokenize(text)
        return tokens

    def get_most_similiar(self, list):
        max = -1
        index = 0
        for i in list:
            if (i > max):
                max = i

        if max == 0:
            return -1
        for i in list:
            if i == max:
                return index
            else:
                index += 1

    def transform_to_words(self, list):
        result = ""
        for tuple in list:
            word = self._plain_dictionary[tuple[0]]
            result = result + " " + word
        return result.strip()

    def stem_words(self, docs):
        stem_docs = []

        for doc in docs:
            stem_doc = []
            for word in doc:
                stem_word = lancaster.stem(word)
                stem_doc.append(stem_word)
            stem_docs.append(stem_doc)
        return stem_docs

    def stem_query(self, query):
        query_doc = []
        for word in query:
            query_doc.append(lancaster.stem(word))
        return query_doc


    def talk_to_Bot(self, query):
        tokens = self._get_tokens(query)
        query_doc = self.stem_query(tokens)
        query_doc_bow = self._dictionary.doc2bow(query_doc)
        query_doc_tf_idf = self._tf_idf[query_doc_bow]
        index = self.get_most_similiar(self._sims[query_doc_tf_idf])
        if index == -1:
            return {'name': "I did not understand, can you please rephrase?",
                    'id': -1}
        symptom = self._symptoms[index].lower()
        id = self._ids[index]
        return {'name': symptom,
                'id': id}
