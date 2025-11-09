import { Document, Packer, Paragraph, HeadingLevel } from "docx";
import { saveAs } from "file-saver";
import { parseInlineFormatting } from "../utils/markdownParser";
import { logger } from "../utils/logger";

interface ExportOptions {
  filename?: string;
}

export const useExport = () => {
  const exportToDocx = async (
    markdownContent: string,
    options: ExportOptions = {}
  ) => {
    const { filename = "export.docx" } = options;

    try {
      // Parse markdown into paragraphs
      const lines = markdownContent.split("\n");
      const paragraphs: Paragraph[] = [];

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Skip empty lines
        if (line.trim() === "") {
          paragraphs.push(new Paragraph({ text: "" }));
          continue;
        }

        // Headings
        if (line.startsWith("### ")) {
          paragraphs.push(
            new Paragraph({
              text: line.substring(4),
              heading: HeadingLevel.HEADING_3,
              spacing: { before: 240, after: 120 }
            })
          );
        } else if (line.startsWith("## ")) {
          paragraphs.push(
            new Paragraph({
              text: line.substring(3),
              heading: HeadingLevel.HEADING_2,
              spacing: { before: 300, after: 120 }
            })
          );
        } else if (line.startsWith("# ")) {
          paragraphs.push(
            new Paragraph({
              text: line.substring(2),
              heading: HeadingLevel.HEADING_1,
              spacing: { before: 360, after: 120 }
            })
          );
        }
        // Code blocks
        else if (line.startsWith("```")) {
          const codeLines: string[] = [];
          i++; // Skip the opening ```
          while (i < lines.length && !lines[i].startsWith("```")) {
            codeLines.push(lines[i]);
            i++;
          }
          paragraphs.push(
            new Paragraph({
              text: codeLines.join("\n"),
              shading: { fill: "F5F5F5" },
              spacing: { before: 120, after: 120 },
              indent: { left: 360 }
            })
          );
        }
        // Bullet lists
        else if (line.match(/^[*-]\s/)) {
          const text = line.substring(2);
          const textRuns = parseInlineFormatting(text);
          paragraphs.push(
            new Paragraph({
              children: textRuns,
              bullet: { level: 0 },
              spacing: { before: 60, after: 60 }
            })
          );
        }
        // Numbered lists
        else if (line.match(/^\d+\.\s/)) {
          const text = line.replace(/^\d+\.\s/, "");
          const textRuns = parseInlineFormatting(text);
          paragraphs.push(
            new Paragraph({
              children: textRuns,
              numbering: { reference: "default-numbering", level: 0 },
              spacing: { before: 60, after: 60 }
            })
          );
        }
        // Regular paragraphs
        else {
          const textRuns = parseInlineFormatting(line);
          paragraphs.push(
            new Paragraph({
              children: textRuns,
              spacing: { before: 120, after: 120 }
            })
          );
        }
      }

      // Create document
      const doc = new Document({
        sections: [
          {
            properties: {},
            children: paragraphs
          }
        ],
        numbering: {
          config: [
            {
              reference: "default-numbering",
              levels: [
                {
                  level: 0,
                  format: "decimal",
                  text: "%1.",
                  alignment: "start"
                }
              ]
            }
          ]
        }
      });

      // Generate and save the document
      const blob = await Packer.toBlob(doc);
      saveAs(blob, filename);
    } catch (error) {
      logger.error("Error exporting to DOCX:", error);
      throw error;
    }
  };

  return { exportToDocx };
};
