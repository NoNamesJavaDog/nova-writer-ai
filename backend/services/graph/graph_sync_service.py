"""Graph sync service for Neo4j."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from sqlalchemy.orm import selectinload

from core.config import NEO4J_ENABLED
from core.database import SessionLocal
from models import (
    Novel,
    Volume,
    Chapter,
    Character,
    WorldSetting,
    TimelineEvent,
    Foreshadowing,
)
from services.graph.neo4j_client import run_cypher
from core.security import generate_uuid

logger = logging.getLogger(__name__)


def _build_lists(novel: Novel) -> Dict[str, List[Dict[str, Any]]]:
    volumes = [
        {
            "id": v.id,
            "novel_id": v.novel_id,
            "title": v.title,
            "summary": v.summary or "",
            "outline": v.outline or "",
            "volume_order": v.volume_order,
            "created_at": v.created_at,
            "updated_at": v.updated_at,
        }
        for v in novel.volumes
    ]
    chapters = [
        {
            "id": ch.id,
            "volume_id": ch.volume_id,
            "title": ch.title,
            "summary": ch.summary or "",
            "chapter_order": ch.chapter_order,
            "created_at": ch.created_at,
            "updated_at": ch.updated_at,
        }
        for v in novel.volumes
        for ch in v.chapters
    ]
    characters = [
        {
            "id": c.id,
            "novel_id": c.novel_id,
            "name": c.name,
            "age": c.age or "",
            "role": c.role or "",
            "personality": c.personality or "",
            "background": c.background or "",
            "goals": c.goals or "",
            "character_order": c.character_order,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in novel.characters
    ]
    world_settings = [
        {
            "id": w.id,
            "novel_id": w.novel_id,
            "title": w.title,
            "description": w.description or "",
            "category": w.category or "",
            "setting_order": w.setting_order,
            "created_at": w.created_at,
            "updated_at": w.updated_at,
        }
        for w in novel.world_settings
    ]
    timeline_events = [
        {
            "id": t.id,
            "novel_id": t.novel_id,
            "time": t.time,
            "event": t.event,
            "impact": t.impact or "",
            "event_order": t.event_order,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in novel.timeline_events
    ]
    foreshadowings = [
        {
            "id": f.id,
            "novel_id": f.novel_id,
            "content": f.content,
            "chapter_id": f.chapter_id,
            "resolved_chapter_id": f.resolved_chapter_id,
            "is_resolved": f.is_resolved,
            "foreshadowing_order": f.foreshadowing_order,
            "created_at": f.created_at,
            "updated_at": f.updated_at,
        }
        for f in novel.foreshadowings
    ]
    return {
        "volumes": volumes,
        "chapters": chapters,
        "characters": characters,
        "world_settings": world_settings,
        "timeline_events": timeline_events,
        "foreshadowings": foreshadowings,
    }


def _sync_novel_graph(novel: Novel) -> None:
    lists = _build_lists(novel)
    timeline_ids = [t["id"] for t in sorted(lists["timeline_events"], key=lambda x: x["event_order"])]

    params = {
        "novel": {
            "id": novel.id,
            "title": novel.title,
            "genre": novel.genre,
            "synopsis": novel.synopsis or "",
            "full_outline": novel.full_outline or "",
            "created_at": novel.created_at,
            "updated_at": novel.updated_at,
        },
        "volumes": lists["volumes"],
        "chapters": lists["chapters"],
        "characters": lists["characters"],
        "world_settings": lists["world_settings"],
        "timeline_events": lists["timeline_events"],
        "foreshadowings": lists["foreshadowings"],
        "timeline_ids": timeline_ids,
    }

    run_cypher(
        """
        MATCH (n:Novel {id: $novel.id})
        DETACH DELETE n
        """,
        {"novel": {"id": novel.id}},
    )

    run_cypher(
        """
        CREATE (n:Novel {
            id: $novel.id,
            title: $novel.title,
            genre: $novel.genre,
            synopsis: $novel.synopsis,
            full_outline: $novel.full_outline,
            created_at: $novel.created_at,
            updated_at: $novel.updated_at
        })
        WITH n
        UNWIND $volumes AS v
        MERGE (vol:Volume {id: v.id})
        SET vol += v
        MERGE (n)-[:HAS_VOLUME]->(vol)
        """,
        params,
    )

    run_cypher(
        """
        UNWIND $chapters AS c
        MATCH (vol:Volume {id: c.volume_id})
        MERGE (ch:Chapter {id: c.id})
        SET ch += c
        MERGE (vol)-[:HAS_CHAPTER]->(ch)
        """,
        params,
    )

    run_cypher(
        """
        MATCH (n:Novel {id: $novel.id})
        UNWIND $characters AS c
        MERGE (ch:Character {id: c.id})
        SET ch += c
        MERGE (n)-[:HAS_CHARACTER]->(ch)
        """,
        params,
    )

    run_cypher(
        """
        MATCH (n:Novel {id: $novel.id})
        UNWIND $world_settings AS w
        MERGE (ws:WorldSetting {id: w.id})
        SET ws += w
        MERGE (n)-[:HAS_WORLD_SETTING]->(ws)
        """,
        params,
    )

    run_cypher(
        """
        MATCH (n:Novel {id: $novel.id})
        UNWIND $timeline_events AS t
        MERGE (e:TimelineEvent {id: t.id})
        SET e += t
        MERGE (n)-[:HAS_TIMELINE_EVENT]->(e)
        """,
        params,
    )

    run_cypher(
        """
        MATCH (n:Novel {id: $novel.id})
        UNWIND $foreshadowings AS f
        MERGE (fs:Foreshadowing {id: f.id})
        SET fs += f
        MERGE (n)-[:HAS_FORESHADOWING]->(fs)
        """,
        params,
    )

    run_cypher(
        """
        UNWIND $foreshadowings AS f
        MATCH (fs:Foreshadowing {id: f.id})
        OPTIONAL MATCH (intro:Chapter {id: f.chapter_id})
        OPTIONAL MATCH (resolved:Chapter {id: f.resolved_chapter_id})
        FOREACH (_ IN CASE WHEN intro IS NULL THEN [] ELSE [1] END |
            MERGE (fs)-[:INTRODUCED_IN]->(intro)
        )
        FOREACH (_ IN CASE WHEN resolved IS NULL THEN [] ELSE [1] END |
            MERGE (fs)-[:RESOLVED_IN]->(resolved)
        )
        """,
        params,
    )

    if len(timeline_ids) > 1:
        run_cypher(
            """
            UNWIND range(0, size($timeline_ids) - 2) AS idx
            MATCH (a:TimelineEvent {id: $timeline_ids[idx]})
            MATCH (b:TimelineEvent {id: $timeline_ids[idx + 1]})
            MERGE (a)-[:NEXT_EVENT]->(b)
            """,
            params,
        )


def sync_novel_graph(novel_id: str) -> None:
    if not NEO4J_ENABLED:
        return
    db = SessionLocal()
    try:
        novel = (
            db.query(Novel)
            .options(
                selectinload(Novel.volumes).selectinload(Volume.chapters),
                selectinload(Novel.characters),
                selectinload(Novel.world_settings),
                selectinload(Novel.timeline_events),
                selectinload(Novel.foreshadowings),
            )
            .filter(Novel.id == novel_id)
            .first()
        )
        if not novel:
            delete_novel_graph(novel_id)
            return
        _sync_novel_graph(novel)
    except Exception as exc:
        logger.error("Graph sync failed: %s", exc, exc_info=True)
    finally:
        db.close()


def delete_novel_graph(novel_id: str) -> None:
    if not NEO4J_ENABLED:
        return
    run_cypher(
        """
        MATCH (n:Novel {id: $novel_id})
        DETACH DELETE n
        """,
        {"novel_id": novel_id},
    )


def upsert_character_relations(
    novel_id: str,
    relations: List[Dict[str, Any]],
    name_to_id: Dict[str, str],
) -> int:
    if not NEO4J_ENABLED:
        return 0
    now = int(time.time() * 1000)
    payload = []
    for rel in relations or []:
        source_name = (rel.get("source_name") or rel.get("source") or "").strip()
        target_name = (rel.get("target_name") or rel.get("target") or "").strip()
        relation_type = (rel.get("relation_type") or rel.get("type") or "").strip()
        description = (rel.get("description") or "").strip()
        weight = rel.get("weight")
        stage = rel.get("stage")
        if not source_name or not target_name or not relation_type:
            continue
        source_id = name_to_id.get(source_name)
        target_id = name_to_id.get(target_name)
        if not source_id or not target_id or source_id == target_id:
            continue
        payload.append(
            {
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": relation_type,
                "description": description,
                "weight": weight,
                "stage": stage,
                "relation_id": generate_uuid(),
                "now": now,
            }
        )
    if not payload:
        return 0

    rows = run_cypher(
        """
        MATCH (n:Novel {id: $novel_id})
        UNWIND $relations AS rel
        MATCH (n)-[:HAS_CHARACTER]->(a:Character {id: rel.source_id})
        MATCH (n)-[:HAS_CHARACTER]->(b:Character {id: rel.target_id})
        MERGE (a)-[r:RELATES_TO {type: rel.relation_type}]->(b)
        ON CREATE SET r.id = rel.relation_id,
                      r.description = rel.description,
                      r.weight = rel.weight,
                      r.stage = rel.stage,
                      r.created_at = rel.now,
                      r.updated_at = rel.now
        ON MATCH SET r.description = rel.description,
                     r.weight = COALESCE(rel.weight, r.weight),
                     r.stage = COALESCE(rel.stage, r.stage),
                     r.updated_at = rel.now
        RETURN count(r) AS count
        """,
        {"novel_id": novel_id, "relations": payload},
    )
    if not rows:
        return 0
    return int(rows[0].get("count", 0))
