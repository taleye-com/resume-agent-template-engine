/**
 * Two-Column Cover Letter Template Helper
 * Port of Python TwoColumnCoverLetterTemplate generating Typst markup.
 */

import type { TemplateHelper } from "../../../engine/template-interface.js";
import { getFieldWithFallback } from "../../../utils/field-helpers.js";
import { typstEscape } from "../../../utils/typst-escape.js";
import { ValidationError } from "../../../errors/exceptions.js";
import { ErrorCode } from "../../../errors/error-codes.js";

export class TwoColumnCoverLetterHelper implements TemplateHelper {
  readonly requiredFields: string[] = ["personalInfo", "body"];
  readonly templateType: "cover_letter" = "cover_letter";

  private data: Record<string, unknown>;
  private config: Record<string, unknown>;

  constructor(
    data: Record<string, unknown>,
    config?: Record<string, unknown>,
  ) {
    this.data = data;
    this.config = config ?? {};
  }

  /**
   * Validate essential data fields for the two-column cover letter template.
   * Checks personalInfo (name, email), body exists.
   * Body can be string or string[]. Recipient if present must be object.
   */
  validateData(): void {
    // Check required top-level sections
    for (const section of this.requiredFields) {
      if (!(section in this.data) || !this.data[section]) {
        throw new ValidationError(ErrorCode.VAL001, section, {
          section: "cover letter data",
        });
      }
    }

    // Validate personalInfo has required sub-fields
    const personalInfo = this.data.personalInfo as Record<string, unknown>;
    if (!personalInfo || typeof personalInfo !== "object") {
      throw new ValidationError(ErrorCode.VAL002, "personalInfo", {
        expected_type: "object",
        actual_type: typeof personalInfo,
      });
    }

    for (const field of ["name", "email"]) {
      if (!(field in personalInfo) || !personalInfo[field]) {
        throw new ValidationError(ErrorCode.VAL001, `personalInfo.${field}`, {
          section: "personalInfo",
        });
      }
    }

    // Body can be string or string[]
    const body = this.data.body;
    if (typeof body !== "string" && !Array.isArray(body)) {
      throw new ValidationError(ErrorCode.VAL002, "body", {
        expected_type: "string or array",
        actual_type: typeof body,
      });
    }

    // Recipient if present must be an object
    if ("recipient" in this.data && this.data.recipient != null) {
      if (
        typeof this.data.recipient !== "object" ||
        Array.isArray(this.data.recipient)
      ) {
        throw new ValidationError(ErrorCode.VAL002, "recipient", {
          expected_type: "object",
          actual_type: Array.isArray(this.data.recipient)
            ? "array"
            : typeof this.data.recipient,
        });
      }
    }
  }

  /**
   * Generate the header block with blue bold name, centered.
   */
  generatePersonalInfo(): string {
    const info = this.data.personalInfo as Record<string, unknown>;
    const name = typstEscape(String(info.name ?? ""));

    return `#text(size: 20pt, weight: "bold", fill: rgb(0, 79, 144))[${name}]
  #v(3pt)`;
  }

  /**
   * Generate sidebar contact information block.
   * Styled with white text on dark background (same as two-column resume sidebar).
   */
  generateSidebarContact(): string {
    const info = this.data.personalInfo as Record<string, unknown>;
    if (!info) return "";

    const sections: string[] = [];

    // Contact section header
    sections.push(
      `#text(size: 12pt, weight: "bold")[#upper[Contact]]`,
    );
    sections.push(`#v(0.2cm)`);
    sections.push(`#line(length: 100%, stroke: 0.5pt + white)`);
    sections.push(`#v(0.3cm)`);

    // Email
    const email = getFieldWithFallback<string>(info, "email");
    if (email) {
      sections.push(
        `#text(weight: "bold", size: 8pt)[Email] \\
#link("mailto:${email}")[#text(size: 8pt)[${typstEscape(email)}]]`,
      );
      sections.push(`#v(0.2cm)`);
    }

    // Phone
    const phone = getFieldWithFallback<string>(info, "phone");
    if (phone) {
      sections.push(
        `#text(weight: "bold", size: 8pt)[Phone] \\
#link("tel:${phone}")[#text(size: 8pt)[${typstEscape(phone)}]]`,
      );
      sections.push(`#v(0.2cm)`);
    }

    // Location
    const location = getFieldWithFallback<string>(info, "location");
    if (location) {
      sections.push(
        `#text(weight: "bold", size: 8pt)[Location] \\
#text(size: 8pt)[${typstEscape(location)}]`,
      );
      sections.push(`#v(0.2cm)`);
    }

    // Website
    const website = getFieldWithFallback<string>(info, "website");
    const websiteDisplay = getFieldWithFallback<string>(
      info,
      "website_display",
      ["websiteDisplay"],
    );
    if (website && websiteDisplay) {
      sections.push(
        `#text(weight: "bold", size: 8pt)[Website] \\
#link("${website}")[#text(size: 8pt)[${typstEscape(websiteDisplay)}]]`,
      );
      sections.push(`#v(0.2cm)`);
    }

    // LinkedIn
    const linkedin = getFieldWithFallback<string>(info, "linkedin");
    const linkedinDisplay = getFieldWithFallback<string>(
      info,
      "linkedin_display",
      ["linkedinDisplay"],
    );
    if (linkedin && linkedinDisplay) {
      sections.push(
        `#text(weight: "bold", size: 8pt)[LinkedIn] \\
#link("${linkedin}")[#text(size: 8pt)[${typstEscape(linkedinDisplay)}]]`,
      );
      sections.push(`#v(0.2cm)`);
    }

    // GitHub
    const github = getFieldWithFallback<string>(info, "github");
    const githubDisplay = getFieldWithFallback<string>(
      info,
      "github_display",
      ["githubDisplay"],
    );
    if (github && githubDisplay) {
      sections.push(
        `#text(weight: "bold", size: 8pt)[GitHub] \\
#link("${github}")[#text(size: 8pt)[${typstEscape(githubDisplay)}]]`,
      );
      sections.push(`#v(0.2cm)`);
    }

    // Twitter/X
    const twitter = getFieldWithFallback<string>(info, "twitter");
    const twitterDisplay = getFieldWithFallback<string>(
      info,
      "twitter_display",
      ["twitterDisplay"],
    );
    if (twitter && twitterDisplay) {
      sections.push(
        `#text(weight: "bold", size: 8pt)[Twitter] \\
#link("${twitter}")[#text(size: 8pt)[${typstEscape(twitterDisplay)}]]`,
      );
      sections.push(`#v(0.2cm)`);
    }

    const x = getFieldWithFallback<string>(info, "x");
    const xDisplay = getFieldWithFallback<string>(info, "x_display", [
      "xDisplay",
    ]);
    if (x && xDisplay) {
      sections.push(
        `#text(weight: "bold", size: 8pt)[X] \\
#link("${x}")[#text(size: 8pt)[${typstEscape(xDisplay)}]]`,
      );
      sections.push(`#v(0.2cm)`);
    }

    return sections.join("\n    ");
  }

  /**
   * Generate recipient address block.
   * Includes name, title, company, department, and address lines.
   */
  generateRecipientAddress(): string {
    if (!this.data.recipient) {
      return "";
    }

    const recipient = this.data.recipient as Record<string, unknown>;
    const lines: string[] = [];

    if (recipient.name) {
      lines.push(typstEscape(String(recipient.name)));
    }
    if (recipient.title) {
      lines.push(typstEscape(String(recipient.title)));
    }
    if (recipient.company) {
      lines.push(typstEscape(String(recipient.company)));
    }
    if (recipient.department) {
      lines.push(typstEscape(String(recipient.department)));
    }

    // Handle different address formats
    if (recipient.address) {
      const address = recipient.address;
      if (Array.isArray(address)) {
        for (const line of address) {
          if (line) lines.push(typstEscape(String(line)));
        }
      } else if (typeof address === "string") {
        lines.push(typstEscape(address));
      }
    }

    // Structured address components
    const addressComponents: string[] = [];
    if (recipient.street) {
      addressComponents.push(typstEscape(String(recipient.street)));
    }

    const cityStateParts: string[] = [];
    if (recipient.city) cityStateParts.push(String(recipient.city));
    if (recipient.state) cityStateParts.push(String(recipient.state));
    if (recipient.zip) cityStateParts.push(String(recipient.zip));
    if (cityStateParts.length > 0) {
      addressComponents.push(typstEscape(cityStateParts.join(", ")));
    }

    if (recipient.country) {
      addressComponents.push(typstEscape(String(recipient.country)));
    }

    lines.push(...addressComponents);

    if (lines.length === 0) {
      return "";
    }

    return lines.join(" \\\n      ");
  }

  /**
   * Generate the date string. Uses provided date or auto-generates current date.
   */
  generateDate(): string {
    const date = getFieldWithFallback<string>(
      this.data,
      "date",
      [],
      "",
    );
    if (date) {
      return typstEscape(date);
    }

    // Auto-generate current date
    const now = new Date();
    const formatted = now.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    return typstEscape(formatted);
  }

  /**
   * Generate the salutation. Uses provided salutation or smart default based on recipient.
   */
  generateSalutation(): string {
    const salutation = getFieldWithFallback<string>(
      this.data,
      "salutation",
      [],
      "",
    );
    if (salutation) {
      return typstEscape(salutation);
    }

    // Smart default based on recipient
    const recipient = (this.data.recipient ?? {}) as Record<string, unknown>;
    if (recipient.name) {
      return typstEscape(`Dear ${String(recipient.name)},`);
    }
    if (recipient.title) {
      return typstEscape(`Dear ${String(recipient.title)},`);
    }
    if (recipient.company) {
      return typstEscape(
        `Dear Hiring Manager at ${String(recipient.company)},`,
      );
    }
    return typstEscape("Dear Hiring Manager,");
  }

  /**
   * Generate the body content. Supports string or array of paragraphs.
   */
  generateBodyContent(): string {
    const body = this.data.body;

    if (typeof body === "string") {
      return typstEscape(body);
    }

    if (Array.isArray(body)) {
      return body
        .filter((paragraph) => paragraph)
        .map((paragraph) => typstEscape(String(paragraph)))
        .join("\n\n      ");
    }

    return typstEscape(String(body));
  }

  /**
   * Generate the closing line. Uses provided closing or defaults to "Sincerely,".
   */
  generateClosing(): string {
    const closing = getFieldWithFallback<string>(
      this.data,
      "closing",
      [],
      "",
    );
    if (closing) {
      return typstEscape(closing);
    }
    return typstEscape("Sincerely,");
  }

  /**
   * Render the complete two-column cover letter as a Typst document.
   */
  render(): string {
    const info = this.data.personalInfo as Record<string, unknown>;
    const name = typstEscape(String(info.name ?? ""));

    const personalInfoBlock = this.generatePersonalInfo();
    const sidebarContact = this.generateSidebarContact();
    const recipientAddress = this.generateRecipientAddress();
    const date = this.generateDate();
    const salutation = this.generateSalutation();
    const bodyContent = this.generateBodyContent();
    const closing = this.generateClosing();

    // Build main content column
    const mainContentParts: string[] = [];

    // Recipient address
    if (recipientAddress) {
      mainContentParts.push(`      ${recipientAddress}`);
      mainContentParts.push(`      #v(0.3cm)`);
    }

    // Date
    mainContentParts.push(`      #align(right)[${date}]`);
    mainContentParts.push(`      #v(0.3cm)`);

    // Salutation
    mainContentParts.push(`      ${salutation}`);
    mainContentParts.push(`      #v(0.3cm)`);

    // Body
    mainContentParts.push(`      ${bodyContent}`);

    // Closing and signature
    mainContentParts.push(`      #v(0.5cm)`);
    mainContentParts.push(`      #align(left)[
        ${closing} \\
        #v(0.2cm)
        ${name}
      ]`);

    const mainContent = mainContentParts.join("\n");

    const parts: string[] = [];

    // Page and text setup
    parts.push(
      `#set page(paper: "us-letter", margin: (top: 0.8cm, bottom: 0.8cm, left: 0.8cm, right: 0.8cm))`,
    );
    parts.push(`#set text(font: "Charter", size: 10pt)`);
    parts.push("");

    // Header (centered name in blue)
    parts.push(`// Header`);
    parts.push(`#align(center)[
  ${personalInfoBlock}
]`);
    parts.push(`#v(0.3cm)`);
    parts.push("");

    // Two-column layout
    parts.push(`// Two-column layout`);
    parts.push(`#grid(
  columns: (30%, 1fr),
  gutter: 2%,
  // Sidebar
  rect(fill: rgb(45, 55, 72), width: 100%, inset: 0.3cm, radius: 2pt)[
    #set text(fill: white, size: 9pt)
    ${sidebarContact}
  ],
  // Main content
  [
    #set par(justify: false, leading: 0.65em)
${mainContent}
  ]
)`);

    return parts.join("\n");
  }
}
