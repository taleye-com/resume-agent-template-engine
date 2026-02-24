/**
 * Two-Column Resume Template Helper
 *
 * Generates Typst markup for a two-column resume layout:
 * - Left sidebar (35%): colored background (RGB 45,55,72), white text
 *   containing contact info, skills, education, certifications.
 * - Right main content (65%): professional summary, experience,
 *   projects, achievements, publications.
 *
 * Port of the Python TwoColumnResumeTemplate (LaTeX) to Typst.
 */

import type { TemplateHelper } from "../../../engine/template-interface.js";
import { getFieldWithFallback } from "../../../utils/field-helpers.js";
import { typstEscape } from "../../../utils/typst-escape.js";
import { ValidationError } from "../../../errors/exceptions.js";
import { ErrorCode } from "../../../errors/error-codes.js";

// Color constants matching the Python template
const SIDEBAR_COLOR = "rgb(45, 55, 72)";
const PRIMARY_COLOR = "rgb(0, 79, 144)";

export class TwoColumnResumeHelper implements TemplateHelper {
  private readonly data: Record<string, unknown>;
  private readonly config: Record<string, unknown>;

  constructor(
    data: Record<string, unknown>,
    config?: Record<string, unknown>,
  ) {
    this.data = data;
    this.config = config ?? {};
  }

  // ---------------------------------------------------------------------------
  // TemplateHelper interface
  // ---------------------------------------------------------------------------

  get requiredFields(): string[] {
    return ["personalInfo"];
  }

  get templateType(): "resume" | "cover_letter" {
    return "resume";
  }

  validateData(): void {
    // Require personalInfo section
    if (!this.data.personalInfo) {
      throw new ValidationError(
        ErrorCode.VAL001,
        "personalInfo",
        { section: "resume data" },
      );
    }

    const personalInfo = this.data.personalInfo as Record<string, unknown>;

    // Require name
    if (!personalInfo.name) {
      throw new ValidationError(
        ErrorCode.VAL001,
        "personalInfo.name",
        { section: "personalInfo" },
      );
    }

    // Require email
    if (!personalInfo.email) {
      throw new ValidationError(
        ErrorCode.VAL001,
        "personalInfo.email",
        { section: "personalInfo" },
      );
    }
  }

  render(): string {
    this.validateData();

    const personalInfo = this.generatePersonalInfo();
    const sidebarContact = this.generateSidebarContact();
    const sidebarSkills = this.generateSidebarSkills();
    const sidebarEducation = this.generateSidebarEducation();
    const sidebarCertifications = this.generateSidebarCertifications();
    const professionalSummary = this.generateProfessionalSummary();
    const experience = this.generateExperience();
    const projects = this.generateProjects();
    const achievements = this.generateAchievements();
    const publications = this.generatePublications();

    // Build sidebar content (white text on dark background)
    const sidebarSections = [
      sidebarContact,
      sidebarSkills,
      sidebarEducation,
      sidebarCertifications,
    ].filter(Boolean);

    const sidebarContent = sidebarSections.join("\n#v(0.4cm)\n");

    // Build main content sections
    const mainSections = [
      professionalSummary,
      experience,
      projects,
      achievements,
      publications,
    ].filter(Boolean);

    const mainContent = mainSections.join("\n");

    // Compose the full Typst document
    const lines: string[] = [
      `#set page(paper: "us-letter", margin: (top: 0.8cm, bottom: 0.8cm, left: 0.8cm, right: 0.8cm))`,
      `#set text(font: "Charter", size: 10pt)`,
      `#set par(justify: false)`,
      ``,
      `// Header`,
      personalInfo,
      `#v(0.3cm)`,
      ``,
      `// Two-column layout`,
      `#grid(`,
      `  columns: (35%, 1fr),`,
      `  gutter: 2%,`,
      `  // Sidebar`,
      `  rect(fill: ${SIDEBAR_COLOR}, width: 100%, inset: 0.3cm, radius: 0pt)[`,
      `    #set text(fill: white, size: 9pt)`,
      `    ${sidebarContent}`,
      `  ],`,
      `  // Main content`,
      `  [`,
      `    ${mainContent}`,
      `  ]`,
      `)`,
    ];

    return lines.join("\n");
  }

  // ---------------------------------------------------------------------------
  // Section generators
  // ---------------------------------------------------------------------------

  /** Generate centered header with name in large bold blue text. */
  generatePersonalInfo(): string {
    const info = this.data.personalInfo as Record<string, unknown>;
    const name = typstEscape(String(info.name ?? ""));

    const lines: string[] = [
      `#align(center)[`,
      `  #text(size: 20pt, weight: "bold", fill: ${PRIMARY_COLOR})[${name}]`,
      `  #v(3pt)`,
      `]`,
    ];
    return lines.join("\n");
  }

  /** Generate sidebar contact block with labeled entries. */
  generateSidebarContact(): string {
    const info = this.data.personalInfo as Record<string, unknown> | undefined;
    if (!info) return "";

    const lines: string[] = [];
    lines.push(this.sidebarSectionHeader("Contact"));

    // Email
    if (info.email) {
      const email = typstEscape(String(info.email));
      lines.push(
        `#text(weight: "bold", size: 9pt)[Email] #linebreak()`,
      );
      lines.push(
        `#link("mailto:${String(info.email)}")[${email}]`,
      );
      lines.push(`#v(0.15cm)`);
    }

    // Phone
    if (info.phone) {
      const phone = typstEscape(String(info.phone));
      lines.push(
        `#text(weight: "bold", size: 9pt)[Phone] #linebreak()`,
      );
      lines.push(
        `#link("tel:${String(info.phone)}")[${phone}]`,
      );
      lines.push(`#v(0.15cm)`);
    }

    // Location
    if (info.location) {
      const location = typstEscape(String(info.location));
      lines.push(
        `#text(weight: "bold", size: 9pt)[Location] #linebreak()`,
      );
      lines.push(location);
      lines.push(`#v(0.15cm)`);
    }

    // Website
    const websiteUrl = info.website as string | undefined;
    const websiteDisplay = (info.website_display ?? info.websiteDisplay) as string | undefined;
    if (websiteUrl && websiteDisplay) {
      lines.push(
        `#text(weight: "bold", size: 9pt)[Website] #linebreak()`,
      );
      lines.push(
        `#link("${String(websiteUrl)}")[${typstEscape(String(websiteDisplay))}]`,
      );
      lines.push(`#v(0.15cm)`);
    }

    // LinkedIn
    const linkedinUrl = info.linkedin as string | undefined;
    const linkedinDisplay = (info.linkedin_display ?? info.linkedinDisplay) as string | undefined;
    if (linkedinUrl && linkedinDisplay) {
      lines.push(
        `#text(weight: "bold", size: 9pt)[LinkedIn] #linebreak()`,
      );
      lines.push(
        `#link("${String(linkedinUrl)}")[${typstEscape(String(linkedinDisplay))}]`,
      );
      lines.push(`#v(0.15cm)`);
    }

    // GitHub
    const githubUrl = info.github as string | undefined;
    const githubDisplay = (info.github_display ?? info.githubDisplay) as string | undefined;
    if (githubUrl && githubDisplay) {
      lines.push(
        `#text(weight: "bold", size: 9pt)[GitHub] #linebreak()`,
      );
      lines.push(
        `#link("${String(githubUrl)}")[${typstEscape(String(githubDisplay))}]`,
      );
      lines.push(`#v(0.15cm)`);
    }

    return lines.join("\n");
  }

  /** Generate sidebar skills grouped by category or as a flat list. */
  generateSidebarSkills(): string {
    const skillsData = getFieldWithFallback<unknown>(
      this.data,
      "technologiesAndSkills",
      ["skills", "technologies", "tech_skills"],
      [],
    );

    if (!skillsData || (Array.isArray(skillsData) && skillsData.length === 0)) {
      return "";
    }

    const lines: string[] = [];
    lines.push(this.sidebarSectionHeader("Skills"));

    if (Array.isArray(skillsData) && skillsData.every((s) => typeof s === "string")) {
      // Simple flat list of skill strings
      const escaped = (skillsData as string[]).map((s) => typstEscape(s));
      lines.push(escaped.join(", "));
    } else if (
      skillsData !== null &&
      typeof skillsData === "object" &&
      !Array.isArray(skillsData)
    ) {
      // Dictionary format: { "technical": [...], "soft": [...] }
      const dict = skillsData as Record<string, unknown>;
      for (const [category, skillList] of Object.entries(dict)) {
        if (Array.isArray(skillList) && skillList.length > 0) {
          const skillStrings = skillList.map((s) => typstEscape(String(s)));
          lines.push(
            `*${typstEscape(this.titleCase(category))}* #linebreak()`,
          );
          lines.push(skillStrings.join(", "));
          lines.push(`#v(0.15cm)`);
        }
      }
    } else if (Array.isArray(skillsData)) {
      // Structured list: [{ category: "...", skills: [...] }, ...]
      for (const skillGroup of skillsData) {
        if (skillGroup !== null && typeof skillGroup === "object") {
          const group = skillGroup as Record<string, unknown>;
          const category = getFieldWithFallback<string>(
            group,
            "category",
            ["name", "type"],
            "Skills",
          );
          const skillList = getFieldWithFallback<unknown[]>(
            group,
            "skills",
            ["items", "technologies"],
            [],
          );

          if (Array.isArray(skillList) && skillList.length > 0) {
            const skillStrings = skillList.map((s) => typstEscape(String(s)));
            lines.push(
              `*${typstEscape(String(category))}* #linebreak()`,
            );
            lines.push(skillStrings.join(", "));
            lines.push(`#v(0.15cm)`);
          }
        }
      }
    }

    return lines.join("\n");
  }

  /** Generate sidebar education entries in compact form. */
  generateSidebarEducation(): string {
    const education = this.data.education as unknown[] | undefined;
    if (!education || !Array.isArray(education) || education.length === 0) {
      return "";
    }

    const lines: string[] = [];
    lines.push(this.sidebarSectionHeader("Education"));

    for (const entry of education) {
      const edu = entry as Record<string, unknown>;

      const degree = typstEscape(
        String(
          getFieldWithFallback<string>(
            edu,
            "degree",
            ["title", "qualification"],
            "Degree",
          ),
        ),
      );
      const institution = typstEscape(
        String(
          getFieldWithFallback<string>(
            edu,
            "institution",
            ["school", "university", "college"],
            "Institution",
          ),
        ),
      );
      const endDate = typstEscape(
        String(
          getFieldWithFallback<string>(
            edu,
            "endDate",
            ["end_date", "date", "graduationDate"],
            "",
          ),
        ),
      );
      const focus = typstEscape(
        String(
          getFieldWithFallback<string>(
            edu,
            "focus",
            ["major", "specialization", "concentration"],
            "",
          ),
        ),
      );

      lines.push(`*${degree}* #linebreak()`);
      lines.push(`${institution} #linebreak()`);
      if (endDate) {
        lines.push(`_${endDate}_`);
        if (focus) {
          lines.push(` #linebreak()`);
        }
      }
      if (focus) {
        lines.push(`${focus}`);
      }
      lines.push(`#v(0.2cm)`);
    }

    return lines.join("\n");
  }

  /** Generate sidebar certifications in compact comma-separated format. */
  generateSidebarCertifications(): string {
    const certifications = getFieldWithFallback<unknown>(
      this.data,
      "certifications",
      ["certificates", "credentials", "licenses"],
      undefined,
    );

    if (!certifications) return "";

    // Check emptiness for arrays and objects
    if (Array.isArray(certifications) && certifications.length === 0) return "";
    if (
      typeof certifications === "object" &&
      !Array.isArray(certifications) &&
      Object.keys(certifications as Record<string, unknown>).length === 0
    ) {
      return "";
    }

    const lines: string[] = [];
    lines.push(this.sidebarSectionHeader("Certifications"));

    if (
      certifications !== null &&
      typeof certifications === "object" &&
      !Array.isArray(certifications)
    ) {
      // Dictionary format: { "ai_ml": [...], "cloud": [...] }
      const dict = certifications as Record<string, unknown>;
      for (const [categoryKey, items] of Object.entries(dict)) {
        if (!Array.isArray(items) || items.length === 0) continue;

        const categoryName = typstEscape(this.formatCategoryName(categoryKey));
        const certNames = items.map((cert) => {
          const [, cleanName] = this.extractCertIcon(String(cert));
          return typstEscape(cleanName);
        });

        lines.push(`*${categoryName}:* ${certNames.join(", ")}`);
        lines.push(`#v(0.15cm)`);
      }
    } else if (Array.isArray(certifications)) {
      if (
        certifications.length > 0 &&
        certifications[0] !== null &&
        typeof certifications[0] === "object"
      ) {
        // Structured list: [{ category: "AI", items: [...] }, ...]
        for (const certGroup of certifications) {
          const group = certGroup as Record<string, unknown>;
          const category = group.category as string | undefined;
          const items = group.items as unknown[] | undefined;

          if (!items || items.length === 0) continue;

          const certNames = items.map((cert) => {
            const [, cleanName] = this.extractCertIcon(String(cert));
            return typstEscape(cleanName);
          });

          if (category) {
            lines.push(
              `*${typstEscape(String(category))}:* ${certNames.join(", ")}`,
            );
          } else {
            lines.push(certNames.join(", "));
          }
          lines.push(`#v(0.15cm)`);
        }
      } else {
        // Flat list of certification strings
        const certNames = (certifications as unknown[]).map((cert) => {
          const [, cleanName] = this.extractCertIcon(String(cert));
          return typstEscape(cleanName);
        });
        lines.push(certNames.join(", "));
      }
    }

    return lines.join("\n");
  }

  /** Generate professional summary with main section heading. */
  generateProfessionalSummary(): string {
    const summary = this.data.professionalSummary as string | undefined;
    if (!summary) return "";

    const lines: string[] = [];
    lines.push(this.mainSectionHeader("Professional Summary"));
    lines.push(typstEscape(String(summary)));
    lines.push(`#v(0.3cm)`);

    return lines.join("\n");
  }

  /** Generate experience section with title, dates, company, location, and achievements. */
  generateExperience(): string {
    const experience = this.data.experience as unknown[] | undefined;
    if (!experience || !Array.isArray(experience) || experience.length === 0) {
      return "";
    }

    const lines: string[] = [];
    lines.push(this.mainSectionHeader("Experience"));

    for (const entry of experience) {
      const exp = entry as Record<string, unknown>;

      const title = typstEscape(
        String(
          getFieldWithFallback<string>(
            exp,
            "title",
            ["position", "role"],
            "Position",
          ),
        ),
      );
      const company = typstEscape(
        String(
          getFieldWithFallback<string>(
            exp,
            "company",
            ["employer", "organization"],
            "Company",
          ),
        ),
      );
      const location = typstEscape(String(exp.location ?? ""));
      const startDate = String(exp.startDate ?? "");
      const endDate = String(
        getFieldWithFallback<string>(exp, "endDate", ["end_date"], "Present"),
      );

      const dateRange = startDate
        ? `${typstEscape(startDate)} - ${typstEscape(endDate)}`
        : typstEscape(endDate);

      const achievements = getFieldWithFallback<unknown[]>(
        exp,
        "achievements",
        ["details", "responsibilities", "duties"],
        [],
      );

      // Title and date on same line
      lines.push(
        `#grid(columns: (1fr, auto), align: (left, right), [*${title}*], [_${dateRange}_])`,
      );
      // Company and location
      if (location) {
        lines.push(
          `#grid(columns: (1fr, auto), align: (left, right), [_${company}_], [${location}])`,
        );
      } else {
        lines.push(`_${company}_`);
      }

      // Achievement bullets
      if (Array.isArray(achievements) && achievements.length > 0) {
        lines.push(`#v(0.1cm)`);
        for (const achievement of achievements) {
          lines.push(`- ${typstEscape(String(achievement))}`);
        }
      }

      lines.push(`#v(0.25cm)`);
    }

    return lines.join("\n");
  }

  /** Generate projects section with name, description, and technologies. */
  generateProjects(): string {
    const projects = this.data.projects as unknown[] | undefined;
    if (!projects || !Array.isArray(projects) || projects.length === 0) {
      return "";
    }

    const lines: string[] = [];
    lines.push(this.mainSectionHeader("Projects"));

    for (const entry of projects) {
      const proj = entry as Record<string, unknown>;

      const name = typstEscape(
        String(
          getFieldWithFallback<string>(
            proj,
            "name",
            ["title", "project_name"],
            "Project",
          ),
        ),
      );
      const description = typstEscape(
        String(
          getFieldWithFallback<string>(
            proj,
            "description",
            ["summary", "desc"],
            "",
          ),
        ),
      );
      const tools = getFieldWithFallback<unknown[]>(
        proj,
        "tools",
        ["technologies", "tech_stack", "stack"],
        [],
      );

      lines.push(`*${name}*`);
      if (description) {
        lines.push(` #linebreak()`);
        lines.push(description);
      }
      if (Array.isArray(tools) && tools.length > 0) {
        const toolStrings = tools.map((t) => typstEscape(String(t)));
        lines.push(` #linebreak()`);
        lines.push(`_Technologies: ${toolStrings.join(", ")}_`);
      }
      lines.push(`#v(0.2cm)`);
    }

    return lines.join("\n");
  }

  /** Generate achievements section as a bullet list. */
  generateAchievements(): string {
    const achievements = getFieldWithFallback<unknown[]>(
      this.data,
      "achievements",
      ["accomplishments", "awards", "honors"],
      [],
    );

    if (!Array.isArray(achievements) || achievements.length === 0) {
      return "";
    }

    const lines: string[] = [];
    lines.push(this.mainSectionHeader("Achievements"));

    for (const achievement of achievements) {
      lines.push(`- ${typstEscape(String(achievement))}`);
    }

    lines.push(`#v(0.3cm)`);
    return lines.join("\n");
  }

  /** Generate publications section with title and date. */
  generatePublications(): string {
    const publications = getFieldWithFallback<unknown[]>(
      this.data,
      "articlesAndPublications",
      ["publications", "articles", "papers"],
      [],
    );

    if (!Array.isArray(publications) || publications.length === 0) {
      return "";
    }

    const lines: string[] = [];
    lines.push(this.mainSectionHeader("Publications"));

    for (const entry of publications) {
      const pub = entry as Record<string, unknown>;
      const title = typstEscape(
        String(getFieldWithFallback<string>(pub, "title", ["name"], "Publication")),
      );
      const date = typstEscape(
        String(
          getFieldWithFallback<string>(
            pub,
            "date",
            ["published_date", "year"],
            "",
          ),
        ),
      );

      if (date) {
        lines.push(`- *${title}* (${date})`);
      } else {
        lines.push(`- *${title}*`);
      }
    }

    lines.push(`#v(0.3cm)`);
    return lines.join("\n");
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  /**
   * Produce a sidebar section header: bold uppercase title with a white rule.
   */
  private sidebarSectionHeader(title: string): string {
    return [
      `#text(weight: "bold", size: 12pt)[#upper[${typstEscape(title)}]]`,
      `#v(0.2cm)`,
      `#line(length: 100%, stroke: 0.5pt + white)`,
      `#v(0.2cm)`,
    ].join("\n");
  }

  /**
   * Produce a main-content section header: bold uppercase blue title with a blue rule.
   */
  private mainSectionHeader(title: string): string {
    return [
      `#text(fill: ${PRIMARY_COLOR}, weight: "bold", size: 14pt)[#upper[${typstEscape(title)}]]`,
      `#v(0.15cm)`,
      `#line(length: 100%, stroke: 0.75pt + ${PRIMARY_COLOR})`,
      `#v(0.2cm)`,
    ].join("\n");
  }

  /**
   * Extract a source icon abbreviation from certification text.
   * Returns [icon, cleanName]. Icon may be empty string if none matched.
   */
  private extractCertIcon(certText: string): [string, string] {
    const iconMap: Record<string, string> = {
      linkedin: "LI",
      hackerrank: "HR",
      workato: "WK",
      coursera: "CR",
      udemy: "UD",
      edx: "EX",
      aws: "AWS",
      google: "GG",
      microsoft: "MS",
    };

    // Check for source in parentheses
    const parenOpen = certText.lastIndexOf("(");
    const parenClose = certText.lastIndexOf(")");
    if (parenOpen !== -1 && parenClose !== -1 && parenClose > parenOpen) {
      const source = certText.substring(parenOpen + 1, parenClose).trim().toLowerCase();
      const cleanName = certText.substring(0, parenOpen).trim();
      for (const [key, icon] of Object.entries(iconMap)) {
        if (source.includes(key)) {
          return [icon, cleanName];
        }
      }
    }

    // Check for dash-separated source
    const dashIdx = certText.lastIndexOf(" - ");
    if (dashIdx !== -1) {
      const cleanName = certText.substring(0, dashIdx).trim();
      const source = certText.substring(dashIdx + 3).trim().toLowerCase();
      for (const [key, icon] of Object.entries(iconMap)) {
        if (source.includes(key)) {
          return [icon, cleanName];
        }
      }
    }

    return ["", certText];
  }

  /**
   * Format a category key like "ai_ml" into "Ai Ml" display text.
   * Matches Python's: category_key.replace("_", " ").title()
   */
  private formatCategoryName(categoryKey: string): string {
    return categoryKey
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  /** Convert a string to title case. */
  private titleCase(str: string): string {
    return str
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
}
