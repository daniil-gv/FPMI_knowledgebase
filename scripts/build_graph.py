import os, json
import yaml

VAULT_DIR = "vault"
# Важно: baseurl для GitHub Pages репо-проекта: /REPO/
# Мы прокинем это в CI через env, чтобы не хардкодить.
BASE_URL = os.environ.get("BASE_URL", "/")

nodes = []
edges = []
entities = {}  # slug -> data

def load_frontmatter(path: str):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return yaml.safe_load(parts[1]) or {}

# 1) собрать сущности
for root, _, files in os.walk(VAULT_DIR):
    for fn in files:
        if not fn.endswith(".md"):
            continue
        path = os.path.join(root, fn)
        fm = load_frontmatter(path)
        if not fm:
            continue
        t = fm.get("type")
        slug = fm.get("slug")
        title = fm.get("title")
        if not t or not slug:
            continue

        entities[slug] = fm

        # URL страницы на сайте mkdocs обычно будет BASE_URL + slug + "/"
        # Но mkdocs по умолчанию строит URL из пути файла, а не slug.
        # Поэтому ниже мы сделаем ПРАВИЛЬНЫЕ url на основе ПУТИ, а slug оставим как id.
        rel_path = os.path.relpath(path, VAULT_DIR).replace("\\", "/")
        # mkdocs: Areas/Analysis.md -> areas/analysis/ (примерно)
        # Самый надёжный вариант: ссылаться на "путь без .md"
        page = rel_path[:-3]  # remove .md
        url = f"{BASE_URL}{page}/"

        nodes.append({
            "data": {
                "id": slug,
                "label": title or slug,
                "type": t,
                "url": url
            }
        })

# помощник: проверять что slug существует
def has(slug: str) -> bool:
    return slug in entities

# 2) связи
for slug, fm in entities.items():
    t = fm.get("type")

    if t == "lab":
        area = fm.get("area")
        if area and has(area):
            edges.append({"data": {"source": slug, "target": area, "type": "belongs_to", "weight": 1}})

        for collab in fm.get("collaborates_with", []) or []:
            if collab and has(collab):
                edges.append({"data": {"source": slug, "target": collab, "type": "collaboration", "weight": 1}})

    if t == "person":
        lab = fm.get("lab")
        if lab and has(lab):
            edges.append({"data": {"source": slug, "target": lab, "type": "member_of", "weight": 1}})

# 3) сохранить
os.makedirs("graph/data", exist_ok=True)
with open("graph/data/graph.json", "w", encoding="utf-8") as f:
    json.dump({"nodes": nodes, "edges": edges}, f, ensure_ascii=False, indent=2)

print(f"graph.json: nodes={len(nodes)} edges={len(edges)}")