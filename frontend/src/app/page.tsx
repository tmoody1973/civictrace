import { TopBar } from "@/components/layout/top-bar";
import { CaseRail } from "@/features/case/case-rail";

export default function Home() {
  return (
    <div className="flex h-dvh flex-col">
      <TopBar />
      <main className="mx-auto w-full max-w-xl p-6">
        <h1 className="mb-1 text-lg font-semibold">Promise Ledger cases</h1>
        <p className="mb-4 text-sm text-muted-foreground">Pick a case to open the Evidence Studio.</p>
        <CaseRail />
      </main>
    </div>
  );
}
