import pandas as pd

df_kesma = pd.read_csv('kesma_articles_with_topics.csv')
df_indep = pd.read_csv('indep_articles_with_topics.csv')

# 1. are outliers evenly distributed across outlets?
print("KESMA outliers by outlet:")
print(df_kesma[df_kesma['topic'] == -1]['outlet'].value_counts(normalize=True))

print("\nIndependent outliers by outlet:")
print(df_indep[df_indep['topic'] == -1]['outlet'].value_counts(normalize=True))

# 2. are outliers shorter than clustered articles?
df_kesma['text_length'] = df_kesma['text'].str.len()
print("\nKESMA mean text length:")
print(df_kesma.groupby(df_kesma['topic'] == -1)['text_length'].mean())

print("\nIndependent mean text length:")
df_indep['text_length'] = df_indep['text'].str.len()
print(df_indep.groupby(df_indep['topic'] == -1)['text_length'].mean())