<%*
const title = await tp.system.prompt("Имя Фамилия?");
if (!title) return;
await tp.file.rename(title);

const files = app.vault.getMarkdownFiles();
const fm = f => app.metadataCache.getFileCache(f)?.frontmatter;

// ---- helpers ----
const asArray = (v) => Array.isArray(v) ? v : (v ? [v] : []);
const stripQuotes = (s) => String(s).replace(/^"+|"+$/g, "").trim(); // убрать внешние кавычки
const linkText = (s) => stripQuotes(s).replace(/^\[\[|\]\]$/g, "").trim(); // "Имя" из [[Имя]]
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
const labFiles = files.filter(f => fm(f)?.type === "lab");
const labNames = labFiles
  .map(f => f.basename)
  .sort((a,b)=>a.localeCompare(b,'ru'));

if (!labNames.length) { new Notice("Сначала создай хотя бы одну лабораторию (type: lab)"); return; }

const peopleFiles = files.filter(f => fm(f)?.type === "person");
const peopleNames = peopleFiles
  .map(f => f.basename)
  .filter(n => n !== title)
  .sort((a,b)=>a.localeCompare(b,'ru'));

// ---- choose relations ----
const selectedLab = await tp.system.suggester(labNames, labNames, false, "Выбери лабораторию");

// (опционально) фильтр коллабораций: люди только из той же лаборатории или любые
const scope = await tp.system.suggester(
  ["Только люди этой лаборатории", "Любые люди"],
  ["same", "all"],
  false,
  "Каких людей показывать в коллаборациях?"
);

let peopleCandidates = peopleNames;

if (scope === "same" && selectedLab) {
  peopleCandidates = peopleFiles
    .filter(f => f.basename !== title)
    .filter(f => {
      const labs = asArray(fm(f)?.lab).map(linkText); // lab: ["[[X]]"]
      return labs.includes(selectedLab);
    })
    .map(f => f.basename)
    .sort((a,b)=>a.localeCompare(b,'ru'));
}

const collaborators = await pickMany(peopleCandidates, "Коллаборации (люди), ESC чтобы закончить");
const collaboratorsLinks = collaborators.map(x => makeQuotedLink(x));

tR += `---
type: person
title: ${title}
lab: ${selectedLab ? `["[[${selectedLab}]]"]` : `[]`}
collaborates_with: [${collaboratorsLinks.join(", ")}]
tags: [kb/person]
---

# ${title}

## Position

## Expertise
`;

const thisLink = makeLink(title);
const findPersonFile = (name) => peopleFiles.find(f => f.basename === name);

for (const otherName of collaborators) {
  const otherFile = findPersonFile(otherName);
  if (!otherFile) continue;

  await app.fileManager.processFrontMatter(otherFile, (frontmatter) => {
    let cw = asArray(frontmatter.collaborates_with).map(stripQuotes);
    const normalized = cw.map(linkText);

    if (!normalized.includes(title)) {
      cw.push(thisLink);
    }

    frontmatter.collaborates_with = cw.map(x => `${x}`);
  });
}
%>