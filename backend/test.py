from pdf2image import convert_from_path
import pytesseract

# Tesseract 설치 경로 지정 (Windows 사용 시)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# OCR 함수
def extract_text_from_pdf_with_ocr(pdf_path):
    print(f"🔍 OCR 처리 시작: {pdf_path}")
    images = convert_from_path(
        pdf_path,
        dpi=300,
        poppler_path=r"C:\Users\DS\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
    )
    result_text = ""

    for i, img in enumerate(images):
        print(f"📄 페이지 {i+1} 인식 중...")
        text = pytesseract.image_to_string(img, lang='kor+eng')
        result_text += f"\n--- Page {i+1} ---\n{text}"

    print("✅ OCR 완료")
    return result_text

# 테스트용 PDF 경로
pdf_path = r"C:\Users\DS\flask-react-project\backend\crawler\hana_attachment_downloads\제안참여 신청서.pdf"

# 실행
text = extract_text_from_pdf_with_ocr(pdf_path)
print("📝 추출된 텍스트:")
print(text)
