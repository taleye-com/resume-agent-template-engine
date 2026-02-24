/**
 * DOCX Generator — creates Word documents from resume/cover letter data.
 * Uses the `docx` npm package. This is a separate code path from Typst (no WASM needed).
 */

import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  BorderStyle,
  SectionType,
  TabStopPosition,
  TabStopType,
  ExternalHyperlink,
} from "docx";
import { getFieldWithFallback } from "../utils/field-helpers.js";

export interface DocxResult {
  docxBytes: Uint8Array;
  filename: string;
}

export async function generateDocx(
  documentType: string,
  data: Record<string, unknown>,
): Promise<DocxResult> {
  const doc = documentType === "cover_letter"
    ? buildCoverLetterDoc(data)
    : buildResumeDoc(data);

  const buffer = await Packer.toBuffer(doc);
  const bytes = new Uint8Array(buffer);

  const personName = (
    (data.personalInfo as Record<string, unknown>)?.name as string ?? "output"
  ).replace(/\s+/g, "_");
  const filename = `${documentType}_${personName}.docx`;

  return { docxBytes: bytes, filename };
}

function buildResumeDoc(data: Record<string, unknown>): Document {
  const personalInfo = (data.personalInfo ?? {}) as Record<string, unknown>;
  const children: Paragraph[] = [];

  // Name header
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [
        new TextRun({
          text: String(personalInfo.name ?? ""),
          bold: true,
          size: 32, // 16pt
          font: "Calibri",
        }),
      ],
    }),
  );

  // Contact info line
  const contactParts: string[] = [];
  if (personalInfo.email) contactParts.push(String(personalInfo.email));
  if (personalInfo.phone) contactParts.push(String(personalInfo.phone));
  if (personalInfo.location) contactParts.push(String(personalInfo.location));
  if (contactParts.length > 0) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [
          new TextRun({
            text: contactParts.join(" | "),
            size: 20, // 10pt
            font: "Calibri",
          }),
        ],
      }),
    );
  }

  // Professional Summary
  const summary = data.professionalSummary as string | undefined;
  if (summary) {
    children.push(sectionHeader("PROFESSIONAL SUMMARY"));
    children.push(
      new Paragraph({
        spacing: { after: 200 },
        children: [new TextRun({ text: summary, size: 20, font: "Calibri" })],
      }),
    );
  }

  // Experience
  const experience = data.experience as unknown[] | undefined;
  if (experience && experience.length > 0) {
    children.push(sectionHeader("EXPERIENCE"));
    for (const entry of experience) {
      const exp = entry as Record<string, unknown>;
      const title = String(
        getFieldWithFallback<string>(exp, "title", ["position", "role"], "Position"),
      );
      const company = String(
        getFieldWithFallback<string>(exp, "company", ["employer", "organization"], "Company"),
      );
      const location = String(exp.location ?? "");
      const startDate = String(exp.startDate ?? "");
      const endDate = String(
        getFieldWithFallback<string>(exp, "endDate", ["end_date"], "Present"),
      );
      const dateRange = startDate ? `${startDate} - ${endDate}` : endDate;

      // Title + date
      children.push(
        new Paragraph({
          spacing: { before: 100 },
          children: [
            new TextRun({ text: title, bold: true, size: 22, font: "Calibri" }),
            new TextRun({ text: `\t${dateRange}`, italics: true, size: 20, font: "Calibri" }),
          ],
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        }),
      );
      // Company + location
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: company, italics: true, size: 20, font: "Calibri" }),
            ...(location
              ? [new TextRun({ text: `\t${location}`, size: 20, font: "Calibri" })]
              : []),
          ],
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        }),
      );

      // Achievements as bullets
      const achievements = getFieldWithFallback<unknown[]>(
        exp, "achievements", ["details", "responsibilities"], [],
      );
      if (Array.isArray(achievements)) {
        for (const achievement of achievements) {
          children.push(
            new Paragraph({
              bullet: { level: 0 },
              children: [
                new TextRun({ text: String(achievement), size: 20, font: "Calibri" }),
              ],
            }),
          );
        }
      }
    }
  }

  // Education
  const education = data.education as unknown[] | undefined;
  if (education && education.length > 0) {
    children.push(sectionHeader("EDUCATION"));
    for (const entry of education) {
      const edu = entry as Record<string, unknown>;
      const degree = String(
        getFieldWithFallback<string>(edu, "degree", ["title", "qualification"], "Degree"),
      );
      const institution = String(
        getFieldWithFallback<string>(edu, "institution", ["school", "university"], "Institution"),
      );
      const gradDate = String(
        getFieldWithFallback<string>(edu, "graduationDate", ["endDate", "end_date", "date"], ""),
      );
      const gpa = String(edu.gpa ?? "");

      children.push(
        new Paragraph({
          spacing: { before: 100 },
          children: [
            new TextRun({ text: degree, bold: true, size: 22, font: "Calibri" }),
            ...(gradDate
              ? [new TextRun({ text: `\t${gradDate}`, italics: true, size: 20, font: "Calibri" })]
              : []),
          ],
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        }),
      );
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: institution, italics: true, size: 20, font: "Calibri" }),
            ...(gpa
              ? [new TextRun({ text: ` | GPA: ${gpa}`, size: 20, font: "Calibri" })]
              : []),
          ],
        }),
      );
    }
  }

  // Skills
  const skills = getFieldWithFallback<unknown>(data, "skills", ["technologiesAndSkills", "technologies"], undefined);
  if (skills) {
    children.push(sectionHeader("SKILLS"));
    if (typeof skills === "object" && !Array.isArray(skills) && skills !== null) {
      const dict = skills as Record<string, unknown>;
      for (const [category, skillList] of Object.entries(dict)) {
        if (Array.isArray(skillList) && skillList.length > 0) {
          const catName = category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
          children.push(
            new Paragraph({
              children: [
                new TextRun({ text: `${catName}: `, bold: true, size: 20, font: "Calibri" }),
                new TextRun({ text: skillList.join(", "), size: 20, font: "Calibri" }),
              ],
            }),
          );
        }
      }
    } else if (Array.isArray(skills)) {
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: (skills as string[]).join(", "), size: 20, font: "Calibri" }),
          ],
        }),
      );
    }
  }

  return new Document({
    sections: [{ children }],
  });
}

function buildCoverLetterDoc(data: Record<string, unknown>): Document {
  const personalInfo = (data.personalInfo ?? {}) as Record<string, unknown>;
  const recipient = (data.recipient ?? {}) as Record<string, unknown>;
  const children: Paragraph[] = [];

  // Sender info header
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 50 },
      children: [
        new TextRun({
          text: String(personalInfo.name ?? ""),
          bold: true,
          size: 28,
          font: "Calibri",
        }),
      ],
    }),
  );

  const contactParts: string[] = [];
  if (personalInfo.email) contactParts.push(String(personalInfo.email));
  if (personalInfo.phone) contactParts.push(String(personalInfo.phone));
  if (personalInfo.location) contactParts.push(String(personalInfo.location));
  if (contactParts.length > 0) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 300 },
        children: [
          new TextRun({ text: contactParts.join(" | "), size: 20, font: "Calibri" }),
        ],
      }),
    );
  }

  // Recipient address
  if (recipient.name || recipient.company) {
    const recipientLines: string[] = [];
    if (recipient.name) recipientLines.push(String(recipient.name));
    if (recipient.title) recipientLines.push(String(recipient.title));
    if (recipient.company) recipientLines.push(String(recipient.company));

    for (const line of recipientLines) {
      children.push(
        new Paragraph({
          spacing: { after: 50 },
          children: [new TextRun({ text: line, size: 20, font: "Calibri" })],
        }),
      );
    }
    children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));
  }

  // Date
  const dateStr = (data.date as string) ||
    new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  children.push(
    new Paragraph({
      spacing: { after: 200 },
      children: [new TextRun({ text: dateStr, size: 20, font: "Calibri" })],
    }),
  );

  // Salutation
  let salutation = data.salutation as string | undefined;
  if (!salutation) {
    if (recipient.name) salutation = `Dear ${String(recipient.name)},`;
    else if (recipient.title) salutation = `Dear ${String(recipient.title)},`;
    else if (recipient.company) salutation = `Dear Hiring Manager at ${String(recipient.company)},`;
    else salutation = "Dear Hiring Manager,";
  }
  children.push(
    new Paragraph({
      spacing: { after: 200 },
      children: [new TextRun({ text: salutation, size: 20, font: "Calibri" })],
    }),
  );

  // Body
  const body = data.body;
  const paragraphs: string[] = typeof body === "string"
    ? [body]
    : Array.isArray(body)
      ? body.map(String)
      : [String(body)];

  for (const paragraph of paragraphs) {
    children.push(
      new Paragraph({
        spacing: { after: 200 },
        children: [new TextRun({ text: paragraph, size: 20, font: "Calibri" })],
      }),
    );
  }

  // Closing
  const closing = (data.closing as string) || "Sincerely,";
  children.push(new Paragraph({ spacing: { before: 300 }, children: [] }));
  children.push(
    new Paragraph({
      children: [new TextRun({ text: closing, size: 20, font: "Calibri" })],
    }),
  );
  children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));
  children.push(
    new Paragraph({
      children: [
        new TextRun({
          text: String(personalInfo.name ?? ""),
          bold: true,
          size: 20,
          font: "Calibri",
        }),
      ],
    }),
  );

  return new Document({
    sections: [{ children }],
  });
}

function sectionHeader(title: string): Paragraph {
  return new Paragraph({
    spacing: { before: 240, after: 100 },
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
    },
    children: [
      new TextRun({
        text: title,
        bold: true,
        size: 24, // 12pt
        font: "Calibri",
      }),
    ],
  });
}
