from typing import Union

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings
from app.utils.logger import logger


class TextSplitterFactory:
    """Factory for creating text splitters."""

    def __init__(self, settings: Settings, embeddings_client: OpenAIEmbeddings) -> None:
        self._settings = settings
        self._embeddings = embeddings_client

    def create_splitter(
        self,
        method: str = "recursive",
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> Union[SemanticChunker, RecursiveCharacterTextSplitter]:
        """
        Create text splitter based on method.

        Args:
            method: "semantic" or "recursive"
            chunk_size: Chunk size for recursive splitter (uses default if None)
            chunk_overlap: Overlap for recursive splitter (uses default if None)

        Returns:
            (SemanticChunker or RecursiveCharacterTextSplitter)

        Raises:
            ValueError: If method is invalid
        """
        if method == "semantic":
            logger.info("Creating semantic chunker with gradient breakpoint")
            return SemanticChunker(
                embeddings=self._embeddings,
                breakpoint_threshold_type="gradient",
            )

        elif method == "recursive":
            # Use provided values or defaults from settings
            chunk_size = chunk_size or self._settings.default_chunk_size
            chunk_overlap = chunk_overlap or self._settings.default_chunk_overlap

            logger.info(f"Creating recursive splitter: size={chunk_size}, overlap={chunk_overlap}")
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

        else:
            raise ValueError(f"Invalid splitting method: {method}. Use 'semantic' or 'recursive'")
