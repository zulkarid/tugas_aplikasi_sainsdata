import os
import json
from langchain_core.documents import Document
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

DB_DIR = "./chroma_db"
LOCAL_JSON_DATASET = 'dataset_instagram-hashtag-scraper_2026-05-05_12-49-49-187.json'
MODEL_NAME = "cieloforge/Deepseek-r1-7b-spec:latest"

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class InstagramRAG:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=MODEL_NAME)
        self.rag_chain = None
        self.init_rag_system()

    def init_rag_system(self):
        if not os.path.exists(LOCAL_JSON_DATASET):
            print("⚠️ Dataset JSON belum ditemukan. RAG tidak diinisialisasi.")
            return

        print(f"🔄 [RAG] Mengindeks dataset Instagram menggunakan {MODEL_NAME}...")
        with open(LOCAL_JSON_DATASET, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)

        documents = []
        for item in posts_data:
            text_content = (
                f"Pengunggah: {item.get('ownerFullName', '')} (@{item.get('ownerUsername', '')})\n"
                f"Metrik: {item.get('likesCount', 0)} Likes, {item.get('commentsCount', 0)} Komentar\n"
                f"Waktu: {item.get('timestamp', '')}\n"
                f"Hashtags: {', '.join(item.get('hashtags', []))}\n"
                f"Isi Caption: {item.get('caption', '')}"
            )
            metadata = {"url": item.get("url", "")}
            documents.append(Document(page_content=text_content, metadata=metadata))

        vector_store = Chroma.from_documents(documents, self.embeddings, persist_directory=DB_DIR)
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})

        llm = Ollama(model=MODEL_NAME, temperature=0.2)
        
        system_prompt = (
            "Anda adalah AI Analis Media Sosial. Analisis data Instagram berikut untuk menjawab "
            "pertanyaan user secara objektif. Jika informasinya tidak ada di dalam konteks, "
            "katakan saja Anda tidak mengetahuinya berdasarkan data scraping.\n\n"
            "Konteks Data:\n{context}\n\nPertanyaan: {input}"
        )
        prompt = ChatPromptTemplate.from_template(system_prompt)

        self.rag_chain = (
            {"context": retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        print("✅ [RAG] Sistem RAG Berhasil Dimuat Menggunakan LCEL!")

    def query_ai(self, message):
        if not self.rag_chain:
            return "Sistem AI belum siap atau data belum diindeks."
        
        response = self.rag_chain.invoke(message)
        return response