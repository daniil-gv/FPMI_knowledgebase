import json
import os
from urllib.parse import quote

import yaml

VAULT_DIR = "vault/fpmi"
BASE_URL = os.environ.get("BASE_URL", "/")

VALID_TYPES = {"area", "lab", "person"}


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def load_frontmatter(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return yaml.safe_load(parts[1]) or {}


def parse_wikilink(value):
    if value is None:
        return None
    s = str(value).strip().strip('"').strip("'").strip()
    if not s:
        return None

    if s.startswith("[[") and s.endswith("]]"):
        s = s[2:-2].strip()
    if "|" in s:
        s = s.split("|", 1)[0].strip()
    if "#" in s:
        s = s.split("#", 1)[0].strip()
    if "/" in s:
        s = s.rsplit("/", 1)[-1].strip()
    if s.endswith(".md"):
        s = s[:-3].strip()
    return s or None


def url_from_rel_md(rel_md_path):
    rel = rel_md_path.replace("\\", "/")
    if rel.endswith(".md"):
        rel = rel[:-3]

    encoded_rel = "/".join(quote(part) for part in rel.split("/"))
    base = BASE_URL if BASE_URL.endswith("/") else f"{BASE_URL}/"
    if not base.startswith("/"):
        base = f"/{base}"
    return f"{base}{encoded_rel}/"


entities = []
entities_by_type_name = {}
entities_by_type_name_lower = {}
entities_by_type_alias = {}
entities_by_type_alias_lower = {}

for root, dirs, files in os.walk(VAULT_DIR):
    dirs[:] = [d for d in dirs if not d.startswith(".") and not d.startswith("_")]
    for fn in files:
        if not fn.endswith(".md"):
            continue

        path = os.path.join(root, fn)
        fm = load_frontmatter(path)
        if not fm:
            continue

        entity_type = fm.get("type")
        if entity_type not in VALID_TYPES:
            continue

        name = os.path.splitext(fn)[0]
        label = fm.get("title") or name
        rel_path = os.path.relpath(path, VAULT_DIR)
        entity_id = f"{entity_type}:{name}"

        entity = {
            "id": entity_id,
            "type": entity_type,
            "name": name,
            "label": label,
            "url": url_from_rel_md(rel_path),
            "fm": fm,
        }
        entities.append(entity)
        entities_by_type_name[(entity_type, name)] = entity
        entities_by_type_name_lower[(entity_type, name.casefold())] = entity

        aliases = {name}
        if isinstance(label, str) and label.strip():
            aliases.add(label.strip())
        slug = fm.get("slug")
        if isinstance(slug, str) and slug.strip():
            aliases.add(slug.strip())

        for alias in aliases:
            entities_by_type_alias[(entity_type, alias)] = entity
            entities_by_type_alias_lower[(entity_type, alias.casefold())] = entity


def resolve_entity(entity_type, link_value):
    target_name = parse_wikilink(link_value)
    if not target_name:
        return None
    return (
        entities_by_type_name.get((entity_type, target_name))
        or entities_by_type_name_lower.get((entity_type, target_name.casefold()))
        or entities_by_type_alias.get((entity_type, target_name))
        or entities_by_type_alias_lower.get((entity_type, target_name.casefold()))
    )


nodes = [
    {
        "data": {
            "id": entity["id"],
            "label": entity["label"],
            "type": entity["type"],
            "url": entity["url"],
        }
    }
    for entity in entities
]

edges = []
edge_ids = set()
collab_pairs = set()
unresolved_links = 0


def add_edge(source, target, edge_type, weight=1):
    key = (source, target, edge_type)
    if key in edge_ids:
        return
    edge_ids.add(key)
    edges.append(
        {
            "data": {
                "id": f"e:{len(edges)}",
                "source": source,
                "target": target,
                "type": edge_type,
                "weight": weight,
            }
        }
    )


for entity in entities:
    fm = entity["fm"]
    source_id = entity["id"]
    source_type = entity["type"]

    if source_type == "lab":
        for area_ref in as_list(fm.get("area")):
            target = resolve_entity("area", area_ref)
            if not target:
                unresolved_links += 1
                continue
            add_edge(source_id, target["id"], "belongs_to")

    if source_type == "person":
        for lab_ref in as_list(fm.get("lab")):
            target = resolve_entity("lab", lab_ref)
            if not target:
                unresolved_links += 1
                continue
            add_edge(source_id, target["id"], "member_of")

    for collab_ref in as_list(fm.get("collaborates_with")):
        target = resolve_entity(source_type, collab_ref)
        if not target:
            unresolved_links += 1
            continue
        if target["id"] == source_id:
            continue

        pair = (source_type, min(source_id, target["id"]), max(source_id, target["id"]))
        if pair in collab_pairs:
            continue
        collab_pairs.add(pair)
        add_edge(source_id, target["id"], "collaboration")


os.makedirs("graph/data", exist_ok=True)
with open("graph/data/graph.json", "w", encoding="utf-8") as f:
    json.dump({"nodes": nodes, "edges": edges}, f, ensure_ascii=False, indent=2)

print(
    f"graph.json: nodes={len(nodes)} edges={len(edges)} unresolved_links={unresolved_links}"
)
