import { TopBar } from "@/components/layout/top-bar";
import { IntakePage } from "@/features/intake/intake-page";

export default function Intake() {
  return (
    <div className="flex h-dvh flex-col">
      <TopBar />
      <main className="mx-auto w-full max-w-2xl overflow-y-auto p-6">
        <h1 className="mb-1 text-lg font-semibold">Start a case</h1>
        <p className="mb-4 text-sm text-muted-foreground">
          Search the City of Milwaukee&apos;s official record in plain words, review what it
          lists, and approve it into a Promise Ledger case. Nothing becomes a case without you.
        </p>
        <IntakePage />
      </main>
    </div>
  );
}
