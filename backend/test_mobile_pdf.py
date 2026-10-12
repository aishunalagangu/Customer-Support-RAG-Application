
from langchain_community.document_loaders import PyPDFLoader
from pathlib import Path

pdf_path = Path("documents/Mobile_Support_Knowledge_Base (1).pdf")

if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found: {pdf_path.resolve()}")

pages = PyPDFLoader(str(pdf_path)).load()

print("PDF:", pdf_path.name)
print("Total pages:", len(pages))

for index, page in enumerate(pages[:4], start=1):
    print(f"\n--- PAGE {index} ---")
    print(page.page_content[:1000])
