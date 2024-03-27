import { render } from "@testing-library/svelte";
import { it } from "vitest";
import Homepage from "../lib/Homepage.svelte";
import Card from "../lib/Card.svelte";
import type { RecentCards, CardJson } from "$lib/scripts/homepage";

const cards: CardJson[] = [
  {
    date: "2021-09-01T00:00:00Z",
    app_env: "test",
    uid: "test",
    repository: "test",
    contact: "test",
    name: "test",
    version: "0.1.0",
    timestamp: 1711563309,
    tags: new Map(),
  },
];

const recentCards: RecentCards = {
  modelcards: cards,
  datacards: cards,
  runcards: cards,
};

it("render homepage", () => {
  render(Card, {
    hoverColor: "blue",
    repository: "test",
    name: "test",
    version: "0.1.0",
    timestamp: 1711563309,
    svgClass: "test",
  });
});

it("render span", () => {
  render(Homepage, { cards: recentCards });
});
