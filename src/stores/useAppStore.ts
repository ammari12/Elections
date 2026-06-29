import { create } from "zustand";

export type Theme = "dark" | "light";
export type Period = "24h" | "7d" | "30d" | "3m" | "custom";
export type AlertSeverity = "critical" | "high" | "medium" | "low";

export interface Notification {
  id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  timestamp: Date;
  read: boolean;
}

interface AppState {
  theme: Theme;
  toggleTheme: () => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  period: Period;
  setPeriod: (p: Period) => void;
  selectedRegions: string[];
  setSelectedRegions: (r: string[]) => void;
  selectedParties: string[];
  setSelectedParties: (p: string[]) => void;
  notifications: Notification[];
  addNotification: (n: Notification) => void;
  dismissNotification: (id: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: "dark",
  toggleTheme: () =>
    set((s) => ({ theme: s.theme === "dark" ? "light" : "dark" })),
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  period: "30d",
  setPeriod: (period) => set({ period }),
  selectedRegions: [],
  setSelectedRegions: (selectedRegions) => set({ selectedRegions }),
  selectedParties: [],
  setSelectedParties: (selectedParties) => set({ selectedParties }),
  notifications: [],
  addNotification: (n) =>
    set((s) => ({ notifications: [n, ...s.notifications] })),
  dismissNotification: (id) =>
    set((s) => ({
      notifications: s.notifications.filter((n) => n.id !== id),
    })),
}));
