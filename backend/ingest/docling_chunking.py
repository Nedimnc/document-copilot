"""Docling HybridChunker wiring with readable table serialization for SEC filings."""

from __future__ import annotations

import re

from docling_core.transforms.serializer.base import (
    BaseDocSerializer,
    BaseSerializerProvider,
)
from docling_core.transforms.serializer.markdown import (
    MarkdownDocSerializer,
    MarkdownParams,
    MarkdownTableSerializer,
)
from docling_core.types.doc.base import ImageRefMode
from docling_core.types.doc.document import DoclingDocument

# Docling's default chunking path flattens tables as "row, column = value" triplets,
# which is hard for analysts to verify. Markdown pipe tables match export_to_markdown.
TRIPLET_ARTIFACT_RE = re.compile(
    r"(?:^|[.\s])(?:[^,\n]{1,80},\s*[^=\n]{1,80}\s*=\s*[^.\n]{0,40})",
    re.MULTILINE,
)


class MarkdownTableChunkingDocSerializer(MarkdownDocSerializer):
    table_serializer: MarkdownTableSerializer = MarkdownTableSerializer()
    params: MarkdownParams = MarkdownParams(
        image_mode=ImageRefMode.PLACEHOLDER,
        image_placeholder="",
        escape_underscores=False,
        escape_html=False,
    )


class MarkdownTableChunkingSerializerProvider(BaseSerializerProvider):
    def get_serializer(self, doc: DoclingDocument) -> BaseDocSerializer:
        return MarkdownTableChunkingDocSerializer(doc=doc)


def looks_like_triplet_table_serialization(text: str) -> bool:
    """True when text looks like Docling TripletTableSerializer output."""
    matches = TRIPLET_ARTIFACT_RE.findall(text)
    return len(matches) >= 3

