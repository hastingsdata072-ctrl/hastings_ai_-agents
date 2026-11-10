"""
Retrieval evaluation metrics for Hastings RAG Studio.

Implements precision@k, recall@k, and MRR (Mean Reciprocal Rank).
These measure retrieval quality against a labelled question set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievalMetrics:
    """Evaluation metrics for a single query."""
    query: str
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float
    k: int
    retrieved_ids: list[int]
    relevant_ids: list[int]


@dataclass
class AggregateMetrics:
    """Aggregated metrics across multiple queries."""
    mean_precision_at_k: float
    mean_recall_at_k: float
    mrr: float
    num_queries: int
    k: int


def precision_at_k(retrieved_ids: list[int], relevant_ids: list[int], k: int) -> float:
    """
    Fraction of the top-k retrieved results that are relevant.

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant chunk IDs for this query.
        k: Cutoff rank.

    Returns:
        Precision@k value between 0.0 and 1.0.
    """
    if k == 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    hits = sum(1 for cid in top_k if cid in relevant_set)
    return hits / k


def recall_at_k(retrieved_ids: list[int], relevant_ids: list[int], k: int) -> float:
    """
    Fraction of all relevant results that appear in the top-k.

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant chunk IDs for this query.
        k: Cutoff rank.

    Returns:
        Recall@k value between 0.0 and 1.0.
    """
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    hits = sum(1 for cid in top_k if cid in relevant_set)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids: list[int], relevant_ids: list[int]) -> float:
    """
    Reciprocal of the rank of the first relevant result.

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant chunk IDs for this query.

    Returns:
        1/rank of first hit, or 0.0 if no relevant result found.
    """
    relevant_set = set(relevant_ids)
    for rank, cid in enumerate(retrieved_ids, start=1):
        if cid in relevant_set:
            return 1.0 / rank
    return 0.0


def evaluate_query(
    query: str,
    retrieved_chunks: list[dict[str, Any]],
    relevant_chunk_ids: list[int],
    k: int,
) -> RetrievalMetrics:
    """
    Evaluate retrieval quality for a single query.

    Args:
        query: The question text.
        retrieved_chunks: Chunks returned by the retrieval system.
        relevant_chunk_ids: Ground-truth relevant chunk IDs.
        k: Evaluation cutoff.

    Returns:
        RetrievalMetrics for this query.
    """
    retrieved_ids = [c["id"] for c in retrieved_chunks]

    return RetrievalMetrics(
        query=query,
        precision_at_k=precision_at_k(retrieved_ids, relevant_chunk_ids, k),
        recall_at_k=recall_at_k(retrieved_ids, relevant_chunk_ids, k),
        reciprocal_rank=reciprocal_rank(retrieved_ids, relevant_chunk_ids),
        k=k,
        retrieved_ids=retrieved_ids,
        relevant_ids=relevant_chunk_ids,
    )


def aggregate_metrics(query_metrics: list[RetrievalMetrics]) -> AggregateMetrics:
    """
    Compute mean precision@k, mean recall@k, and MRR across queries.

    Args:
        query_metrics: List of per-query RetrievalMetrics.

    Returns:
        AggregateMetrics with mean values.
    """
    if not query_metrics:
        return AggregateMetrics(0.0, 0.0, 0.0, 0, 0)

    n = len(query_metrics)
    return AggregateMetrics(
        mean_precision_at_k=sum(m.precision_at_k for m in query_metrics) / n,
        mean_recall_at_k=sum(m.recall_at_k for m in query_metrics) / n,
        mrr=sum(m.reciprocal_rank for m in query_metrics) / n,
        num_queries=n,
        k=query_metrics[0].k,
    )
