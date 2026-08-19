import Link from "next/link";

export function TopBar({ caseId }: { caseId?: string }) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b px-4">
      <Link href="/" className="font-semibold tracking-tight">
        CivicTrace <span className="font-normal text-muted-foreground">Evidence Studio</span>
      </Link>
      {caseId ? (
        <span className="truncate font-mono text-xs text-muted-foreground">
          <span className="sr-only">Current case id: </span>
          {caseId}
        </span>
      ) : null}
    </header>
  );
}
