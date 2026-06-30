"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { extractText } from "@/lib/extractText";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, Image, Film, Music, X, CheckCircle, AlertCircle, Clock, ExternalLink } from "lucide-react";
import { useState, useCallback, useRef, useEffect } from "react";

interface UploadedFile {
  id: string;
  name: string;
  type: string;
  size: number;
  status: "uploading" | "processing" | "complete" | "error";
  progress: number;
  url: string;
  highlights?: string[];
  supported?: boolean;
}

const fileIcons: Record<string, any> = { pdf: FileText, docx: FileText, txt: FileText, csv: FileText, md: FileText, image: Image, audio: Music, video: Film };

function iconKey(name: string, mimeType: string): string {
  const ext = name.split(".").pop()?.toLowerCase() || "";
  if (["pdf", "docx", "txt", "csv", "md"].includes(ext)) return ext;
  return mimeType.split("/")[0] || "pdf";
}

export default function UploadPage() {
  const { addUploadedDocument, loadFromStorage } = useAnalysisStore();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  const processFile = useCallback(async (file: File) => {
    const id = `up-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const url = URL.createObjectURL(file);
    setFiles((prev) => [{ id, name: file.name, type: iconKey(file.name, file.type), size: file.size, status: "uploading", progress: 20, url }, ...prev]);

    await new Promise((r) => setTimeout(r, 300));
    setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, status: "processing", progress: 60 } : f)));

    const { text, supported } = await extractText(file);

    if (supported && text.trim()) {
      const excerpt = text.trim().slice(0, 800);
      addUploadedDocument({ title: file.name, fileName: file.name, url, excerpt });

      const lower = text.toLowerCase();
      const highlights: string[] = [];
      const partyHit = ["rni", "pam", "istiqlal", "pjd", "usfp", "mouvement populaire", "pps", "union constitutionnelle", "fgd"].find((k) => lower.includes(k));
      if (partyHit) highlights.push(`Mention détectée d'un parti politique ("${partyHit}")`);
      const alertHit = ["désinformation", "fake news", "violence", "menace", "haine", "fraude", "corruption", "diffamation", "manipulation"].find((k) => lower.includes(k));
      if (alertHit) highlights.push(`Terme sensible détecté : "${alertHit}" — intégré au calcul des alertes`);
      if (highlights.length === 0) highlights.push("Aucun mot-clé parti/alerte détecté — document intégré aux mentions totales uniquement");

      setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, status: "complete", progress: 100, highlights, supported: true } : f)));
    } else {
      setFiles((prev) => prev.map((f) => (f.id === id ? {
        ...f, status: "complete", progress: 100, supported: false,
        highlights: ["Type de fichier non analysable automatiquement (texte non extrait) — le fichier reste consultable comme source via le lien direct."],
      } : f)));
    }
  }, [addUploadedDocument]);

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList) return;
    Array.from(fileList).forEach((f) => processFile(f));
  }, [processFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const statusIcons = { uploading: Clock, processing: AlertCircle, complete: CheckCircle, error: X };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Upload className="text-amber-400" /> Upload Intelligent</h1>
          <p className="text-sm text-gray-400">Importez des documents pour analyse automatique. Le texte est extrait localement (PDF, DOCX, TXT, CSV, MD) puis intégré au calcul des mentions, partis, alertes et cartographie des risques. Chaque document reste consultable via son lien source direct.</p>
        </motion.div>

        <input ref={inputRef} type="file" multiple className="hidden" onChange={(e) => { handleFiles(e.target.files); e.target.value = ""; }} />

        {/* Drop Zone */}
        <motion.div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          animate={dragging ? { scale: 1.02, borderColor: "rgba(59,130,246,0.5)" } : { scale: 1 }}
          className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/10 bg-white/[0.02] p-12 transition-colors hover:border-blue-500/30 hover:bg-white/[0.04] cursor-pointer"
        >
          <motion.div animate={dragging ? { y: -10 } : { y: 0 }} className="mb-4 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 p-4">
            <Upload size={32} className="text-blue-400" />
          </motion.div>
          <h3 className="mb-2 text-lg font-semibold">Glissez vos fichiers ici</h3>
          <p className="mb-4 text-sm text-gray-400">Texte extrait : PDF, DOCX, TXT, CSV, MD. Autres types (images, audio, vidéo) sont conservés comme source mais non analysés automatiquement.</p>
          <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}>Ou parcourir vos fichiers</Button>
        </motion.div>

        {/* Files List */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Documents traités ({files.length})</h3>
          {files.length === 0 && <GlassCard className="p-8 text-center text-sm text-gray-500">Aucun document importé pour le moment.</GlassCard>}
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
                          <a href={file.url} target="_blank" rel="noopener noreferrer" className="ml-auto flex items-center gap-1 text-xs text-emerald-400 hover:underline">
                            <ExternalLink size={12} /> Voir le fichier source
                          </a>
                        </div>
                        <div className="text-xs text-gray-500 mb-2">{(file.size / 1000000).toFixed(2)} Mo</div>

                        {file.status !== "complete" && <ProgressBar value={file.progress} color={file.status === "error" ? "from-red-500 to-red-400" : "from-blue-500 to-purple-500"} />}

                        {file.highlights && (
                          <div className="mt-3 space-y-1.5 rounded-xl bg-white/[0.03] p-3">
                            <div className="text-xs font-medium text-gray-300 mb-1">{file.supported === false ? "Statut" : "Faits saillants extraits :"}</div>
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
