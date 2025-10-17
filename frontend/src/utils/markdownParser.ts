import { TextRun } from "docx";

/**
 * Parse inline markdown formatting (bold, italic, code) and convert to TextRun objects
 * @param text - The text string with markdown formatting
 * @returns Array of TextRun objects with appropriate formatting
 */
export function parseInlineFormatting(text: string): TextRun[] {
  const textRuns: TextRun[] = [];
  let currentText = "";
  let i = 0;

  while (i < text.length) {
    // Inline code `code`
    if (text[i] === "`" && text.indexOf("`", i + 1) !== -1) {
      if (currentText) {
        textRuns.push(new TextRun({ text: currentText }));
        currentText = "";
      }
      const endIndex = text.indexOf("`", i + 1);
      const codeText = text.substring(i + 1, endIndex);
      textRuns.push(
        new TextRun({
          text: codeText,
          font: "Courier New",
          shading: { fill: "F5F5F5" }
        })
      );
      i = endIndex + 1;
    }
    // Bold **text** or __text__
    else if (
      (text[i] === "*" && text[i + 1] === "*") ||
      (text[i] === "_" && text[i + 1] === "_")
    ) {
      if (currentText) {
        textRuns.push(new TextRun({ text: currentText }));
        currentText = "";
      }
      const delimiter = text[i] === "*" ? "**" : "__";
      const endIndex = text.indexOf(delimiter, i + 2);
      if (endIndex !== -1) {
        const boldText = text.substring(i + 2, endIndex);
        textRuns.push(new TextRun({ text: boldText, bold: true }));
        i = endIndex + 2;
      } else {
        currentText += text[i];
        i++;
      }
    }
    // Italic *text* or _text_
    else if (text[i] === "*" || text[i] === "_") {
      if (currentText) {
        textRuns.push(new TextRun({ text: currentText }));
        currentText = "";
      }
      const delimiter = text[i];
      const endIndex = text.indexOf(delimiter, i + 1);
      if (endIndex !== -1 && text[endIndex + 1] !== delimiter) {
        const italicText = text.substring(i + 1, endIndex);
        textRuns.push(new TextRun({ text: italicText, italics: true }));
        i = endIndex + 1;
      } else {
        currentText += text[i];
        i++;
      }
    } else {
      currentText += text[i];
      i++;
    }
  }

  if (currentText) {
    textRuns.push(new TextRun({ text: currentText }));
  }

  return textRuns.length > 0 ? textRuns : [new TextRun({ text: "" })];
}
