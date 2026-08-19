import { EvidenceStudioShell } from "@/components/layout/evidence-studio-shell";
import { TopBar } from "@/components/layout/top-bar";
import { CaseRail } from "@/features/case/case-rail";
import { CaseReviewPane } from "@/features/case/case-review-pane";

export default async function CasePage({ params }: PageProps<"/cases/[caseId]">) {
  const { caseId } = await params;
  const decoded = decodeURIComponent(caseId);
  return (
    <div className="flex h-dvh flex-col">
      <TopBar caseId={decoded} />
      <EvidenceStudioShell
        rail={<CaseRail activeCaseId={decoded} />}
        source={<Placeholder>Original PDF opens here on the exact anchored page (MOO-699).</Placeholder>}
        review={<CaseReviewPane caseId={decoded} />}
        timeline={<Placeholder>Evidence Trace rows from the ledger render here (MOO-698).</Placeholder>}
      />
    </div>
  );
}

function Placeholder({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>;
}
