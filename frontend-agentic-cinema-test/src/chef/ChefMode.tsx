import { useMemo, useState } from "react";
import styles from "./ChefMode.module.css";

type Menu = { title: string; starter: string; main: string; dessert: string; drink: string };
const MENUS: Record<string, Menu> = {
  "French cinema": { title: "French Cinema Night", starter: "Goat cheese crostini", main: "Herb roast chicken with gratin dauphinois", dessert: "Chocolate mousse", drink: "Sparkling water with lemon" },
  "Studio premiere": { title: "Studio Premiere", starter: "Tomato & basil tartlets", main: "Truffle mushroom pasta", dessert: "Berry pavlova", drink: "Citrus spritz" },
  "Late screening": { title: "Late Screening", starter: "Warm focaccia", main: "Roasted vegetable flatbread", dessert: "Vanilla yoghurt & berries", drink: "Mint tea" },
};

export default function ChefMode() {
  const [brief, setBrief] = useState("French cinema");
  const menu = useMemo(() => MENUS[brief] ?? MENUS["French cinema"], [brief]);
  return <section className={styles.card} aria-labelledby="chef-title">
    <div className={styles.kicker}>HEAD CHEF MODE</div>
    <h2 id="chef-title">Build the food story around the screening</h2>
    <p className={styles.intro}>A lightweight production-planning tool for film-night hospitality. This is deterministic demo functionality, not a food-ordering service.</p>
    <label>Production brief<select value={brief} onChange={(e) => setBrief(e.target.value)}>{Object.keys(MENUS).map((key) => <option key={key}>{key}</option>)}</select></label>
    <div className={styles.menu}><h3>{menu.title}</h3><dl><div><dt>Starter</dt><dd>{menu.starter}</dd></div><div><dt>Main</dt><dd>{menu.main}</dd></div><div><dt>Dessert</dt><dd>{menu.dessert}</dd></div><div><dt>Drink</dt><dd>{menu.drink}</dd></div></dl></div>
  </section>;
}
