from langchain_teddynote.document_loaders import HWPLoader
from langchain_community.document_loaders import UnstructuredExcelLoader


loader = HWPLoader(r'C:\Users\DS\flask-react-project\backend\crawler\woori_attachment_downloads\3 입찰보증금 납부서.hwp')

docs = loader.load()

loader_excel = UnstructuredExcelLoader(r"C:\Users\DS\flask-react-project\backend\crawler\woori_attachment_downloads\붙임1. 도입사양.xlsx", mode = 'elements')

docs_excel = loader_excel.load()

print(docs[0].page_content[:1000])

print(docs_excel[0].page_content[:200])

