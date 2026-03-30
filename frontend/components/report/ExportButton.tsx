"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { getReportData } from "@/lib/api";

interface ExportButtonProps {
  simId: string;
}

export function ExportButton({ simId }: ExportButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);
    try {
      const data = await getReportData(simId);
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `narrativeflow-${simId.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently fail for now
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button variant="outline" onClick={handleExport} disabled={loading}>
      {loading ? "Exporting..." : "Export JSON"}
    </Button>
  );
}
