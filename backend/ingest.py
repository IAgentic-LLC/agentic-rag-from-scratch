"""Build the search index: split the docs into chunks, embed them, save to data/index.json."""
from app import config
from app.corpus import load_chunks
from app.models import embedder
from app.retrieval import HybridIndex

if __name__ == "__main__":
    chunks = load_chunks(config.DOCS_DIR)
    index = HybridIndex.build(chunks, embedder())
    index.save(config.INDEX_PATH)
    print(f"Indexed {len(chunks)} chunks from {len({c.doc for c in chunks})} documents into {config.INDEX_PATH.name}")
