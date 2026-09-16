import { readFile } from "node:fs/promises";

const files = [
  "app/page.tsx",
  "app/layout.tsx",
  "app/api/cinema/route.ts",
  "app/api/cinema/action/route.ts",
  "components/CinemaApp.tsx",
  "components/CinemaApp.module.css"
];

for (const file of files) {
  const text = await readFile(file, "utf8");
  if (!text.trim()) throw new Error(`${file} is empty`);
}

const app = await readFile("components/CinemaApp.tsx", "utf8");
const route = await readFile("app/api/cinema/route.ts", "utf8");
const action = await readFile("app/api/cinema/action/route.ts", "utf8");

for (const marker of [
  'fetch("/api/cinema"',
  'fetch("/api/cinema/action"',
  'window.print()',
  'navigator.share',
  'setHintOpen'
]) {
  if (!app.includes(marker)) throw new Error(`Missing UI interaction: ${marker}`);
}

for (const marker of ['CINEMA_BACKEND_URL', 'cache: "no-store"', 'AbortController']) {
  if (!route.includes(marker)) throw new Error(`Missing API safeguard: ${marker}`);
}

for (const marker of ['CINEMA_SAVE_URL', 'CINEMA_CHALLENGE_URL']) {
  if (!action.includes(marker)) throw new Error(`Missing action boundary: ${marker}`);
}

console.log("FRONTEND_SOURCE_SMOKE_PASS");
