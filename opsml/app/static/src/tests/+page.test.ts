import { render } from "@testing-library/svelte";
import HomeSpan from "../lib/Homepage_span.svelte";
import Card from "../lib/Card.svelte";
import { it } from "vitest";

it("render homepage", () => {
  render(Card, {
    hoverColor: "blue",
    repository: "test",
    name: "test",
    version: "0.1.0",
    date: "2021-09-01T00:00:00Z",
    svgClass: "test",
  });
});

it("render span", () => {
  render(HomeSpan);
});
