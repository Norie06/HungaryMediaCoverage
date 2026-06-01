import json
import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

# --- LOAD PREPROCESSED DATAFRAMES FROM R1 ---
df_kesma = pd.read_csv('./bertopic_results/kesma_articles_with_topics.csv')
df_indep = pd.read_csv('./bertopic_results/indep_articles_with_topics.csv')

# --- DEFINE EXCLUSIONS BASED ON R1 INSPECTION ---
kesma_exclude = [2, 3, 4, 5, 10, 11, 13, 15, 17, 18, 22, 24, 30, 33, 37, 38, 39, 40, 42, 43, 44, 45, 47, 49, 50, 51, 54]   # health, celebrity, boilerplate, weather, sex, DST, earthquake
indep_exclude = [3, 6, 9, 40, 49, 50, 51, 53, 56, 63, 64, 68, 70, 71, 75, 79, 89, 94, 96]             # Mexico cartel, China

# --- FILTER OUT EXCLUDED TOPICS AND OUTLIERS ---
df_kesma_r2 = df_kesma[
    (~df_kesma['topic'].isin(kesma_exclude)) & 
    (df_kesma['topic'] != -1)
].reset_index(drop=True)

df_indep_r2 = df_indep[
    (~df_indep['topic'].isin(indep_exclude)) & 
    (df_indep['topic'] != -1)
].reset_index(drop=True)

print(f"KESMA r2: {len(df_kesma_r2)} articles")
print(f"Independent r2: {len(df_indep_r2)} articles")

docs_kesma_r2 = df_kesma_r2['text'].tolist()
docs_indep_r2 = df_indep_r2['text'].tolist()

# --- LOAD STOPWORDS ---
with open('stopwords-hu.txt', 'r', encoding='utf-8') as f:
    hungarian_stopwords = [line.strip() for line in f.readlines()]

# --- SET UP MODELS ---
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

topic_model_kesma_r2 = BERTopic(
    embedding_model=embedding_model,
    vectorizer_model=CountVectorizer(stop_words=hungarian_stopwords, ngram_range=(1,2), min_df=3),
    min_topic_size=30,
    nr_topics='auto',
    language='multilingual'
)

topic_model_indep_r2 = BERTopic(
    embedding_model=embedding_model,
    vectorizer_model=CountVectorizer(stop_words=hungarian_stopwords, ngram_range=(1,2), min_df=3),
    min_topic_size=26,
    nr_topics='auto',
    language='multilingual'
)

# --- FIT ---
print("Round 2 - Fitting KESMA model...")
topics_kesma_r2, _ = topic_model_kesma_r2.fit_transform(docs_kesma_r2)
df_kesma_r2['topic_r2'] = topics_kesma_r2

print("Round 2 - Fitting independent model...")
topics_indep_r2, _ = topic_model_indep_r2.fit_transform(docs_indep_r2)
df_indep_r2['topic_r2'] = topics_indep_r2

# --- SAVE ---
topic_model_kesma_r2.get_topic_info().to_csv('./bertopic_results/kesma_topics_r2.csv', index=False)
topic_model_indep_r2.get_topic_info().to_csv('./bertopic_results/indep_topics_r2.csv', index=False)
df_kesma_r2.to_csv('./bertopic_results/kesma_articles_r2.csv', index=False)
df_indep_r2.to_csv('./bertopic_results/indep_articles_r2.csv', index=False)

print("Done!")