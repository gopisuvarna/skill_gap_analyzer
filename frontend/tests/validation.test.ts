import { isLikelyEmail } from "../src/lib/validation";

describe("isLikelyEmail", () => {
  it("accepts a simple valid email address", () => {
    expect(isLikelyEmail("user@example.com")).toBe(true);
  });

  it("trims surrounding whitespace before validating", () => {
    expect(isLikelyEmail("  user@example.com  ")).toBe(true);
  });

  it("rejects invalid email addresses", () => {
    expect(isLikelyEmail("")).toBe(false);
    expect(isLikelyEmail("user example.com")).toBe(false);
    expect(isLikelyEmail("user.example.com")).toBe(false);
    expect(isLikelyEmail("user@example")).toBe(false);
    expect(isLikelyEmail("user@example.")).toBe(false);
    expect(isLikelyEmail("user@@example.com")).toBe(false);
  });
});
