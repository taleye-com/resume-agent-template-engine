import { describe, it, expect } from "vitest";
import { ClassicResumeHelper } from "../../src/templates/resume/classic/helper.js";
import { TwoColumnResumeHelper } from "../../src/templates/resume/two-column/helper.js";
import { ClassicCoverLetterHelper } from "../../src/templates/cover-letter/classic/helper.js";
import { TwoColumnCoverLetterHelper } from "../../src/templates/cover-letter/two-column/helper.js";
import {
  SAMPLE_RESUME_DATA,
  SAMPLE_COVER_LETTER_DATA,
  MINIMAL_RESUME_DATA,
} from "../fixtures/sample-data.js";

// ---------------------------------------------------------------------------
// ClassicResumeHelper
// ---------------------------------------------------------------------------

describe("ClassicResumeHelper", () => {
  it("renders full resume data to Typst", () => {
    const helper = new ClassicResumeHelper(SAMPLE_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("#set page");
    expect(output).toContain("John Doe");
    expect(output).toContain("Senior Software Engineer");
    expect(output).toContain("= Experience");
    expect(output).toContain("= Education");
  });

  it("renders minimal resume data", () => {
    const helper = new ClassicResumeHelper(MINIMAL_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("Test User");
    expect(output).toContain("#set page");
  });

  it("throws on missing personalInfo via validateData", () => {
    const helper = new ClassicResumeHelper({});
    expect(() => helper.validateData()).toThrow();
  });

  it("throws on missing name via validateData", () => {
    const helper = new ClassicResumeHelper({
      personalInfo: { email: "a@b.com" },
    });
    expect(() => helper.validateData()).toThrow();
  });

  it("throws on missing email via validateData", () => {
    const helper = new ClassicResumeHelper({
      personalInfo: { name: "Test" },
    });
    expect(() => helper.validateData()).toThrow();
  });

  it("produces analyzeDocument output with totalMetrics", () => {
    const helper = new ClassicResumeHelper(SAMPLE_RESUME_DATA);
    const analysis = helper.analyzeDocument();
    expect(analysis).toBeDefined();
    expect(analysis).toHaveProperty("totalMetrics");
    const totalMetrics = analysis.totalMetrics as Record<string, unknown>;
    expect(totalMetrics).toHaveProperty("totalWords");
    expect(totalMetrics).toHaveProperty("estimatedPages");
  });

  it("includes spacing config in rendered output", () => {
    const helper = new ClassicResumeHelper(SAMPLE_RESUME_DATA);
    const output = helper.render();
    // compact mode is the default
    expect(output).toContain("Compact Mode");
  });

  it("respects normal spacing mode", () => {
    const helper = new ClassicResumeHelper(SAMPLE_RESUME_DATA, {
      spacing_mode: "normal",
    });
    const output = helper.render();
    expect(output).toContain("Normal Mode");
  });

  it("respects ultra-compact spacing mode", () => {
    const helper = new ClassicResumeHelper(SAMPLE_RESUME_DATA, {
      spacing_mode: "ultra-compact",
    });
    const output = helper.render();
    expect(output).toContain("Ultra-Compact Mode");
  });

  it("generates professional summary section", () => {
    const helper = new ClassicResumeHelper(SAMPLE_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("Professional Summary");
    expect(output).toContain("Experienced full-stack");
  });

  it("generates certifications section for dict format", () => {
    const helper = new ClassicResumeHelper(SAMPLE_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("Certifications");
    expect(output).toContain("AWS Solutions Architect Professional");
  });

  it("generates projects section", () => {
    const helper = new ClassicResumeHelper(SAMPLE_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("Projects");
    expect(output).toContain("Open Source CLI Tool");
  });

  it("omits empty sections gracefully", () => {
    const helper = new ClassicResumeHelper(MINIMAL_RESUME_DATA);
    const output = helper.render();
    // should NOT contain section headers for empty sections
    expect(output).not.toContain("= Experience");
    expect(output).not.toContain("= Education");
    expect(output).not.toContain("= Projects");
  });

  it("exposes requiredFields and templateType", () => {
    const helper = new ClassicResumeHelper(MINIMAL_RESUME_DATA);
    expect(helper.requiredFields).toContain("personalInfo");
    expect(helper.templateType).toBe("resume");
  });
});

// ---------------------------------------------------------------------------
// TwoColumnResumeHelper
// ---------------------------------------------------------------------------

describe("TwoColumnResumeHelper", () => {
  it("renders two-column resume with grid layout", () => {
    const helper = new TwoColumnResumeHelper(SAMPLE_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("#grid(");
    expect(output).toContain("columns:");
    expect(output).toContain("John Doe");
    expect(output).toContain("rect(fill:");
  });

  it("renders minimal data without crashing", () => {
    const helper = new TwoColumnResumeHelper(MINIMAL_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("Test User");
  });

  it("throws on missing personalInfo via validateData", () => {
    const helper = new TwoColumnResumeHelper({});
    expect(() => helper.validateData()).toThrow();
  });

  it("throws on missing name via validateData", () => {
    const helper = new TwoColumnResumeHelper({
      personalInfo: { email: "a@b.com" },
    });
    expect(() => helper.validateData()).toThrow();
  });

  it("throws on missing email via validateData", () => {
    const helper = new TwoColumnResumeHelper({
      personalInfo: { name: "Test" },
    });
    expect(() => helper.validateData()).toThrow();
  });

  it("includes sidebar contact information", () => {
    const helper = new TwoColumnResumeHelper(SAMPLE_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("john.doe\\@example.com");
    expect(output).toContain("San Francisco");
  });

  it("includes experience section in main content", () => {
    const helper = new TwoColumnResumeHelper(SAMPLE_RESUME_DATA);
    const output = helper.render();
    expect(output).toContain("Senior Software Engineer");
    expect(output).toContain("Tech Corp");
  });

  it("exposes requiredFields and templateType", () => {
    const helper = new TwoColumnResumeHelper(MINIMAL_RESUME_DATA);
    expect(helper.requiredFields).toContain("personalInfo");
    expect(helper.templateType).toBe("resume");
  });
});

// ---------------------------------------------------------------------------
// ClassicCoverLetterHelper
// ---------------------------------------------------------------------------

describe("ClassicCoverLetterHelper", () => {
  it("renders cover letter with body paragraphs", () => {
    const helper = new ClassicCoverLetterHelper(SAMPLE_COVER_LETTER_DATA);
    const output = helper.render();
    expect(output).toContain("#set page");
    expect(output).toContain("John Doe");
    expect(output).toContain("Jane Smith");
    expect(output).toContain("Sincerely,");
    expect(output).toContain("strong interest");
  });

  it("throws on missing body via validateData", () => {
    const helper = new ClassicCoverLetterHelper({
      personalInfo: { name: "Test", email: "t@t.com" },
    });
    expect(() => helper.validateData()).toThrow();
  });

  it("throws on missing personalInfo via validateData", () => {
    const helper = new ClassicCoverLetterHelper({
      body: ["Some paragraph"],
    });
    expect(() => helper.validateData()).toThrow();
  });

  it("generates salutation from recipient name", () => {
    const helper = new ClassicCoverLetterHelper(SAMPLE_COVER_LETTER_DATA);
    const output = helper.render();
    expect(output).toContain("Dear Jane Smith,");
  });

  it("generates default salutation when no recipient", () => {
    const helper = new ClassicCoverLetterHelper({
      personalInfo: { name: "Test", email: "t@t.com" },
      body: "Test body paragraph.",
    });
    const output = helper.render();
    expect(output).toContain("Dear Hiring Manager,");
  });

  it("exposes requiredFields and templateType", () => {
    const helper = new ClassicCoverLetterHelper(SAMPLE_COVER_LETTER_DATA);
    expect(helper.requiredFields).toEqual(["personalInfo", "body"]);
    expect(helper.templateType).toBe("cover_letter");
  });
});

// ---------------------------------------------------------------------------
// TwoColumnCoverLetterHelper
// ---------------------------------------------------------------------------

describe("TwoColumnCoverLetterHelper", () => {
  it("renders two-column cover letter with sidebar", () => {
    const helper = new TwoColumnCoverLetterHelper(SAMPLE_COVER_LETTER_DATA);
    const output = helper.render();
    expect(output).toContain("#grid(");
    expect(output).toContain("rect(fill:");
    expect(output).toContain("John Doe");
    expect(output).toContain("Sincerely,");
  });

  it("throws on missing body via validateData", () => {
    const helper = new TwoColumnCoverLetterHelper({
      personalInfo: { name: "Test", email: "t@t.com" },
    });
    expect(() => helper.validateData()).toThrow();
  });

  it("throws on missing personalInfo via validateData", () => {
    const helper = new TwoColumnCoverLetterHelper({
      body: ["Some paragraph"],
    });
    expect(() => helper.validateData()).toThrow();
  });

  it("includes sidebar contact block", () => {
    const helper = new TwoColumnCoverLetterHelper(SAMPLE_COVER_LETTER_DATA);
    const output = helper.render();
    expect(output).toContain("Contact");
    expect(output).toContain("john.doe\\@example.com");
  });

  it("exposes requiredFields and templateType", () => {
    const helper = new TwoColumnCoverLetterHelper(SAMPLE_COVER_LETTER_DATA);
    expect(helper.requiredFields).toEqual(["personalInfo", "body"]);
    expect(helper.templateType).toBe("cover_letter");
  });
});
