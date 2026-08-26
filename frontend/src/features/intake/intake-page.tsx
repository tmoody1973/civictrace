"use client";

import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { ApiErrorState } from "@/components/layout/api-error-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BundleReview } from "@/features/intake/bundle-review";
import { useIntakeBundle, useIntakeLookup, useIntakeSearch } from "@/features/intake/queries";
import type { MatterSearchResultView } from "@/lib/api-types";

const inputClassName =
  "w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-ring";

/** Start your own case: plain-words search → official matters → human review (MOO-749).
 *  The file number is an output the journalist clicks, never knowledge they must bring. */
export function IntakePage() {
  const [query, setQuery] = useState("");
  const search = useIntakeSearch();
  const lookup = useIntakeLookup();
  const bundleId = lookup.data?.bundle_id ?? null;
  const bundle = useIntakeBundle(bundleId);

  return (
    <div className="space-y-6">
      <form
        className="space-y-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (query.trim()) search.mutate(query.trim());
        }}
      >
        <label className="block text-sm font-medium" htmlFor="intake-search">
          What are you looking into?
        </label>
        <p className="text-sm text-muted-foreground">
          Type a few words — a project, a place, a program — and the system searches the
          City&apos;s official record for matching files. It matches words in official titles
          (not meaning), so try the words officials would use. A six-digit file number works
          too, if you have one.
        </p>
        <div className="flex gap-2">
          <input
            id="intake-search"
            className={inputClassName}
            placeholder="e.g. Amani homeownership — or 260435"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Button type="submit" disabled={search.isPending}>
            {search.isPending ? "Searching…" : "Search the record"}
          </Button>
        </div>
      </form>

      {search.isError ? <ApiErrorState error={search.error} what="the official record" /> : null}
      {search.data ? (
        <SearchResults
          results={search.data}
          onPick={(file) => lookup.mutate(file)}
          picking={lookup.isPending}
        />
      ) : null}
      {lookup.isError ? <ApiErrorState error={lookup.error} what="the selected file" /> : null}
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

function SearchResults({
  results,
  onPick,
  picking,
}: {
  results: MatterSearchResultView[];
  onPick: (file: string) => void;
  picking: boolean;
}) {
  if (results.length === 0) {
    return (
      <p className="text-sm text-muted-foreground" data-testid="search-empty">
        The official record lists nothing with those words. Try fewer or different words —
        official titles often use formal names (&ldquo;Tax Incremental District&rdquo;, a
        street name, a program&apos;s full name).
      </p>
    );
  }
  return (
    <ul className="space-y-2" aria-label="Matching official files" data-testid="search-results">
      {results.map((matter) => (
        <li key={matter.matter_id} className="rounded-md border p-3 text-sm">
          <p className="leading-relaxed">{matter.title}</p>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="outline">File {matter.legistar_file}</Badge>
            <span>{matter.matter_type ?? "Matter"}</span>
            <span>· status {matter.matter_status ?? "unknown"}</span>
            <span>· introduced {matter.intro_date ?? "unknown"}</span>
          </p>
          <Button
            className="mt-2"
            size="sm"
            disabled={picking}
            onClick={() => onPick(matter.legistar_file)}
            aria-label={`Review file ${matter.legistar_file}`}
          >
            Review this file — see its documents
          </Button>
        </li>
      ))}
    </ul>
  );
}
