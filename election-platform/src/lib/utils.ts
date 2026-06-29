import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat("fr-FR").format(num);
}

export function formatDate(date: Date | string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(date));
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: "#E53E3E",
    high: "#DD6B20",
    medium: "#ECC94B",
    low: "#38A169",
  };
  return colors[severity] || "#3182CE";
}
