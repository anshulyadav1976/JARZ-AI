"use client";

import React, { useState } from "react";

interface TooltipProps {
  children: React.ReactNode;
  content: string;
  side?: "left" | "right";
}

export function Tooltip({ children, content, side = "right" }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          className={`absolute z-50 px-2 py-1 text-xs font-medium text-white bg-gray-900 dark:bg-gray-700 rounded shadow-lg whitespace-nowrap ${
            side === "right" ? "left-full ml-2" : "right-full mr-2"
          } top-1/2 -translate-y-1/2 animate-in fade-in-0 zoom-in-95`}
        >
          {content}
          <div
            className={`absolute w-2 h-2 bg-gray-900 dark:bg-gray-700 transform rotate-45 top-1/2 -translate-y-1/2 ${
              side === "right" ? "-left-1" : "-right-1"
            }`}
          />
        </div>
      )}
    </div>
  );
}
