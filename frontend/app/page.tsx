import { Suspense } from "react";
import { SeedForm } from "@/components/seed-input/SeedForm";
import { RecentSimulations } from "@/components/seed-input/RecentSimulations";

export default function HomePage() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center p-8 gap-8">
      <div className="text-center space-y-3 max-w-2xl">
        <h1 className="text-4xl font-bold tracking-tight">NarrativeFlow</h1>
        <p className="text-lg text-muted-foreground">
          Predict how misinformation spreads before it happens. Seed a scenario,
          watch it propagate through a simulated social network, and discover
          where interventions are most effective.
        </p>
      </div>

      <Suspense>
        <SeedForm />
      </Suspense>

      <RecentSimulations />

      <div className="text-center text-xs text-muted-foreground max-w-md">
        <p>
          Powered by the SMIR propagation model with LLM-generated behavioral
          archetypes. Runs entirely on your machine — no data leaves your
          network.
        </p>
      </div>
    </main>
  );
}
