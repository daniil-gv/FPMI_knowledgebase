<%*
const title = await tp.system.prompt("Название области?");
if (!title) return;
await tp.file.rename(title);

const files = app.vault.getMarkdownFiles();
const fm = f => app.metadataCache.getFileCache(f)?.frontmatter;

// ---- helpers ----
const asArray = (v) => Array.isArray(v) ? v : (v ? [v] : []);
const normalizeLinkText = (s) => String(s).replace(/^"+|"+$/g,"").trim(); // убираем кавычки
const makeLinkString = (name) => `[[${name}]]`;
const makeQuotedLinkString = (name) => `"[[${name}]]"`; // как у тебя

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

// ---- собрать список областей ----
const areaFiles = files.filter(f => fm(f)?.type === "area");
const areaNames = areaFiles
  .map(f => f.basename)
  .filter(n => n !== title)
  .sort((a,b)=>a.localeCompare(b,'ru'));

// ---- выбрать коллаборации ----
const collaborators = await pickMany(areaNames, "Коллаборации (области)");
const collaboratorsLinks = collaborators.map(x => makeQuotedLinkString(x));

// ---- записать текущую заметку ----
tR += `---
type: area
title: ${title}
collaborates_with: [${collaboratorsLinks.join(", ")}]
tags: [kb/area]
---

# ${title}

## Description
`;

// ---- двустороннее прокидывание ----
const thisLink = makeLinkString(title);
const findAreaFileByName = (name) => areaFiles.find(f => f.basename === name);

for (const otherName of collaborators) {
  const otherFile = findAreaFileByName(otherName);
  if (!otherFile) continue;

  await app.fileManager.processFrontMatter(otherFile, (frontmatter) => {
    let cw = asArray(frontmatter.collaborates_with).map(normalizeLinkText);
    if (!cw.includes(thisLink)) {
      cw.push(thisLink);
    }

    frontmatter.collaborates_with = cw.map(x => `${x}`);
  });
}
%>