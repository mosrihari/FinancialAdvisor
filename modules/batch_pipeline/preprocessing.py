import numpy as np
from unstructured.cleaners.core import (
    clean_extra_whitespace, 
    clean_non_ascii_chars,
    group_broken_paragraphs
)
import re
from chromadb.utils import embedding_functions
import settings

model_name = settings.EMBEDDING_MODEL_NAME
model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name)

def clean_data(contents):
    TAG_RE = re.compile(r'<[^>]+>')
    contents = TAG_RE.sub('', contents)
    contents = group_broken_paragraphs(contents)
    contents = clean_non_ascii_chars(contents)
    contents = clean_extra_whitespace(contents)
    return contents

def add_to_chromadb(contents, db):
    
    collection_name = settings.CHROMA_DB_COLLECTION
    document = contents
    collection_status = False
    while collection_status != True:
        try:
            collection = db.get_or_create_collection(name=collection_name)
            collection_status = True
        except Exception as e:
            pass
    results = collection.query(
        query_texts=[contents],
        n_results=2
    )
    # checking duplicates
    match_list = [d for d in results['distances'][0] if np.abs(d) < 0.0001]
    
    if(not match_list):
        embeddings_sent = model([document])
        pattern = re.compile(r'\d+')
        result_ids = collection.get()['ids']
        # Extract numbers from each string in results
        result_ids = sorted([int(pattern.search(item).group()) for item in result_ids])
        if(len(result_ids) == 0):
            # if this is the first entry
            final_id = 'ID1'
            collection.add(embeddings=embeddings_sent, documents=[document], ids=[final_id])
        else:
            final_id = "ID"+str(result_ids[-1] + 1)
            collection.add(embeddings=embeddings_sent, documents=[document], ids=[final_id])
    else:
        pass
    return True

def query_data(collection, question): #list of list
    results = collection.query(
                    query_texts=[question],
                    n_results=settings.N_QUERY_RESULTS
                    )
    return results['documents']

