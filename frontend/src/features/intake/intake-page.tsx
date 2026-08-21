"use client";

import Link from "next/link";
import { useState } from "react";

import { ApiErrorState } from "@/components/layout/api-error-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BundleReview } from "@/features/intake/bundle-review";
import { useIntakeBundle, useIntakeLookup } from "@/features/intake/queries";

const inputClassName =
  "w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-ring";

/** Start your own case: official lookup → human review → gated creation (MOO-719). */
export function IntakePage() {
  const [fileNumber, setFileNumber] = useState("");
  const lookup = useIntakeLookup();
  const bundleId = lookup.data?.bundle_id ?? null;
  const bundle = useIntakeBundle(bundleId);

  return (
    <div className="space-y-6">
      <form
        className="space-y-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (fileNumber.trim()) lookup.mutate(fileNumber.trim());
        }}
      >
        <label className="block text-sm font-medium" htmlFor="intake-file-number">
          Milwaukee Legistar file number
        </label>
        <p className="text-sm text-muted-foreground">
          The system asks the City&apos;s official record system what this file is and which
          documents it lists. Nothing becomes a case until you review and approve.
        </p>
        <div className="flex gap-2">
          <input
            id="intake-file-number"
            className={inputClassName}
            placeholder="e.g. 260433"
            value={fileNumber}
            onChange={(event) => setFileNumber(event.target.value)}
            inputMode="numeric"
          />
          <Button type="submit" disabled={lookup.isPending}>
            {lookup.isPending ? "Looking up…" : "Look up"}
          </Button>
        </div>
      </form>

      {lookup.isError ? <ApiErrorState error={lookup.error} what="the official record" /> : null}
      {bundleId && bundle.isPending ? (
        <Skeleton role="status" className="h-40 w-full" aria-label="Loading candidate bundle" />
      ) : null}
      {bundle.data ? <BundleReview bundle={bundle.data} /> : null}

      <p className="text-sm">
        <Link href="/" className="underline underline-offset-2">
          Back to cases
        </Link>
      </p>
    </div>
  );
}
