import { describe, expect, it } from "vitest";

import { compareHashes, sha256Hex } from "@/features/artifact/hash";

describe("compareHashes", () => {
  it("matches when ledger, header and computed agree", () => {
    expect(compareHashes("sha256:a", "sha256:a", "sha256:a")).toBe("match");
    expect(compareHashes("sha256:a", null, "sha256:a")).toBe("match");
  });
  it("flags a mismatch from either the ledger or the header", () => {
    expect(compareHashes("sha256:a", "sha256:a", "sha256:b")).toBe("mismatch");
    expect(compareHashes("sha256:a", "sha256:x", "sha256:a")).toBe("mismatch");
  });
  it("is unknown when something is missing", () => {
    expect(compareHashes(null, "sha256:a", "sha256:a")).toBe("unknown");
    expect(compareHashes("sha256:a", "sha256:a", null)).toBe("unknown");
  });
  it("computes the same sha256 the backend does", async () => {
    const bytes = new TextEncoder().encode("abc").buffer as ArrayBuffer;
    expect(await sha256Hex(bytes)).toBe("sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  });
});
