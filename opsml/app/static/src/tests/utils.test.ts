import * as page from "../lib/scripts/utils";
import { it, expect } from "vitest";

// test calculateTimeBetween
it("calculateTimeBetween", () => {
  let ts = new Date().getTime();
  let timeBetween = page.calculateTimeBetween(ts);
  expect(timeBetween).toMatch(/(^\d+ hours ago$)|(^\d+ days ago$)/);
});
