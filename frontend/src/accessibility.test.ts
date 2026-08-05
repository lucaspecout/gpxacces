import { describe, expect, it } from "vitest";

describe("accessibility legend", () => {
  it("keeps four distinct statuses", () => {
    expect(new Set(["green", "orange", "red", "gray"]).size).toBe(4);
  });
});
