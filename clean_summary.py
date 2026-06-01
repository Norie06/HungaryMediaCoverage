import pandas as pd
import ast

def extract_top_topics(csv_path, top_n_keywords=10, min_count=30, exclude_outliers=True):
    df = pd.read_csv(csv_path)
    
    if exclude_outliers:
        df = df[df['Topic'] != -1]
    
    df = df[df['Count'] >= min_count].sort_values('Count', ascending=False)
    
    results = []
    for _, row in df.iterrows():
        # parse the representation column which is a string representation of a list
        try:
            keywords = ast.literal_eval(row['Representation'])
            keywords = keywords[:top_n_keywords]
        except:
            keywords = row['Representation']
        
        results.append({
            'topic': row['Topic'],
            'count': row['Count'],
            'keywords': ', '.join(keywords)
        })
    
    return pd.DataFrame(results)

kesma_topics = extract_top_topics('bertopic_results/kesma_topics_r3_t0.csv')
indep_topics = extract_top_topics('bertopic_results/indep_topics_r3_t0.csv')

print("=== KESMA TOP TOPICS ===")
print(kesma_topics.to_string(index=False))

print("\n=== INDEPENDENT TOP TOPICS ===")
print(indep_topics.to_string(index=False))

# save for easy reference
kesma_topics.to_csv('bertopic_results/kesma_form_topics.csv', index=False)
indep_topics.to_csv('bertopic_results/indep_form_topics.csv', index=False)