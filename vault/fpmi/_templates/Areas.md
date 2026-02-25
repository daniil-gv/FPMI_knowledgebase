<%*
const title = await tp.system.prompt("Название области науки?");
if (!title) return;

await tp.file.rename(title);

// helpers
const mdFiles = () => app.vault.getMarkdownFiles();
const fm = (file) => app.metadataCache.getFileCache(file)?.frontmatter;
const byType = (t) => mdFiles().filter(f => fm(f)?.type === t);
const uniq = (arr) => [...new Set(arr)].filter(Boolean);

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

const areas = byType("area").map(f => f.basename).filter(n => n !== title);
const collaborators = await pickMany(areas, "Добавить связанные области");

tR += `---
type: area
title: "${title}"
collaborates_with: [${collaborators.map(a => `"${a}"`).join(", ")}]
tags: ["kb/area"]
---

# ${title}

## Description
`;
%>
