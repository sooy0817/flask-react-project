from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI


def summarize_pdf(path: str) -> str:

    loader = PyMuPDFLoader(path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
    chunks = splitter.split_documents(docs)

    embedding = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embedding)

    retriever = vectorstore.as_retriever()
    llm  = ChatOpenAI(temperature = 0)

    rag_chain = RetrievalQA.from_chain_type(
        llm = llm,
        retriever = retriever,
        return_source_documents = False
    )