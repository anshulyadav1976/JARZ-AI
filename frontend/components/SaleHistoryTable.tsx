"use client";

import React, { useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import type { SaleHistoryRecord } from "@/lib/types";

function formatCurrency(value?: number | null) {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(s?: string | null) {
  if (!s) return "—";
  try {
    const d = new Date(s);
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return String(s);
  }
}

export interface SaleHistoryTableProps {
  postcode: string;
  data?: SaleHistoryRecord[];
  exportUrl: string;
}

export function SaleHistoryTable({ postcode, data = [], exportUrl }: SaleHistoryTableProps) {
  const handleExport = useCallback(async () => {
    const url = `${exportUrl}/api/postcode/${encodeURIComponent(postcode.replace(/\s/g, "").toUpperCase())}/sale/history/export`;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `sale_history_${postcode.replace(/\s/g, "")}.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      console.error("Export failed", e);
    }
  }, [postcode, exportUrl]);

  const rows = data.flatMap((rec) =>
    (rec.transactions || []).map((tx, i) => ({
      address: rec.property_address,
      property_type: rec.property_type,
      sold_date: tx.sold_date,
      sold_price: tx.sold_price,
      tenure: tx.property_tenure,
      price_diff: tx.price_diff_amount,
      price_diff_pct: tx.price_diff_percentage,
    }))
  );

  if (data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide mb-3">
          <span className="w-2 h-2 bg-primary rounded-full" />
          Sale History — {postcode}
        </div>
        <p className="text-muted-foreground">No sale history for this postcode.</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wide">
          <span className="w-2 h-2 bg-primary rounded-full" />
          Sale History — {postcode}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleExport}
          className="gap-2"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </Button>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        {rows.length} transaction{rows.length !== 1 ? "s" : ""} across {data.length} propert{data.length !== 1 ? "ies" : "y"}.
      </p>
      <div className="overflow-x-auto max-h-64 overflow-y-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 sticky top-0">
            <tr>
              <th className="text-left p-2 font-semibold text-muted-foreground">Address</th>
              <th className="text-left p-2 font-semibold text-muted-foreground">Type</th>
              <th className="text-right p-2 font-semibold text-muted-foreground">Sold date</th>
              <th className="text-right p-2 font-semibold text-muted-foreground">Sold price</th>
              <th className="text-right p-2 font-semibold text-muted-foreground">Tenure</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 50).map((row, i) => (
              <tr key={i} className="border-t border-border/50">
                <td className="p-2 text-foreground truncate max-w-[180px]" title={row.address}>
                  {row.address}
                </td>
                <td className="p-2 text-muted-foreground">{row.property_type ?? "—"}</td>
                <td className="p-2 text-right tabular-nums">{formatDate(row.sold_date)}</td>
                <td className="p-2 text-right tabular-nums font-medium">{formatCurrency(row.sold_price)}</td>
                <td className="p-2 text-right text-muted-foreground">{row.tenure ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > 50 && (
        <p className="text-xs text-muted-foreground mt-2">Showing first 50 of {rows.length} transactions. Use Export CSV for full data.</p>
      )}
      <p className="mt-4 text-[10px] text-muted-foreground/80">Data: ScanSan sale history API</p>
    </div>
  );
}
