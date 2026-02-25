<%*
const title = await tp.system.prompt("Название лаборатории?");
if (!title) return;
await tp.file.rename(title);

const files = app.vault.getMarkdownFiles();
const fm = f => app.metadataCache.getFileCache(f)?.frontmatter;

// ---- helpers ----
const asArray = (v) => Array.isArray(v) ? v : (v ? [v] : []);
const stripQuotes = (s) => String(s).replace(/^"+|"+$/g, "").trim(); // убрать внешние кавычки
const linkText = (s) => stripQuotes(s).replace(/^\[\[|\]\]$/g, "").trim(); // получить "Название" из [[Название]]
const makeLink = (name) => `[[${name}]]`;
const makeQuotedLink = (name) => `"[[${name}]]"`;

async function pickMany(options, placeholder) {
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

// ---- lists ----
const areaFiles = files.filter(f => fm(f)?.type === "area");
const areaNames = areaFiles
  .map(f => f.basename)
  .sort((a,b)=>a.localeCompare(b,'ru'));

if (!areaNames.length) { new Notice("Сначала создай хотя бы одну область (type: area)"); return; }

const labFiles = files.filter(f => fm(f)?.type === "lab");
const labNames = labFiles
  .map(f => f.basename)
  .filter(n => n !== title)
  .sort((a,b)=>a.localeCompare(b,'ru'));

// ---- choose relations ----
const selectedArea = await tp.system.suggester(areaNames, areaNames, false, "Выбери область");

// (опционально) фильтрация коллабораций по той же области:
const scope = await tp.system.suggester(
  ["Только лабы этой области", "Любые лабы"],
  ["same", "all"],
  false,
  "Какие лабы показывать в коллаборациях?"
);

let labCandidates = labNames;

if (scope === "same" && selectedArea) {
  labCandidates = labFiles
    .filter(f => f.basename !== title)
    .filter(f => {
      const a = asArray(fm(f)?.area).map(linkText); // area: ["[[X]]"] или [...]
      return a.includes(selectedArea);
    })
    .map(f => f.basename)
    .sort((a,b)=>a.localeCompare(b,'ru'));
}

const collaborators = await pickMany(labCandidates, "Коллаборации (лабы), ESC чтобы закончить");
const collaboratorsLinks = collaborators.map(x => makeQuotedLink(x));

// ---- write current note ----
tR += `---
type: lab
title: ${title}
area: ${selectedArea ? `["[[${selectedArea}]]"]` : `[]`}
collaborates_with: [${collaboratorsLinks.join(", ")}]
tags: [kb/lab]
---

# ${title}

## Description

## Members (авто)
\`\`\`dataview
LIST FROM ""
WHERE type = "person" AND contains(lab, this.file.link)
\`\`\`
`;

// ---- add reverse links to collaborator labs ----
const thisLink = makeLink(title);

// helper: find lab file by basename
const findLabFile = (name) => labFiles.find(f => f.basename === name);

for (const otherName of collaborators) {
  const otherFile = findLabFile(otherName);
  if (!otherFile) continue;

  await app.fileManager.processFrontMatter(otherFile, (frontmatter) => {
    let cw = asArray(frontmatter.collaborates_with).map(stripQuotes); // теперь элементы вида [[X]]
    const normalized = cw.map(linkText); // только имена

    if (!normalized.includes(title)) {
      cw.push(thisLink); // добавляем [[title]]
    }

    // возвращаем как список строк с кавычками: ["[[...]]", ...]
    frontmatter.collaborates_with = cw.map(x => `${x}`);
  });
}
%>