"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Shield, Radio, Map, FileText, Upload, Users, ArrowRight, Activity, Eye, BarChart3, Globe } from "lucide-react";
import { Button } from "@/components/ui/Button";

const ParticleField = dynamic(() => import("@/components/three/ParticleField").then(m => ({ default: m.ParticleField })), { ssr: false });

const features = [
  { icon: Radio, title: "Veille OSINT", desc: "Surveillance en temps réel des réseaux sociaux et de la presse marocaine", color: "from-blue-500 to-cyan-500" },
  { icon: Shield, title: "Sécurité Électorale", desc: "Détection automatique des menaces, injures et désinformation", color: "from-red-500 to-orange-500" },
  { icon: Map, title: "Cartographie", desc: "Visualisation géographique des risques sur les 12 régions du Maroc", color: "from-emerald-500 to-teal-500" },
  { icon: Users, title: "Partis Politiques", desc: "Suivi de l'activité des 12 partis politiques majeurs", color: "from-purple-500 to-pink-500" },
  { icon: Upload, title: "Upload Intelligent", desc: "Analyse automatique de documents, images et vidéos", color: "from-amber-500 to-yellow-500" },
  { icon: FileText, title: "Rapports PDF", desc: "Génération de rapports professionnels de 55-75 pages", color: "from-indigo-500 to-blue-500" },
];

const stats = [
  { value: "53+", label: "Sources Presse" },
  { value: "12", label: "Régions" },
  { value: "12", label: "Partis Suivis" },
  { value: "24/7", label: "Veille Continue" },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0A0E1A]">
      <ParticleField />

      {/* Navigation */}
      <motion.nav initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.6 }} className="fixed top-0 z-50 w-full border-b border-white/5 bg-[#0A0E1A]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 font-bold text-white">V</div>
            <span className="text-lg font-bold">VeilleMaroc</span>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm text-gray-400 hover:text-white transition-colors">Fonctionnalités</a>
            <a href="#stats" className="text-sm text-gray-400 hover:text-white transition-colors">Statistiques</a>
            <Link href="/dashboard"><Button size="sm">Accéder au Dashboard</Button></Link>
          </div>
        </div>
      </motion.nav>

      {/* Hero */}
      <section className="relative flex min-h-screen items-center justify-center px-6 pt-20">
        <div className="mx-auto max-w-5xl text-center">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-1.5 text-sm text-blue-400">
              <Activity size={14} /> Élections Législatives 2026
            </div>
          </motion.div>

          <motion.h1 initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.1 }} className="mb-6 text-5xl font-extrabold leading-tight tracking-tight md:text-7xl">
            Plateforme de{" "}
            <span className="gradient-text">Veille Électorale</span>
            <br />du Maroc
          </motion.h1>

          <motion.p initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }} className="mx-auto mb-10 max-w-2xl text-lg text-gray-400 md:text-xl">
            Surveillance OSINT en temps réel, analyse de sentiment, détection des menaces et génération de rapports stratégiques pour les élections législatives 2026.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.3 }} className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/dashboard">
              <Button size="lg">
                Accéder au Dashboard <ArrowRight size={18} />
              </Button>
            </Link>
            <Button variant="secondary" size="lg">
              <Eye size={18} /> Voir une démo
            </Button>
          </motion.div>
        </div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 2, delay: 1 }} className="absolute bottom-10 left-1/2 -translate-x-1/2">
          <motion.div animate={{ y: [0, 8, 0] }} transition={{ repeat: Infinity, duration: 2 }} className="h-10 w-6 rounded-full border-2 border-white/20 p-1">
            <div className="h-2 w-full rounded-full bg-white/40" />
          </motion.div>
        </motion.div>
      </section>

      {/* Stats */}
      <section id="stats" className="relative py-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
            {stats.map((s, i) => (
              <motion.div key={s.label} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="glass rounded-2xl p-6 text-center">
                <div className="mb-2 text-3xl font-extrabold gradient-text">{s.value}</div>
                <div className="text-sm text-gray-400">{s.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative py-20">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold md:text-4xl">Fonctionnalités <span className="gradient-text">Complètes</span></h2>
            <p className="mx-auto max-w-2xl text-gray-400">Une plateforme tout-en-un pour la veille électorale, combinant OSINT, analyse IA et visualisation de données.</p>
          </motion.div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => (
              <motion.div key={f.title} initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} whileHover={{ y: -8, scale: 1.02 }} className="glass group cursor-pointer rounded-2xl p-6 transition-all hover:shadow-2xl hover:shadow-blue-500/10">
                <div className={`mb-4 inline-flex rounded-xl bg-gradient-to-r ${f.color} p-3`}>
                  <f.icon size={24} className="text-white" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">{f.title}</h3>
                <p className="text-sm text-gray-400">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} className="glass rounded-3xl p-12">
            <Globe size={48} className="mx-auto mb-6 text-blue-400" />
            <h2 className="mb-4 text-3xl font-bold">Prêt à sécuriser les élections ?</h2>
            <p className="mx-auto mb-8 max-w-lg text-gray-400">Commencez dès maintenant à surveiller l&apos;espace public marocain et à générer des rapports stratégiques.</p>
            <Link href="/dashboard"><Button size="lg">Commencer maintenant <ArrowRight size={18} /></Button></Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8">
        <div className="mx-auto max-w-6xl px-6 text-center text-sm text-gray-500">
          © 2026 VeilleMaroc — Plateforme de Veille Électorale. Tous droits réservés.
        </div>
      </footer>
    </div>
  );
}
