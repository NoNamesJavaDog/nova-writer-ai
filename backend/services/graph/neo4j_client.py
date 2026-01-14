"""Neo4j client wrapper."""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Optional

from neo4j import GraphDatabase, Driver

from core.config import NEO4J_ENABLED, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

logger = logging.getLogger(__name__)

_driver: Optional[Driver] = None


def get_driver() -> Optional[Driver]:
    global _driver
    if not NEO4J_ENABLED:
        return None
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def run_cypher(query: str, params: Optional[Dict[str, Any]] = None) -> Iterable[Dict[str, Any]]:
    driver = get_driver()
    if driver is None:
        return []
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
    except Exception as exc:
        logger.error("Neo4j query failed: %s", exc, exc_info=True)
        return []
