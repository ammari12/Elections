"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, Image, Film, Music, X, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { useState, useCallback } from "react";

interface UploadedFile {
  id: string;
  name: string;
  type: string;
  size: number;
  status: "uploading" | "processing" | "complete" | "error";
  progress: number;
  highlights?: string[];
}

const mockFiles: UploadedFile[] = [
  { id: "1", name: "rapport-terrain-casablanca.pdf", type: "pdf", size: 2400000, status: "complete", progress: 100, highlights: ["3 mentions de tensions dans le quartier Hay Mohammadi", "Signalement de tracts anonymes anti-PAM"] },
  { id: "2", name: "communique-pjd-juin2026.docx", type: "docx", size: 180000, status: "complete", progress: 100, highlights: ["Annonce d'un rassemblement à Rabat le 15 juillet", "Critique directe du bilan gouvernemental RNI"] },
  { id: "3", name: "temoignage-audio-fes.mp3", type: "audio", size: 5600000, status: "processing", progress: 65 },
  { id: "4", name: "photo-affichage-illegal.jpg", type: "image", size: 3200000, status: "complete", progress: 100, highlights: ["Affichage de propagande non autorisé détecté", "Localisation: Marrakech, avenue Mohammed V"] },
];

const fileIcons: Record<string, any> = { pdf: FileText, docx: FileText, image: Image, audio: Music, video: Film };

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>(mockFiles);
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const newFiles: UploadedFile[] = Array.from(e.dataTransfer.files).map((f, i) => ({
      id: `new-${Date.now()}-${i}`,
      name: f.name,
      type: f.type.split("/")[0] || "pdf",
      size: f.size,
      status: "uploading" as const,
      progress: 0,
    }));
    setFiles((prev) => [...newFiles, ...prev]);
  }, []);

  const statusIcons = { uploading: Clock, processing: AlertCircle, complete: CheckCircle, error: X };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Upload className="text-amber-400" /> Upload Intelligent</h1>
          <p className="text-sm text-gray-400">Importez des documents pour analyse automatique (PDF, DOCX, images, vidéos, audio)</p>
        </motion.div>

        {/* Drop Zone */}
        <motion.div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          animate={dragging ? { scale: 1.02, borderColor: "rgba(59,130,246,0.5)" } : { scale: 1 }}
          className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/10 bg-white/[0.02] p-12 transition-colors hover:border-blue-500/30 hover:bg-white/[0.04] cursor-pointer"
        >
          <motion.div animate={dragging ? { y: -10 } : { y: 0 }} className="mb-4 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 p-4">
            <Upload size={32} className="text-blue-400" />
          </motion.div>
          <h3 className="mb-2 text-lg font-semibold">Glissez vos fichiers ici</h3>
          <p className="mb-4 text-sm text-gray-400">PDF, DOCX, TXT, CSV, Excel, Images, Vidéos, Audio</p>
          <Button variant="secondary" size="sm">Ou parcourir vos fichiers</Button>
        </motion.div>

        {/* Files List */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Documents traités ({files.length})</h3>
          <AnimatePresence>
            {files.map((file, i) => {
              const Icon = fileIcons[file.type] || FileText;
              const StatusIcon = statusIcons[file.status];
              return (
                <motion.div key={file.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -100 }} transition={{ delay: i * 0.05 }}>
                  <GlassCard className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="rounded-xl bg-white/5 p-3">
                        <Icon size={24} className="text-blue-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-sm truncate">{file.name}</span>
                          <Badge variant={file.status === "complete" ? "low" : file.status === "error" ? "critical" : "info"}>
                            <StatusIcon size={12} /> {file.status === "complete" ? "Terminé" : file.status === "processing" ? "Traitement" : file.status === "uploading" ? "Upload" : "Erreur"}
                          </Badge>
                        </div>
                        <div className="text-xs text-gray-500 mb-2">{(file.size / 1000000).toFixed(1)} Mo</div>

                        {file.status !== "complete" && <ProgressBar value={file.progress} color={file.status === "error" ? "from-red-500 to-red-400" : "from-blue-500 to-purple-500"} />}

                        {file.highlights && (
                          <div className="mt-3 space-y-1.5 rounded-xl bg-white/[0.03] p-3">
                            <div className="text-xs font-medium text-gray-300 mb-1">Faits saillants extraits :</div>
                            {file.highlights.map((h, j) => (
                              <div key={j} className="flex items-start gap-2 text-xs text-gray-400">
                                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                                {h}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </GlassCard>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </DashboardLayout>
  );
}
