"use client";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

const variants = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-green-500/20 text-green-400 border-green-500/30",
  info: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

interface BadgeProps {
  variant: keyof typeof variants;
  children: React.ReactNode;
  pulse?: boolean;
  className?: string;
}

export function Badge({ variant, children, pulse = false, className }: BadgeProps) {
  return (
    <motion.span
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className={cn("absolute inline-flex h-full w-full animate-ping rounded-full opacity-75", variant === "critical" ? "bg-red-400" : "bg-current")} />
          <span className={cn("relative inline-flex h-2 w-2 rounded-full", variant === "critical" ? "bg-red-500" : "bg-current")} />
        </span>
      )}
      {children}
    </motion.span>
  );
}
