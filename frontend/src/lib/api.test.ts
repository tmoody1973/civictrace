import { describe, expect, it } from "vitest";

import { ApiError, unwrapEnvelope } from "@/lib/api";

describe("unwrapEnvelope", () => {
  it("returns data from an ok envelope", () => {
    expect(unwrapEnvelope({ ok: true, data: { status: "ok" }, error: null }, 200)).toEqual({ status: "ok" });
  });

  it("throws the backend's own error text on a 404 envelope", () => {
    expect(() => unwrapEnvelope({ ok: false, data: null, error: "case 'x' not found" }, 404)).toThrowError(
      new ApiError("case 'x' not found", 404),
    );
  });

  it("refuses a body that is not an envelope", () => {
    expect(() => unwrapEnvelope({ detail: "Not Found" }, 404)).toThrow(/Unexpected response shape/);
    expect(() => unwrapEnvelope(null, 500)).toThrow(ApiError);
  });
});
