import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { allApprovalCopy } from "@/features/approval/copy";
import { allCaseCopy } from "@/features/case/copy";
import { allTraceCopy } from "@/features/trace/copy";

// Single source of truth: the backend's own allegation-word list.
const POLICY_FILE = resolve(process.cwd(), "../backend/app/policies/language_policy.py");

function allegationTermsFromBackend(): string[] {
  const source = readFileSync(POLICY_FILE, "utf8");
  const block = source.split("ALLEGATION_TERMS")[1]?.split(")")[0] ?? "";
  const terms = [...block.matchAll(/"([^"]+)"/g)].map((match) => match[1]);
  if (terms.length < 10) throw new Error(`could not read ALLEGATION_TERMS from ${POLICY_FILE}`);
  return terms;
}

describe("case copy vocabulary", () => {
  it("contains none of the backend's allegation words", () => {
    const terms = allegationTermsFromBackend();
    const pattern = new RegExp(`\\b(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\b`, "i");
    const offenders = [...allCaseCopy(), ...allTraceCopy(), ...allApprovalCopy()].filter((text) =>
      pattern.test(text),
    );
    expect(offenders).toEqual([]);
  });

  it("uses record-grounded phrasing", () => {
    const joined = allCaseCopy().join(" ");
    expect(joined).toMatch(/record establishes/);
    expect(joined).toMatch(/does not establish/);
    expect(joined).toMatch(/later document revises/);
  });
});
