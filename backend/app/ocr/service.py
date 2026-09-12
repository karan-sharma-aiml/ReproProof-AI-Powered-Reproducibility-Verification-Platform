from __future__ import annotations

from app.providers.contracts import OCRProvider
from app.providers.mock import MockOCRProvider


class TesseractProvider(MockOCRProvider):
    name = "tesseract"


class EasyOCRProvider(MockOCRProvider):
    name = "easyocr"


class GoogleVisionProvider(MockOCRProvider):
    name = "google-vision"


class AzureVisionProvider(MockOCRProvider):
    name = "azure-vision"


class AWSTextractProvider(MockOCRProvider):
    name = "aws-textract"


class PDFParserProvider(MockOCRProvider):
    name = "pdf-parser"


class ImageParserProvider(MockOCRProvider):
    name = "image-parser"


class OCRGateway:
    def __init__(self, provider: OCRProvider | None = None) -> None:
        self.provider = provider or PDFParserProvider()

    async def extract_text(self, document: bytes) -> str:
        return await self.provider.extract_text(document)

    async def extract_tables(self, document: bytes):
        return await self.provider.extract_tables(document)
