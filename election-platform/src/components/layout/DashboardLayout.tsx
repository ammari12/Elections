"use client";
import { Sidebar } from "./Sidebar";
import { useAppStore } from "@/stores/useAppStore";
import { motion } from "framer-motion";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useAppStore();

  return (
    <div className="min-h-screen bg-[#0A0E1A] text-white">
      <Sidebar />
      <motion.main
        initial={false}
        animate={{ marginLeft: sidebarOpen ? 260 : 72 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="min-h-screen p-6"
      >
        {children}
      </motion.main>
    </div>
  );
}
