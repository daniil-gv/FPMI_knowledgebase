<%*
const title = await tp.system.prompt("Имя Фамилия?");
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

// -------- выбери лабораторию --------
const labsFiles = byType("lab");
const labNames = labsFiles.map(f => f.basename);
const selectedLab = await pickOne(labNames, "Выбери лабораторию");

// находим область выбранной лабы
const selectedLabFile = labsFiles.find(f => f.basename === selectedLab);
const selectedArea = selectedLabFile ? (asArray(fm(selectedLabFile)?.area)[0] || "") : "";

// строим список лабораторий этой области
const labsSameArea = labsFiles
  .filter(f => hasText(fm(f)?.area, selectedArea))
  .map(f => f.basename);

// -------- кандидаты-люди: только из этой области --------
const peopleFiles = byType("person");
const peopleSameArea = peopleFiles
  .filter(f => f.basename !== title)
  .filter(f => {
    const personLabs = asArray(fm(f)?.lab);        // у человека lab: [..]
    return personLabs.some(l => labsSameArea.includes(String(l)));
  })
  .map(f => f.basename);

const collaborates = await pickMany(
  peopleSameArea,
  selectedArea
    ? `Коллаборации: люди из области "${selectedArea}"`
    : `Коллаборации: люди (область не определена)`
);

// -------- YAML --------
tR += `---
type: person
title: ${title}
lab: ${selectedLab ? `[${selectedLab}]` : `[]`}
collaborates_with: ${collaborates.length ? `[${collaborates.join(", ")}]` : `[]`}
tags: [kb/person]
---

# ${title}

## Position

## Expertise
`;
%>