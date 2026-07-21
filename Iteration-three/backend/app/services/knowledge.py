"""Knowledge service for cross-session knowledge sharing.

Provides CRUD operations for knowledge facts, timeline events, character
relationships, foreshadowing tracking, and a delta log for pending changes.
Includes semantic search using sentence-transformers embeddings and
conflict detection for maintaining consistency.
"""

from __future__ import annotations

import asyncio
import logging
import struct
import uuid
from typing import Any

import aiosqlite

logger = logging.getLogger("knowledge")


class KnowledgeService:
    """Service for managing project knowledge.

    Manages five knowledge domains:
    - Facts: structured entity attributes (e.g. "Li Xiaoyao's cultivation level")
    - Events: timeline events ordered by chapter
    - Relationships: character-to-character connections
    - Foreshadowing: plot devices that need future resolution
    - Delta Log: pending changes awaiting user confirmation

    Embeddings are computed using a lazy-loaded ``all-MiniLM-L6-v2`` model
    and stored as float32 binary blobs.

    Args:
        db: An aiosqlite connection for metadata queries.
    """

    _model: Any = None  # Lazy-loaded SentenceTransformer via thread pool
    _model_lock: asyncio.Lock | None = None

    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db
        if KnowledgeService._model_lock is None:
            KnowledgeService._model_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Facts
    # ------------------------------------------------------------------

    async def store_fact(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str | None,
        fact_key: str,
        fact_value: str,
        summary: str,
        source_session_id: str | None = None,
        compute_embedding: bool = False,
    ) -> str:
        """Store a structured fact.

        Args:
            project_id: Owning project.
            entity_type: Type of entity (e.g. ``"character"``, ``"world"``).
            entity_id: Unique identifier of the entity.
            fact_key: Attribute name (e.g. ``"cultivation_level"``).
            fact_value: Attribute value as a string.
            summary: Human-readable description of this fact.
            source_session_id: Chat session that produced this fact.
            compute_embedding: If True, compute and store a text embedding.

        Returns:
            The generated fact ID.
        """
        fact_id = str(uuid.uuid4())
        embedding: bytes | None = None
        if compute_embedding:
            embedding = await self._compute_embedding(f"{summary} {fact_value}")
        await self.db.execute(
            """
            INSERT INTO knowledge_facts
                (id, project_id, entity_type, entity_id, fact_key, fact_value,
                 summary, embedding, source_session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (fact_id, project_id, entity_type, entity_id, fact_key, fact_value, summary, embedding, source_session_id),
        )
        await self.db.commit()
        return fact_id

    async def get_facts(
        self,
        project_id: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve facts for a project, optionally filtered by entity.

        Args:
            project_id: Owning project.
            entity_type: Optional entity type filter.
            entity_id: Optional entity ID filter.

        Returns:
            List of fact dictionaries.
        """
        if entity_type and entity_id:
            cursor = await self.db.execute(
                """
                SELECT * FROM knowledge_facts
                WHERE project_id = ? AND entity_type = ? AND entity_id = ?
                ORDER BY created_at DESC
                """,
                (project_id, entity_type, entity_id),
            )
        elif entity_type:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_facts WHERE project_id = ? AND entity_type = ? ORDER BY created_at DESC",
                (project_id, entity_type),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_facts WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Events (Timeline)
    # ------------------------------------------------------------------

    async def store_event(
        self,
        project_id: str,
        title: str,
        description: str,
        chapter_number: int | None = None,
        sequence: int = 0,
        event_type: str = "plot",
        involved_entities: str | None = None,
        source_session_id: str | None = None,
        compute_embedding: bool = False,
    ) -> str:
        """Store a timeline event.

        Args:
            project_id: Owning project.
            title: Event title.
            description: Event description.
            chapter_number: Chapter this event occurs in.
            sequence: Order within the chapter.
            event_type: Category (e.g. ``"plot"``, ``"death"``).
            involved_entities: Comma-separated entity IDs or JSON array.
            source_session_id: Chat session that produced this event.
            compute_embedding: If True, compute and store a text embedding.

        Returns:
            The generated event ID.
        """
        event_id = str(uuid.uuid4())
        embedding: bytes | None = None
        if compute_embedding:
            embedding = await self._compute_embedding(f"{title} {description}")
        await self.db.execute(
            """
            INSERT INTO knowledge_events
                (id, project_id, title, description, chapter_number, sequence,
                 event_type, involved_entities, embedding, source_session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                project_id,
                title,
                description,
                chapter_number,
                sequence,
                event_type,
                involved_entities,
                embedding,
                source_session_id,
            ),
        )
        await self.db.commit()
        return event_id

    async def get_timeline(
        self,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Retrieve timeline events ordered by chapter then sequence.

        Args:
            project_id: Owning project.
            limit: Maximum number of events to return.
            offset: Number of events to skip.

        Returns:
            List of event dictionaries.
        """
        cursor = await self.db.execute(
            """
            SELECT * FROM knowledge_events
            WHERE project_id = ?
            ORDER BY chapter_number ASC, sequence ASC
            LIMIT ? OFFSET ?
            """,
            (project_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    async def store_relationship(
        self,
        project_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        description: str | None = None,
        strength: int = 5,
        source_session_id: str | None = None,
    ) -> str:
        """Store a character relationship.

        Args:
            project_id: Owning project.
            source_entity_id: First entity in the relationship.
            target_entity_id: Second entity in the relationship.
            relationship_type: Type (e.g. ``"master"``, ``"friend"``).
            description: Optional description.
            strength: Relationship strength (1-10).
            source_session_id: Chat session that produced this relationship.

        Returns:
            The generated relationship ID.
        """
        rel_id = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO knowledge_relationships
                (id, project_id, source_entity_id, target_entity_id,
                 relationship_type, description, strength, source_session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rel_id,
                project_id,
                source_entity_id,
                target_entity_id,
                relationship_type,
                description,
                strength,
                source_session_id,
            ),
        )
        await self.db.commit()
        return rel_id

    async def get_relationships(
        self,
        project_id: str,
        entity_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relationships, optionally filtered by entity.

        Args:
            project_id: Owning project.
            entity_id: Optional entity ID to filter by (matches source or target).

        Returns:
            List of relationship dictionaries.
        """
        if entity_id:
            cursor = await self.db.execute(
                """
                SELECT * FROM knowledge_relationships
                WHERE project_id = ? AND (source_entity_id = ? OR target_entity_id = ?)
                ORDER BY created_at DESC
                """,
                (project_id, entity_id, entity_id),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_relationships WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Foreshadowing
    # ------------------------------------------------------------------

    async def store_foreshadowing(
        self,
        project_id: str,
        description: str,
        expected_resolve_chapter: int | None = None,
        related_chapter_id: str | None = None,
        priority: str = "normal",
        source_session_id: str | None = None,
        compute_embedding: bool = False,
    ) -> str:
        """Store a foreshadowing entry.

        Args:
            project_id: Owning project.
            description: What the foreshadowing sets up.
            expected_resolve_chapter: Expected chapter of resolution.
            related_chapter_id: Chapter where this foreshadowing was planted.
            priority: Priority level (e.g. ``"normal"``, ``"high"``).
            source_session_id: Chat session that produced this entry.
            compute_embedding: If True, compute and store a text embedding.

        Returns:
            The generated foreshadowing ID.
        """
        fid = str(uuid.uuid4())
        embedding: bytes | None = None
        if compute_embedding:
            embedding = await self._compute_embedding(description)
        await self.db.execute(
            """
            INSERT INTO knowledge_foreshadowing
                (id, project_id, description, expected_resolve_chapter,
                 priority, related_chapter_id, embedding, source_session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fid,
                project_id,
                description,
                expected_resolve_chapter,
                priority,
                related_chapter_id,
                embedding,
                source_session_id,
            ),
        )
        await self.db.commit()
        return fid

    async def get_foreshadowing(
        self,
        project_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve foreshadowing entries, optionally filtered by status.

        Args:
            project_id: Owning project.
            status: Optional status filter (e.g. ``"pending"``, ``"resolved"``).

        Returns:
            List of foreshadowing dictionaries.
        """
        if status:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_foreshadowing WHERE project_id = ? AND status = ? ORDER BY created_at DESC",
                (project_id, status),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_foreshadowing WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def resolve_foreshadowing(
        self,
        foreshadowing_id: str,
        actual_resolve_chapter: int | None = None,
        resolved_by_chapter_id: str | None = None,
    ) -> bool:
        """Mark a foreshadowing entry as resolved.

        Args:
            foreshadowing_id: ID of the foreshadowing entry.
            actual_resolve_chapter: Chapter where it was resolved.
            resolved_by_chapter_id: ID of the resolving chapter.

        Returns:
            True if the entry was found and updated.
        """
        cursor = await self.db.execute(
            """
            UPDATE knowledge_foreshadowing
            SET status = 'resolved',
                actual_resolve_chapter = ?,
                resolved_by_chapter_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (actual_resolve_chapter, resolved_by_chapter_id, foreshadowing_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Delta Log
    # ------------------------------------------------------------------

    async def create_delta(
        self,
        project_id: str,
        session_id: str,
        operation: str,
        target_table: str,
        summary: str,
        record_id: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> str:
        """Create a pending delta entry.

        Args:
            project_id: Owning project.
            session_id: Chat session that produced this delta.
            operation: ``"create"``, ``"update"``, or ``"delete"``.
            target_table: Target table name.
            summary: Human-readable summary of the change.
            record_id: ID of the target record. Auto-generated if not provided.
            old_value: Previous value (for update/delete).
            new_value: New value (for create/update).

        Returns:
            The generated delta ID.
        """
        delta_id = str(uuid.uuid4())
        if record_id is None:
            record_id = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO knowledge_delta_log
                (id, project_id, session_id, operation, target_table,
                 record_id, summary, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (delta_id, project_id, session_id, operation, target_table, record_id, summary, old_value, new_value),
        )
        await self.db.commit()
        return delta_id

    async def get_pending_deltas(
        self,
        project_id: str,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve pending deltas, optionally filtered by session.

        Args:
            project_id: Owning project.
            session_id: Optional session ID filter.

        Returns:
            List of pending delta dictionaries.
        """
        if session_id:
            cursor = await self.db.execute(
                """
                SELECT * FROM knowledge_delta_log
                WHERE project_id = ? AND session_id = ? AND status = 'pending'
                ORDER BY created_at ASC
                """,
                (project_id, session_id),
            )
        else:
            cursor = await self.db.execute(
                """
                SELECT * FROM knowledge_delta_log
                WHERE project_id = ? AND status = 'pending'
                ORDER BY created_at ASC
                """,
                (project_id,),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def confirm_delta(self, delta_id: str) -> bool:
        """Confirm a pending delta and activate the target record.

        For ``create`` operations, the target record's ``is_active`` or
        ``is_confirmed`` flag is set to 1.

        Args:
            delta_id: ID of the delta entry.

        Returns:
            True if the delta was found and updated.
        """
        cursor = await self.db.execute(
            "SELECT * FROM knowledge_delta_log WHERE id = ?",
            (delta_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return False

        await self.db.execute(
            "UPDATE knowledge_delta_log SET status = 'confirmed' WHERE id = ?",
            (delta_id,),
        )

        # Activate the target record for create operations
        if row["operation"] == "create":
            target_table = row["target_table"]
            record_id = row["record_id"]
            if target_table == "knowledge_facts":
                await self.db.execute(
                    "UPDATE knowledge_facts SET is_active = 1 WHERE id = ?",
                    (record_id,),
                )
            elif target_table == "knowledge_events":
                await self.db.execute(
                    "UPDATE knowledge_events SET is_confirmed = 1 WHERE id = ?",
                    (record_id,),
                )

        await self.db.commit()
        return True

    async def reject_delta(self, delta_id: str) -> bool:
        """Reject a pending delta and clean up the target record.

        For ``create`` operations that have not been confirmed yet,
        the target record is deleted.

        Args:
            delta_id: ID of the delta entry.

        Returns:
            True if the delta was found and updated.
        """
        cursor = await self.db.execute(
            "SELECT * FROM knowledge_delta_log WHERE id = ?",
            (delta_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return False

        await self.db.execute(
            "UPDATE knowledge_delta_log SET status = 'rejected' WHERE id = ?",
            (delta_id,),
        )

        # Delete unconfirmed target records for create operations
        if row["operation"] == "create":
            target_table = row["target_table"]
            record_id = row["record_id"]
            if target_table == "knowledge_facts":
                cur2 = await self.db.execute(
                    "SELECT is_active FROM knowledge_facts WHERE id = ?",
                    (record_id,),
                )
                target_row = await cur2.fetchone()
                if target_row is not None and target_row["is_active"] == 0:
                    await self.db.execute(
                        "DELETE FROM knowledge_facts WHERE id = ?",
                        (record_id,),
                    )
            elif target_table == "knowledge_events":
                cur2 = await self.db.execute(
                    "SELECT is_confirmed FROM knowledge_events WHERE id = ?",
                    (record_id,),
                )
                target_row = await cur2.fetchone()
                if target_row is not None and target_row["is_confirmed"] == 0:
                    await self.db.execute(
                        "DELETE FROM knowledge_events WHERE id = ?",
                        (record_id,),
                    )

        await self.db.commit()
        return True

    async def batch_confirm(
        self,
        session_id: str | None = None,
        project_id: str | None = None,
    ) -> int:
        """Confirm all pending deltas for a project and/or session.

        Args:
            session_id: Optional session ID filter.
            project_id: Optional project ID filter.

        Returns:
            Number of deltas confirmed.

        Raises:
            ValueError: If neither session_id nor project_id is provided.
        """
        if not project_id and not session_id:
            raise ValueError("At least one of session_id or project_id is required")

        if project_id and session_id:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_delta_log WHERE project_id = ? AND session_id = ? AND status = 'pending'",
                (project_id, session_id),
            )
        elif session_id:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_delta_log WHERE session_id = ? AND status = 'pending'",
                (session_id,),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_delta_log WHERE project_id = ? AND status = 'pending'",
                (project_id),
            )

        rows = await cursor.fetchall()
        if not rows:
            return 0

        count = 0
        for row in rows:
            # Update delta status
            await self.db.execute(
                "UPDATE knowledge_delta_log SET status = 'confirmed' WHERE id = ?",
                (row["id"],),
            )
            # Activate target record for create operations
            if row["operation"] == "create":
                target_table = row["target_table"]
                record_id = row["record_id"]
                if target_table == "knowledge_facts":
                    await self.db.execute(
                        "UPDATE knowledge_facts SET is_active = 1 WHERE id = ?",
                        (record_id,),
                    )
                elif target_table == "knowledge_events":
                    await self.db.execute(
                        "UPDATE knowledge_events SET is_confirmed = 1 WHERE id = ?",
                        (record_id,),
                    )
            count += 1

        if count > 0:
            await self.db.commit()
        return count

    # ------------------------------------------------------------------
    # Semantic Search
    # ------------------------------------------------------------------

    async def semantic_search(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search facts semantically by embedding similarity.

        Computes an embedding for the query and returns the ``top_k``
        facts with the highest cosine similarity.

        Args:
            project_id: Owning project.
            query: Natural-language search query.
            top_k: Number of results to return.

        Returns:
            List of fact dictionaries ordered by relevance.
        """
        query_embedding = await self._compute_embedding(query)
        if query_embedding is None:
            return []

        query_vec = self._deserialize_embedding(query_embedding)

        cursor = await self.db.execute(
            "SELECT * FROM knowledge_facts WHERE project_id = ? AND embedding IS NOT NULL",
            (project_id,),
        )
        rows = await cursor.fetchall()

        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            row_dict = dict(row)
            blob = row_dict.get("embedding")
            if blob is not None:
                vec = self._deserialize_embedding(blob)
                sim = self._cosine_similarity(query_vec, vec)
                scored.append((sim, row_dict))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    # ------------------------------------------------------------------
    # Knowledge Summary
    # ------------------------------------------------------------------

    async def get_knowledge_summary(self, project_id: str) -> dict[str, Any]:
        """Return a structured summary of all knowledge types.

        Includes recent events, key active facts, active relationships,
        and pending foreshadowing.

        Args:
            project_id: Owning project.

        Returns:
            Dictionary with keys ``recent_events``, ``key_facts``,
            ``active_relationships``, and ``pending_foreshadowing``.
        """
        # Recent events (last 10)
        cursor = await self.db.execute(
            """
            SELECT id, title, description, chapter_number
            FROM knowledge_events
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (project_id,),
        )
        recent_events = [dict(r) for r in await cursor.fetchall()]

        # Key active facts (last 20)
        cursor = await self.db.execute(
            """
            SELECT id, entity_type, entity_id, fact_key, summary
            FROM knowledge_facts
            WHERE project_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (project_id,),
        )
        key_facts = [dict(r) for r in await cursor.fetchall()]

        # Active relationships (last 20)
        cursor = await self.db.execute(
            """
            SELECT id, source_entity_id, target_entity_id, relationship_type, description
            FROM knowledge_relationships
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (project_id,),
        )
        active_relationships = [dict(r) for r in await cursor.fetchall()]

        # Pending foreshadowing (last 20)
        cursor = await self.db.execute(
            """
            SELECT id, description, expected_resolve_chapter, priority
            FROM knowledge_foreshadowing
            WHERE project_id = ? AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (project_id,),
        )
        pending_foreshadowing = [dict(r) for r in await cursor.fetchall()]

        return {
            "recent_events": recent_events,
            "key_facts": key_facts,
            "active_relationships": active_relationships,
            "pending_foreshadowing": pending_foreshadowing,
        }

    # ------------------------------------------------------------------
    # Conflict Detection
    # ------------------------------------------------------------------

    async def detect_conflicts(
        self,
        project_id: str,
        extracted_facts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Detect conflicts between extracted facts and existing knowledge.

        Checks for:
        - Fact key + entity ID collisions (same key, different value).
        - Timeline death_status contradictions (alive character had a death event).

        Args:
            project_id: Owning project.
            extracted_facts: List of fact dictionaries extracted by the LLM.

        Returns:
            List of conflict dictionaries with ``type`` and context fields.
        """
        conflicts: list[dict[str, Any]] = []

        for fact in extracted_facts:
            entity_id = fact.get("entity_id")
            fact_key = fact.get("fact_key")
            fact_value = fact.get("fact_value")

            # Check for fact_key + entity_id collision
            if entity_id and fact_key:
                cursor = await self.db.execute(
                    """
                    SELECT fact_value, summary FROM knowledge_facts
                    WHERE project_id = ? AND entity_id = ? AND fact_key = ? AND is_active = 1
                    """,
                    (project_id, entity_id, fact_key),
                )
                existing = await cursor.fetchone()
                if existing is not None and existing["fact_value"] != fact_value:
                    conflicts.append(
                        {
                            "type": "fact_collision",
                            "entity_id": entity_id,
                            "fact_key": fact_key,
                            "existing_value": existing["fact_value"],
                            "new_value": fact_value,
                            "existing_summary": existing["summary"],
                        }
                    )

            # Check for death_status contradictions
            if fact_key == "death_status" and entity_id:
                cursor = await self.db.execute(
                    """
                    SELECT id, title, description FROM knowledge_events
                    WHERE project_id = ? AND event_type = 'death'
                    AND involved_entities LIKE ?
                    """,
                    (project_id, f"%{entity_id}%"),
                )
                death_events = await cursor.fetchall()
                for event in death_events:
                    conflicts.append(
                        {
                            "type": "death_status_contradiction",
                            "entity_id": entity_id,
                            "existing_event": event["title"],
                            "existing_description": event["description"],
                        }
                    )

        return conflicts

    # ------------------------------------------------------------------
    # Embedding Helpers
    # ------------------------------------------------------------------

    @classmethod
    async def _get_model(cls) -> Any:
        """Lazy-load the sentence-transformers model via thread pool (singleton)."""
        if cls._model is None:
            async with cls._model_lock:  # type: ignore[union-attr]
                if cls._model is None:  # Double-check after acquiring lock
                    from sentence_transformers import SentenceTransformer

                    cls._model = await asyncio.to_thread(SentenceTransformer, "all-MiniLM-L6-v2")
        return cls._model

    async def _compute_embedding(self, text: str) -> bytes | None:
        """Compute and serialize an embedding vector via thread pool.

        Args:
            text: Input text to embed.

        Returns:
            Serialized float32 bytes, or None on failure.
        """
        try:
            model = await self._get_model()
            vec = await asyncio.to_thread(model.encode, text, normalize_embeddings=True)
            return self._serialize_embedding(vec)
        except Exception:
            logger.exception("Embedding computation failed for text: %.50s", text)
            return None

    def _serialize_embedding(self, vec: Any) -> bytes:
        """Serialize a float vector to bytes using struct.pack.

        Args:
            vec: A sequence of floats (list or numpy array).

        Returns:
            Float32 binary blob.
        """
        return struct.pack(f"{len(vec)}f", *vec)

    def _deserialize_embedding(self, blob: bytes) -> list[float]:
        """Deserialize bytes back to a list of floats.

        Args:
            blob: Float32 binary blob.

        Returns:
            List of floats.
        """
        return list(struct.unpack(f"{len(blob) // 4}f", blob))

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two normalized vectors.

        Assumes both vectors are L2-normalized, so this is just the dot product.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Cosine similarity in [0, 1].
        """
        return sum(x * y for x, y in zip(a, b))
