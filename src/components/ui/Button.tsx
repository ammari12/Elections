"use client";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { ButtonHTMLAttributes, forwardRef } from "react";

const variants = {
  primary: "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-blue-500/25",
  secondary: "bg-white/10 text-white border border-white/20 hover:bg-white/20",
  danger: "bg-gradient-to-r from-red-600 to-red-500 text-white hover:from-red-500 hover:to-red-400",
  ghost: "text-gray-400 hover:text-white hover:bg-white/10",
};

const sizes = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-5 py-2.5 text-sm",
  lg: "px-6 py-3 text-base",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => (
    <motion.button
      ref={ref}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50",
        variants[variant],
        sizes[size],
        className
      )}
      {...(props as any)}
    >
      {children}
    </motion.button>
  )
);
Button.displayName = "Button";
