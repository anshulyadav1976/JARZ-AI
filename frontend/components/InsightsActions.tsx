"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Printer, Download, Share2, Bookmark, BookmarkCheck } from "lucide-react";

interface InsightsActionsProps {
  onPrint?: () => void;
  onExport?: () => void;
  onShare?: () => void;
  isSaved?: boolean;
  onToggleSave?: () => void;
}

export function InsightsActions({
  onPrint,
  onExport,
  onShare,
  isSaved = false,
  onToggleSave,
}: InsightsActionsProps) {
  const handlePrint = () => {
    if (onPrint) {
      onPrint();
    } else {
      window.print();
    }
  };

  const handleExport = () => {
    if (onExport) {
      onExport();
    } else {
      // Default: trigger browser print dialog for PDF
      window.print();
    }
  };

  const handleShare = async () => {
    if (onShare) {
      onShare();
    } else {
      // Try native share API
      if (navigator.share) {
        try {
          await navigator.share({
            title: "Rental Market Insights",
            text: "Check out this rental market analysis",
            url: window.location.href,
          });
        } catch (err) {
          // User cancelled or error
          console.log("Share cancelled");
        }
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(window.location.href);
        alert("Link copied to clipboard!");
      }
    }
  };

  return (
    <div className="flex items-center gap-2 p-4 bg-card/50 border-b">
      <div className="flex-1">
        <h2 className="text-lg font-semibold text-foreground">Market Insights</h2>
        <p className="text-xs text-muted-foreground">AI-powered rental market analysis</p>
      </div>
      <div className="flex items-center gap-1">
        {onToggleSave && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleSave}
            className="h-8 w-8 p-0"
            title={isSaved ? "Remove from watchlist" : "Add to watchlist"}
          >
            {isSaved ? (
              <BookmarkCheck className="h-4 w-4 text-primary" />
            ) : (
              <Bookmark className="h-4 w-4" />
            )}
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleShare}
          className="h-8 px-3 gap-1.5"
          title="Share insights"
        >
          <Share2 className="h-3.5 w-3.5" />
          <span className="hidden sm:inline text-xs">Share</span>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleExport}
          className="h-8 px-3 gap-1.5"
          title="Export as PDF"
        >
          <Download className="h-3.5 w-3.5" />
          <span className="hidden sm:inline text-xs">Export</span>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handlePrint}
          className="h-8 px-3 gap-1.5"
          title="Print report"
        >
          <Printer className="h-3.5 w-3.5" />
          <span className="hidden sm:inline text-xs">Print</span>
        </Button>
      </div>
    </div>
  );
}
