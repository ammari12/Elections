export interface ExtractResult {
  text: string;
  supported: boolean;
}

const TEXT_EXTENSIONS = ["txt", "md", "csv", "json", "log"];

function extOf(name: string): string {
  return name.split(".").pop()?.toLowerCase() || "";
}

export async function extractText(file: File): Promise<ExtractResult> {
  const ext = extOf(file.name);

  if (TEXT_EXTENSIONS.includes(ext)) {
    const text = await file.text();
    return { text, supported: true };
  }

  if (ext === "pdf") {
    try {
      const pdfjs = await import("pdfjs-dist");
      pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
      const buffer = await file.arrayBuffer();
      const doc = await pdfjs.getDocument({ data: buffer }).promise;
      let text = "";
      for (let i = 1; i <= doc.numPages; i++) {
        const page = await doc.getPage(i);
        const content = await page.getTextContent();
        text += content.items.map((it: any) => ("str" in it ? it.str : "")).join(" ") + "\n";
      }
      return { text, supported: true };
    } catch {
      return { text: "", supported: false };
    }
  }

  if (ext === "docx") {
    try {
      const mammoth = await import("mammoth");
      const buffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer: buffer });
      return { text: result.value, supported: true };
    } catch {
      return { text: "", supported: false };
    }
  }

  return { text: "", supported: false };
}
