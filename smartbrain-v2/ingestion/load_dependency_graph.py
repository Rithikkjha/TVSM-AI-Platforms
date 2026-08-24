"""Load the service dependency graph JSON into Neo4j as DEPENDS_ON edges.

Reads kiro_steering/_dependencies/service_dependency_graph.json and creates:
- Service nodes (MERGE by name, so existing nodes are reused)
- DEPENDS_ON relationships between services
- Service Bus topic/subscription relationships
- Shared database relationships

Usage:
    python -m ingestion.load_dependency_graph                  # default path
    python -m ingestion.load_dependency_graph --json path.json # custom path
    python -m ingestion.load_dependency_graph --dry-run        # preview only

Requires: Neo4j running, .env with NEO4J_URI/USER/PASSWORD.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from config.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_JSON_PATH = Path("kiro_steering/_dependencies/service_dependency_graph.json")


async def load_graph(json_path: Path, dry_run: bool = False) -> dict[str, int]:
    """Load dependency graph into Neo4j.

    Returns a dict of counts: services_created, edges_created, topics_created.
    """
    from neo4j import AsyncGraphDatabase

    settings = get_settings()

    with open(json_path) as f:
        graph_data = json.load(f)

    services = graph_data.get("services", {})
    service_bus_topics = graph_data.get("service_bus_topics", {})
    shared_databases = graph_data.get("shared_databases", {})

    counts = {
        "services_merged": 0,
        "depends_on_edges": 0,
        "publishes_to_edges": 0,
        "subscribes_from_edges": 0,
        "shared_db_edges": 0,
        "delivers_to_edges": 0,
    }

    if dry_run:
        print("\n🔍 DRY RUN — no changes will be written to Neo4j\n")

    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        async with driver.session() as session:
            # --- Step 1: MERGE all Service nodes ---
            print(f"📦 Merging {len(services)} service nodes...")
            for svc_name, svc_data in services.items():
                tier = svc_data.get("tier", 0)
                description = svc_data.get("description", "")
                aliases = svc_data.get("aliases", [])

                if not dry_run:
                    await session.run(
                        """
                        MERGE (s:Service {name: $name})
                        SET s.tier = $tier,
                            s.description = $description,
                            s.aliases = $aliases,
                            s.source = 'dependency_graph',
                            s.updated_at = datetime()
                        """,
                        name=svc_name,
                        tier=tier,
                        description=description,
                        aliases=aliases,
                    )
                counts["services_merged"] += 1

            # --- Step 2: Create DEPENDS_ON edges ---
            print("🔗 Creating DEPENDS_ON edges...")
            for svc_name, svc_data in services.items():
                depends_on = svc_data.get("depends_on", [])
                for dep in depends_on:
                    if isinstance(dep, dict):
                        target = dep.get("service", "")
                        dep_type = dep.get("type", "unknown")
                        note = dep.get("note", "")
                    else:
                        target = dep
                        dep_type = "unknown"
                        note = ""

                    # Skip external services (Azure AD, etc.)
                    if target not in services and target not in [
                        s for svc in services.values() for s in svc.get("aliases", [])
                    ]:
                        continue

                    if not dry_run:
                        await session.run(
                            """
                            MATCH (a:Service {name: $from_svc})
                            MATCH (b:Service {name: $to_svc})
                            MERGE (a)-[r:DEPENDS_ON]->(b)
                            SET r.type = $dep_type,
                                r.note = $note,
                                r.source = 'dependency_graph'
                            """,
                            from_svc=svc_name,
                            to_svc=target,
                            dep_type=dep_type,
                            note=note,
                        )
                    counts["depends_on_edges"] += 1

            # --- Step 3: Create "depended_by" reverse edges ---
            for svc_name, svc_data in services.items():
                depended_by = svc_data.get("depended_by", [])
                for dependent in depended_by:
                    if dependent not in services:
                        continue
                    if not dry_run:
                        await session.run(
                            """
                            MATCH (a:Service {name: $from_svc})
                            MATCH (b:Service {name: $to_svc})
                            MERGE (a)-[r:DEPENDS_ON]->(b)
                            SET r.source = 'dependency_graph'
                            """,
                            from_svc=dependent,
                            to_svc=svc_name,
                        )
                    counts["depends_on_edges"] += 1

            # --- Step 4: Create delivers_webhooks_to edges ---
            for svc_name, svc_data in services.items():
                delivers_to = svc_data.get("delivers_webhooks_to", [])
                for target in delivers_to:
                    if target not in services:
                        continue
                    if not dry_run:
                        await session.run(
                            """
                            MATCH (a:Service {name: $from_svc})
                            MATCH (b:Service {name: $to_svc})
                            MERGE (a)-[r:DELIVERS_WEBHOOK_TO]->(b)
                            SET r.source = 'dependency_graph'
                            """,
                            from_svc=svc_name,
                            to_svc=target,
                        )
                    counts["delivers_to_edges"] += 1

            # --- Step 5: Service Bus topic relationships ---
            print("📨 Creating Service Bus topic relationships...")
            for topic_name, topic_data in service_bus_topics.items():
                publisher = topic_data.get("publisher", "")
                subscribers = topic_data.get("subscribers", [])

                # Create topic node
                if not dry_run:
                    await session.run(
                        """
                        MERGE (t:ServiceBusTopic {name: $name})
                        SET t.source = 'dependency_graph'
                        """,
                        name=topic_name,
                    )

                # Publisher → Topic
                if publisher in services and not dry_run:
                    await session.run(
                        """
                        MATCH (s:Service {name: $svc})
                        MATCH (t:ServiceBusTopic {name: $topic})
                        MERGE (s)-[r:PUBLISHES_TO]->(t)
                        SET r.source = 'dependency_graph'
                        """,
                        svc=publisher,
                        topic=topic_name,
                    )
                    counts["publishes_to_edges"] += 1

                # Topic → Subscribers
                for sub in subscribers:
                    if sub in services and not dry_run:
                        await session.run(
                            """
                            MATCH (t:ServiceBusTopic {name: $topic})
                            MATCH (s:Service {name: $svc})
                            MERGE (s)-[r:SUBSCRIBES_FROM]->(t)
                            SET r.source = 'dependency_graph'
                            """,
                            topic=topic_name,
                            svc=sub,
                        )
                        counts["subscribes_from_edges"] += 1

            # --- Step 6: Shared database relationships ---
            print("🗄️  Creating shared database relationships...")
            for db_name, db_data in shared_databases.items():
                db_type = db_data.get("type", "")
                db_services = db_data.get("services", [])

                if not dry_run:
                    await session.run(
                        """
                        MERGE (d:Database {name: $name})
                        SET d.type = $type, d.source = 'dependency_graph'
                        """,
                        name=db_name,
                        type=db_type,
                    )

                for svc in db_services:
                    # Handle service names that might have extra text
                    svc_clean = svc.split(" (")[0]  # strip "(all 4 microservices)" etc.
                    if svc_clean in services and not dry_run:
                        await session.run(
                            """
                            MATCH (s:Service {name: $svc})
                            MATCH (d:Database {name: $db})
                            MERGE (s)-[r:USES_DATABASE]->(d)
                            SET r.source = 'dependency_graph'
                            """,
                            svc=svc_clean,
                            db=db_name,
                        )
                        counts["shared_db_edges"] += 1

    finally:
        await driver.close()

    return counts


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Load service dependency graph JSON into Neo4j",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help=f"Path to dependency graph JSON (default: {DEFAULT_JSON_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview counts without writing to Neo4j",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.json.exists():
        print(f"❌ File not found: {args.json}")
        return

    print(f"\n📂 Loading dependency graph from: {args.json}")
    start_dt = datetime.now()
    start = time.time()

    counts = asyncio.run(load_graph(args.json, dry_run=args.dry_run))

    elapsed = time.time() - start
    end_dt = datetime.now()

    print("\n" + "=" * 60)
    print("Dependency Graph Load Results:")
    print("-" * 60)
    for key, value in counts.items():
        print(f"  {key}: {value}")
    print("-" * 60)
    print(f"⏱  Start time:  {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱  End time:    {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱  Total:       {elapsed:.1f}s")
    if args.dry_run:
        print("\n⚠️  DRY RUN — nothing was written to Neo4j")
    else:
        print("\n✅ Dependency graph loaded into Neo4j successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
