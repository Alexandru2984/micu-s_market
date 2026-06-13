from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db import connection
from django.db.models import ExpressionWrapper, F, FloatField, Q
from django.db.models.functions import Greatest


def apply_listing_search(queryset, raw_query):
    query = (raw_query or "").strip()
    if not query:
        return queryset, False

    fallback_filter = (
        Q(title__icontains=query)
        | Q(description__icontains=query)
        | Q(city__icontains=query)
        | Q(county__icontains=query)
    )

    if connection.vendor != "postgresql":
        return queryset.filter(fallback_filter), True

    vector = (
        SearchVector("title", weight="A", config="simple")
        + SearchVector("category__name", weight="B", config="simple")
        + SearchVector("city", weight="B", config="simple")
        + SearchVector("county", weight="C", config="simple")
        + SearchVector("description", weight="D", config="simple")
    )
    search_query = SearchQuery(query, config="simple", search_type="websearch")
    similarity = Greatest(
        TrigramSimilarity("title", query),
        TrigramSimilarity("category__name", query),
        TrigramSimilarity("city", query),
        TrigramSimilarity("description", query),
    )

    queryset = queryset.annotate(
        search_rank=SearchRank(vector, search_query),
        search_similarity=similarity,
    ).annotate(
        search_score=ExpressionWrapper(
            F("search_rank") + F("search_similarity"),
            output_field=FloatField(),
        )
    )

    return (
        queryset.filter(
            Q(search_rank__gte=0.05)
            | Q(search_similarity__gte=0.12)
            | fallback_filter
        ),
        True,
    )


def order_search_results(queryset, sort_by, search_applied):
    if sort_by == "relevance" and search_applied:
        return queryset.order_by("-search_score", "-is_featured", "-created_at")
    return queryset
