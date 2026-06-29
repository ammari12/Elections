"use client";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
  color?: string;
  showLabel?: boolean;
}

export function ProgressBar({ value, max = 100, className, color = "from-blue-500 to-purple-500", showLabel = true }: ProgressBarProps) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className={cn("w-full", className)}>
      {showLabel && <div className="mb-1 text-xs text-gray-400">{Math.round(pct)}%</div>}
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={cn("h-full rounded-full bg-gradient-to-r", color)}
        />
      </div>
    </div>
  );
}
