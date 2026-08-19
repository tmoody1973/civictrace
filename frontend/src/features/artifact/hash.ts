// "Exact copy" must be checkable. Three hashes can disagree: the ledger's, the server header's,
// and what the browser actually received. We compute the third ourselves.

export type HashVerdict = "match" | "mismatch" | "unknown";

export const HASH_PREFIX = "sha256:";

export async function sha256Hex(bytes: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return HASH_PREFIX + [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Compare what the ledger says, what the server claimed, and what we received. */
export function compareHashes(ledgerHash: string | null, headerHash: string | null, computedHash: string | null): HashVerdict {
  if (!ledgerHash || !computedHash) return "unknown";
  if (ledgerHash !== computedHash) return "mismatch";
  if (headerHash && headerHash !== computedHash) return "mismatch";
  return "match";
}

export const HASH_VERDICT_COPY: Record<HashVerdict, string> = {
  match: "Matches ledger — these bytes are the exact saved copy",
  mismatch: "Does not match the ledger — do not rely on this copy",
  unknown: "Not checked — ledger hash or file not available",
};
