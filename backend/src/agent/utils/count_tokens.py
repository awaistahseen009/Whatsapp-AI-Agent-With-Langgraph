import tiktoken

_encoder = tiktoken.get_encoding("cl100k_base")

DIRECT_INJECT_THRESHOLD = 3000  
PAGE_LIMIT = 40
FILE_SIZE_LIMIT_MB = 15

def count_tokens(text: str) -> int:
    return len(_encoder.encode(text))

def should_chunk_document(extracted_text: str) -> bool:
    return count_tokens(extracted_text) > DIRECT_INJECT_THRESHOLD

if __name__ == "__main__":
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader("src/utils/sample_docs/sample-doc.pdf", mode = "single")
    docs = loader.load()
    print(count_tokens(docs[0].page_content))
   