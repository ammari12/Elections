"use client";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/stores/useAppStore";
import {
  LayoutDashboard, Radio, Upload, Shield, Map, Users, FileText, Sun, Moon, ChevronLeft, ChevronRight, Bell, Activity
} from "lucide-react";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/veille", icon: Radio, label: "Veille OSINT" },
  { href: "/upload", icon: Upload, label: "Upload" },
  { href: "/securite", icon: Shield, label: "Sécurité" },
  { href: "/cartographie", icon: Map, label: "Cartographie" },
  { href: "/partis", icon: Users, label: "Partis" },
  { href: "/reporting", icon: FileText, label: "Rapports" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme, toggleTheme, sidebarOpen, toggleSidebar, notifications } = useAppStore();
  const unread = notifications.filter((n) => !n.read).length;

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarOpen ? 260 : 72 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="fixed left-0 top-0 z-50 flex h-screen flex-col border-r border-white/10 bg-[#0B0F1A]/95 backdrop-blur-xl"
    >
      <div className="flex items-center gap-3 border-b border-white/10 px-4 py-5">
        <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.6 }} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-lg font-bold text-white">
          V
        </motion.div>
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} className="overflow-hidden">
              <div className="text-sm font-bold text-white">VeilleMaroc</div>
              <div className="text-[10px] text-gray-500">Élections 2026</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: 4 }}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white shadow-lg shadow-blue-500/5"
                    : "text-gray-400 hover:bg-white/5 hover:text-white"
                )}
              >
                <item.icon size={20} className={active ? "text-blue-400" : ""} />
                <AnimatePresence>
                  {sidebarOpen && (
                    <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
                {active && <motion.div layoutId="activeNav" className="absolute left-0 h-8 w-1 rounded-r-full bg-blue-500" />}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      <div className="space-y-2 border-t border-white/10 px-3 py-4">
        <button onClick={toggleTheme} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-white">
          {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
          {sidebarOpen && <span>{theme === "dark" ? "Mode clair" : "Mode sombre"}</span>}
        </button>

        <div className="relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-gray-400">
          <Bell size={20} />
          {sidebarOpen && <span>Notifications</span>}
          {unread > 0 && (
            <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute right-2 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
              {unread}
            </motion.span>
          )}
        </div>

        <button onClick={toggleSidebar} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-white">
          {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
          {sidebarOpen && <span>Réduire</span>}
        </button>
      </div>
    </motion.aside>
  );
}
