import pandas as pd
import ast
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

# --- LOAD R2 RESULTS ---
df_kesma = pd.read_csv('bertopic_results/kesma_articles_r2.csv')
df_indep = pd.read_csv('bertopic_results/indep_articles_r2.csv')

# --- INCLUDE TOPICS BASED ON MINIMUM ARTICLE COUNTS ---
kesma_include_r2 = set(df_kesma['topic_r2'].value_counts()[df_kesma['topic_r2'].value_counts() > 120].index)
indep_include_r2 = set(df_indep['topic_r2'].value_counts()[df_indep['topic_r2'].value_counts() > 106].index)

# --- MANUAL EXCLUSIONS FOR WEIRD KEYWORD TOPICS ---
kesma_exclude_r2 = [3]
indep_exclude_r2 = [16]

kesma_include_r2 = sorted(kesma_include_r2 - set(kesma_exclude_r2))
indep_include_r2 = sorted(indep_include_r2 - set(indep_exclude_r2))

# --- FILTER TO INCLUDED TOPICS AND DROP OUTLIERS ---
df_kesma = df_kesma[
    df_kesma['topic_r2'].isin(kesma_include_r2) &
    (df_kesma['topic_r2'] != -1)
].reset_index(drop=True)

df_indep = df_indep[
    df_indep['topic_r2'].isin(indep_include_r2) &
    (df_indep['topic_r2'] != -1)
].reset_index(drop=True)

print(f"KESMA after r2 included-topic filter: {len(df_kesma)} articles")
print(f"Independent after r2 included-topic filter: {len(df_indep)} articles")

# --- LOAD STOPWORDS ---
with open('stopwords-hu.txt', 'r', encoding='utf-8') as f:
    hungarian_stopwords = [line.strip() for line in f.readlines()]

embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# -------------------------------------------------------
# PART A: SUBDIVIDE TOPIC 0 (the giant politics cluster)
# -------------------------------------------------------

df_kesma_t0 = df_kesma[df_kesma['topic_r2'] == 0].reset_index(drop=True)
df_indep_t0 = df_indep[df_indep['topic_r2'] == 0].reset_index(drop=True)

print(f"\nTopic 0 sizes — KESMA: {len(df_kesma_t0)} | Independent: {len(df_indep_t0)}")

docs_kesma_t0 = df_kesma_t0['text'].tolist()
docs_indep_t0 = df_indep_t0['text'].tolist()

topic_model_kesma_t0 = BERTopic(
    embedding_model=embedding_model,
    vectorizer_model=CountVectorizer(
        stop_words=hungarian_stopwords,
        ngram_range=(1, 2),
        min_df=3
    ),
    min_topic_size=30,
    nr_topics='auto',
    language='multilingual'
)

topic_model_indep_t0 = BERTopic(
    embedding_model=embedding_model,
    vectorizer_model=CountVectorizer(
        stop_words=hungarian_stopwords,
        ngram_range=(1, 2),
        min_df=3
    ),
    min_topic_size=26,
    nr_topics='auto',
    language='multilingual'
)

print("\nFitting KESMA topic 0 subdivision...")
topics_kesma_t0, _ = topic_model_kesma_t0.fit_transform(docs_kesma_t0)
df_kesma_t0['topic_r3'] = [f"0_{t}" for t in topics_kesma_t0]  # prefix with 0_ so you know origin

print("Fitting independent topic 0 subdivision...")
topics_indep_t0, _ = topic_model_indep_t0.fit_transform(docs_indep_t0)
df_indep_t0['topic_r3'] = [f"0_{t}" for t in topics_indep_t0]

# save subdivision results
topic_model_kesma_t0.get_topic_info().to_csv('kesma_topics_r3_t0.csv', index=False)
topic_model_indep_t0.get_topic_info().to_csv('indep_topics_r3_t0.csv', index=False)

# -------------------------------------------------------
# PART B: KEEP ALL OTHER TOPICS FROM R2 AS-IS
# -------------------------------------------------------

df_kesma_rest = df_kesma[df_kesma['topic_r2'] != 0].copy()
df_kesma_rest['topic_r3'] = df_kesma_rest['topic_r2'].astype(str)

df_indep_rest = df_indep[df_indep['topic_r2'] != 0].copy()
df_indep_rest['topic_r3'] = df_indep_rest['topic_r2'].astype(str)

# -------------------------------------------------------
# PART C: COMBINE AND SAVE FINAL CORPUS
# -------------------------------------------------------

df_kesma_final = pd.concat([df_kesma_t0, df_kesma_rest], ignore_index=True)
df_indep_final = pd.concat([df_indep_t0, df_indep_rest], ignore_index=True)

df_kesma_final.to_csv('kesma_articles_r3.csv', index=False)
df_indep_final.to_csv('indep_articles_r3.csv', index=False)

# -------------------------------------------------------
# PART D: PRINT SUMMARY OF NEW SUBTOPICS
# -------------------------------------------------------

print("\n=== KESMA TOPIC 0 SUBTOPICS ===")
kesma_t0_info = topic_model_kesma_t0.get_topic_info()
for _, row in kesma_t0_info[kesma_t0_info['Topic'] != -1].iterrows():
    try:
        keywords = ast.literal_eval(str(row['Representation']))[:6]
    except:
        keywords = str(row['Representation'])
    print(f"  0_{row['Topic']:3d} | n={row['Count']:4d} | {', '.join(keywords)}")

print("\n=== INDEPENDENT TOPIC 0 SUBTOPICS ===")
indep_t0_info = topic_model_indep_t0.get_topic_info()
for _, row in indep_t0_info[indep_t0_info['Topic'] != -1].iterrows():
    try:
        keywords = ast.literal_eval(str(row['Representation']))[:6]
    except:
        keywords = str(row['Representation'])
    print(f"  0_{row['Topic']:3d} | n={row['Count']:4d} | {', '.join(keywords)}")

# outlier check
kesma_outliers = sum(1 for t in topics_kesma_t0 if t == -1)
indep_outliers = sum(1 for t in topics_indep_t0 if t == -1)
print(f"\nKESMA t0 outliers: {kesma_outliers} / {len(docs_kesma_t0)} ({100*kesma_outliers/len(docs_kesma_t0):.1f}%)")
print(f"Independent t0 outliers: {indep_outliers} / {len(docs_indep_t0)} ({100*indep_outliers/len(docs_indep_t0):.1f}%)")

print("\nDone! Check kesma_topics_r3_t0.csv and indep_topics_r3_t0.csv")