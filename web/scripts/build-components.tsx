import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";

import { Card } from "../src/cards/Card";
import { Leader } from "../src/cards/Leader";

const here = dirname(fileURLToPath(import.meta.url));
const webDir = resolve(here, "..");
const rootDir = resolve(webDir, "..");

const css = readFileSync(resolve(webDir, "src", "cards", "cards.css"), "utf-8");

function doc(title: string, body: string): string {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff;
      font-family: Arial, Helvetica, sans-serif;
    }

${css}
  </style>
</head>

<body>
${body}
</body>
</html>
`;
}

const cardMarkup = renderToStaticMarkup(
  <Card name="Nombre" code="OP16-048" quantity="x4" imageSrc="../example_images/card.png" />
);
writeFileSync(resolve(rootDir, "back", "components", "card.html"), doc("Card", cardMarkup));

const leaderMarkup = renderToStaticMarkup(
  <Leader name="Líder" imageSrc="../example_images/leader.png" />
);
writeFileSync(resolve(rootDir, "back", "components", "leader.html"), doc("Leader", leaderMarkup));

console.log("componentes generados: back/components/card.html, back/components/leader.html");