"""Knowledge Retrieval Activity for Temporal workflows."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import activity

from src.knowledge.knowledge_base import KnowledgeBase
from src.models.knowledge_config import KnowledgeBaseConfig


@dataclass
class RetrieveInput:
    """Input for knowledge retrieval activity."""

    query: str
    collection_name: str
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 5
    similarity_threshold: Optional[float] = None


@dataclass
class RetrievedDocument:
    """A retrieved document with its score."""

    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrieveOutput:
    """Output from knowledge retrieval activity."""

    documents: List[RetrievedDocument]
    query: str
    total_found: int


@activity.defn
async def retrieve_knowledge(input: RetrieveInput) -> RetrieveOutput:
    """
    Retrieve relevant documents from knowledge base.

    This activity connects to vector store, embeds the query,
    and returns the most relevant documents.
    """
    activity.logger.info(
        f"Retrieving knowledge: collection={input.collection_name}, "
        f"top_k={input.top_k}"
    )

    # Build config
    config = KnowledgeBaseConfig(
        collection_name=input.collection_name,
        embedding_model=input.embedding_model,
        top_k=input.top_k,
        similarity_threshold=input.similarity_threshold,
    )

    # Initialize knowledge base
    kb = KnowledgeBase(config)

    try:
        await kb.initialize()

        # Search
        result = await kb.search(
            query=input.query,
            top_k=input.top_k,
            score_threshold=input.similarity_threshold,
        )

        documents = [
            RetrievedDocument(
                content=doc.content,
                score=doc.score,
                metadata=doc.metadata,
            )
            for doc in result.documents
        ]

        activity.logger.info(f"Retrieved {len(documents)} documents")

        return RetrieveOutput(
            documents=documents,
            query=input.query,
            total_found=len(documents),
        )

    finally:
        await kb.close()
