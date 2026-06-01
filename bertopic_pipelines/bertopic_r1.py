import json
import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer


def load_huspacy_model():
    """Load HuSpaCy if available for Hungarian tokenization and lemmatization."""
    try:
        import spacy
        print("Loading HuSpaCy Hungarian pipeline...")
        return spacy.load('hu_core_ud_lg', disable=['parser', 'ner'])
    except Exception as exc:
        print(f"HuSpaCy not available or failed to load: {exc}")
        return None


def huspacy_preprocess(docs, nlp):
    """Lemmatize and normalize Hungarian documents with HuSpaCy."""
    processed = []
    for doc in nlp.pipe(docs, batch_size=64):
        tokens = [
            (token.lemma_ or token.text).strip().lower()
            for token in doc
            if token.is_alpha
        ]
        processed.append(' '.join(tokens))
    return processed


# --- 1. LOAD DATA ---
files = {
    'telex': './articles/by_outlet/telex.json',
    '444': './articles/by_outlet/444.json',
    '24hu': './articles/by_outlet/24hu.json',
    'magyarnemzet': './articles/by_outlet/magyarnemzet.json',
    'origo': './articles/by_outlet/origo.json',
    'mandiner': './articles/by_outlet/mandiner.json',
}

dfs = []
for outlet, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    articles = pd.json_normalize(df['articles'])
    articles['outlet'] = df['outlet']
    dfs.append(articles)

df = pd.concat(dfs, ignore_index=True)
print(f"Total articles: {len(df)}")
print(df['outlet_type'].value_counts())

# --- 2. PREPARE TEXT ---
def to_str(val):
    if isinstance(val, list):
        return ' '.join(str(v) for v in val)
    return str(val) if val is not None else ''

df['text'] = df['title'].apply(to_str) + ' ' + df['excerpt'].apply(to_str)
df['text'] = df['text'].str.strip().str.lower()
df = df[df['text'].str.len() > 0].reset_index(drop=True)

# --- OPTIONAL HUSPACY PREPROCESSING ---
huspacy = load_huspacy_model()
if huspacy is not None:
    print('Applying HuSpaCy lemmatization and tokenization...')
    df['text'] = huspacy_preprocess(df['text'].tolist(), huspacy)

# --- 3. SPLIT BY OUTLET TYPE ---
df_kesma = df[df['outlet_type'] == 'kesma'].reset_index(drop=True)
df_indep = df[df['outlet_type'] == 'independent'].reset_index(drop=True)

print(f"\nKESMA articles: {len(df_kesma)}")
print(f"Independent articles: {len(df_indep)}")

docs_kesma = df_kesma['text'].tolist()
docs_indep = df_indep['text'].tolist()

# --- 4. LOAD STOPWORDS ---
with open('stopwords-hu.txt', 'r', encoding='utf-8') as f:
    hungarian_stopwords = [line.strip() for line in f.readlines()]
# with open('hungarian_stopwords.json', 'r', encoding='utf-8') as f:
#     hungarian_stopwords = json.load(f)

# --- 5. SET UP MODELS ---
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings_kesma = embedding_model.encode(docs_kesma, show_progress_bar=True)
embeddings_indep = embedding_model.encode(docs_indep, show_progress_bar=True)

vectorizer_kesma = CountVectorizer(stop_words=hungarian_stopwords,
                                    ngram_range=(1, 2),
                                    min_df=3)

vectorizer_indep = CountVectorizer(stop_words=hungarian_stopwords,
                                    ngram_range=(1, 2),
                                    min_df=3)

topic_model_kesma = BERTopic(
    embedding_model=embedding_model,
    vectorizer_model=vectorizer_kesma,
    min_topic_size=15,
    nr_topics='auto',
    language='multilingual'
)

topic_model_indep = BERTopic(
    embedding_model=embedding_model,
    vectorizer_model=vectorizer_indep,
    min_topic_size=10,
    nr_topics='auto',
    language='multilingual'
)

# --- 6. FIT MODELS ---
print("Fitting KESMA model...")
topics_kesma, probs_kesma = topic_model_kesma.fit_transform(docs_kesma)
topics_kesma = topic_model_kesma.reduce_outliers(
    docs_kesma, 
    topics_kesma, 
    probabilities=probs_kesma,
    strategy="probabilities", 
    threshold=0.05
)
df_kesma['topic'] = topics_kesma

print("Fitting independent model...")
topics_indep, probs_indep = topic_model_indep.fit_transform(docs_indep)
topics_indep = topic_model_indep.reduce_outliers(
    docs_indep, 
    topics_indep, 
    probabilities=probs_indep,
    strategy="probabilities", 
    threshold=0.05
)
df_indep['topic'] = topics_indep

# --- 7. CHECK OUTLIERS ---
outlier_kesma = sum(1 for t in topics_kesma if t == -1)
outlier_indep = sum(1 for t in topics_indep if t == -1)
print(f"\nKESMA outliers: {outlier_kesma} / {len(docs_kesma)} ({100*outlier_kesma/len(docs_kesma):.1f}%)")
print(f"Independent outliers: {outlier_indep} / {len(docs_indep)} ({100*outlier_indep/len(docs_indep):.1f}%)")

# --- 8. SAVE RESULTS ---
topic_model_kesma.get_topic_info().to_csv('kesma_topics.csv', index=False)
topic_model_indep.get_topic_info().to_csv('indep_topics.csv', index=False)

df_kesma.to_csv('kesma_articles_with_topics.csv', index=False)
df_indep.to_csv('indep_articles_with_topics.csv', index=False)

print("\nDone! Check kesma_topics.csv and indep_topics.csv")