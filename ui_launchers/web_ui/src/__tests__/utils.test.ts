import { describe, expect, it } from "vitest";
import { computeConfidencePct } from "@/lib/utils";

describe("computeConfidencePct", () => {
  it("converts numeric values to percentage", () => {
    expect(computeConfidencePct(0.85)).toBe(85);

  it("converts numeric strings to percentage", () => {
    expect(computeConfidencePct("0.501")).toBe(50);

  it("returns null for invalid inputs", () => {
    expect(computeConfidencePct("abc")).toBeNull();
    expect(computeConfidencePct(null)).toBeNull();
    expect(computeConfidencePct(NaN)).toBeNull();

