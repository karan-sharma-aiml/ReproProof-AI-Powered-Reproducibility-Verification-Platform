from __future__ import annotations

from app.embeddings.service import (
    BGEProvider,
    GeminiEmbeddingProvider,
    InstructorXLProvider,
    LocalEmbeddingProvider,
    OpenAIEmbeddingProvider,
    SentenceTransformersProvider,
)
from app.core.config import get_settings
from app.llm.service import AIGateway, NamedLLMProvider
from app.providers.gemini import GeminiLLMProvider
from app.ocr.service import (
    AWSTextractProvider,
    AzureVisionProvider,
    EasyOCRProvider,
    GoogleVisionProvider,
    ImageParserProvider,
    PDFParserProvider,
    TesseractProvider,
)
from app.providers.contracts import ProviderKind
from app.providers.manager import AIProviderManager
from app.providers.mock import MockLLMProvider
from app.vector.service import (
    ChromaDBProvider,
    FAISSProvider,
    MilvusProvider,
    PineconeProvider,
    QdrantProvider,
    WeaviateProvider,
)


def build_provider_manager() -> AIProviderManager:
    manager = AIProviderManager(default_provider=get_settings().DEFAULT_LLM_PROVIDER)
    manager.register(GeminiLLMProvider(), ProviderKind.LLM)
    for name, priority in (
        ("openai", 20),
        ("anthropic", 30),
        ("huggingface", 40),
        ("azure-openai", 50),
        ("ollama", 60),
    ):
        manager.register(
            NamedLLMProvider(name, configured=False, priority=priority),
            ProviderKind.LLM,
        )
    manager.register(MockLLMProvider(), ProviderKind.LLM)
    for provider in (
        OpenAIEmbeddingProvider(),
        GeminiEmbeddingProvider(),
        SentenceTransformersProvider(),
        InstructorXLProvider(),
        BGEProvider(),
        LocalEmbeddingProvider(),
    ):
        manager.register(provider, ProviderKind.EMBEDDING)
    for provider in (
        FAISSProvider(),
        ChromaDBProvider(),
        QdrantProvider(),
        PineconeProvider(),
        WeaviateProvider(),
        MilvusProvider(),
    ):
        manager.register(provider, ProviderKind.VECTOR)
    for provider in (
        TesseractProvider(),
        EasyOCRProvider(),
        GoogleVisionProvider(),
        AzureVisionProvider(),
        AWSTextractProvider(),
        PDFParserProvider(),
        ImageParserProvider(),
    ):
        manager.register(provider, ProviderKind.OCR)
    return manager


provider_manager = build_provider_manager()
ai_gateway = AIGateway(provider_manager, MockLLMProvider())
