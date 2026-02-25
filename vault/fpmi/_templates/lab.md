<%*
const title = await tp.system.prompt("Название лаборатории?");
if (!title) return;

await tp.file.rename(title);

// -------- helpers --------
const mdFiles = () => app.vault.getMarkdownFiles();
const fm = (file) => app.metadataCache.getFileCache(file)?.frontmatter;
const byType = (t) => mdFiles().filter(f => fm(f)?.type === t);
const uniq = (arr) => [...new Set(arr)].filter(Boolean);

const asArray = (v) => Array.isArray(v) ? v : (v ? [v] : []);
const hasText = (arr, text) => asArray(arr).some(x => String(x).trim() === String(text).trim());

async function pickOne(options, placeholder="Выбери") {
  options = uniq(options).sort((a,b)=>a.localeCompare(b,'ru'));
  if (!options.length) return "";
  return await tp.system.suggester(options, options, false, placeholder) || "";
}
async function pickMany(options, placeholder="Выбери (ESC чтобы закончить)") {
  options = uniq(options).sort((a,b)=>a.localeCompare(b,'ru'));
  let left = [...options];
  let picked = [];
  while (left.length) {
    const choice = await tp.system.suggester(left, left, false, placeholder);
    if (!choice) break;
    picked.push(choice);
    left = left.filter(x => x !== choice);
  }
  return picked;
}

// -------- выбери область --------
const areas = byType("area").map(f => f.basename);
const selectedArea = await pickOne(areas, "Выбери область науки");

// -------- кандидаты для коллабораций: только лабы этой области --------
const allLabs = byType("lab");
const labsSameArea = allLabs
  .filter(f => f.basename !== title)
  .filter(f => hasText(fm(f)?.area, selectedArea))     // area может быть списком или строкой
  .map(f => f.basename);

const collaborators = await pickMany(labsSameArea, "Коллаборации: только лабы этой области");

// -------- участники (пока без фильтра) --------
const people = byType("person").map(f => f.basename);
const members = await pickMany(people, "Добавить участников");

// -------- YAML --------
tR += `---
type: lab
title: ${title}
area: ${selectedArea ? `[${selectedArea}]` : `[]`}
members: ${members.length ? `[${members.join(", ")}]` : `[]`}
collaborates_with: ${collaborators.length ? `[${collaborators.join(", ")}]` : `[]`}
tags: [kb/lab]
---

# ${title}

## Description
`;
%>