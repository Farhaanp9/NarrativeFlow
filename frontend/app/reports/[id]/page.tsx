import Link from "next/link";
import { getReport, getSimulation } from "@/lib/api";
import { ReportView } from "@/components/report/ReportView";
import { ExportButton } from "@/components/report/ExportButton";
import { Button } from "@/components/ui/button";

interface ReportPageProps {
  params: Promise<{ id: string }>;
}

export default async function ReportPage({ params }: ReportPageProps) {
  const { id } = await params;

  let report;
  try {
    report = await getReport(id);
  } catch {
    return (
      <main className="flex-1 flex items-center justify-center p-8">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold">Report Not Found</h1>
          <p className="text-muted-foreground">
            This simulation may still be running or the report has not been
            generated yet.
          </p>
          <Link href={`/simulation/${id}`}>
            <Button variant="outline">Back to Simulation</Button>
          </Link>
        </div>
      </main>
    );
  }

  // Build "Run Again" URL with pre-filled config
  let rerunUrl = "/";
  try {
    const sim = await getSimulation(id);
    const params = new URLSearchParams({
      seed_text: sim.seed_text,
      population_size: String(sim.population_size),
      topology: sim.topology,
      max_ticks: String(sim.max_ticks),
    });
    rerunUrl = `/?${params.toString()}`;
  } catch {
    // If we can't fetch sim details, just link to home
  }

  return (
    <main className="flex-1 max-w-4xl mx-auto p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            NarrativeFlow
          </Link>
          <span className="text-muted-foreground">/</span>
          <span className="text-sm font-mono">{id.slice(0, 8)}</span>
          <span className="text-muted-foreground">/</span>
          <span className="text-sm">Report</span>
        </div>
        <div className="flex gap-2">
          <ExportButton simId={id} />
          <Link href={rerunUrl}>
            <Button variant="outline">Run Again</Button>
          </Link>
          <Link href="/">
            <Button variant="outline">New Simulation</Button>
          </Link>
        </div>
      </div>

      <ReportView content={report.content} />
    </main>
  );
}
