"use client";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  delay?: number;
}

export function GlassCard({ children, className, hover = true, delay = 0 }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      whileHover={hover ? { y: -4, scale: 1.01 } : undefined}
      className={cn(
        "relative rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-xl",
        "dark:bg-white/5 dark:border-white/10",
        "light:bg-white/80 light:border-gray-200/50",
        "transition-shadow duration-300",
        hover && "hover:shadow-2xl hover:shadow-blue-500/10",
        className
      )}
    >
      {children}
    </motion.div>
  );
}
