
from docx import Document
doc = Document()
doc.add_paragraph("Hello World")
doc.save("test_docx.docx")
print("Done")
