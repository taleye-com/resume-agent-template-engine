/**
 * Classic Resume Template Helper -- Typst markup generator.
 * TypeScript port of the Python ClassicResumeTemplate helper.
 *
 * Generates complete Typst documents from structured resume JSON data.
 */

import type { TemplateHelper } from "../../../engine/template-interface.js";
import { getFieldWithFallback } from "../../../utils/field-helpers.js";
import { typstEscape } from "../../../utils/typst-escape.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type DataObject = Record<string, unknown>;

// ---------------------------------------------------------------------------
// Helper: cast unknown to DataObject safely
// ---------------------------------------------------------------------------

function asRecord(value: unknown): DataObject {
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    return value as DataObject;
  }
  return {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asString(value: unknown): string {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  return String(value);
}

// ---------------------------------------------------------------------------
// ClassicResumeHelper
// ---------------------------------------------------------------------------

export class ClassicResumeHelper implements TemplateHelper {
  private data: DataObject;
  private config: DataObject;
  private spacingMode: string;

  constructor(data: DataObject, config?: DataObject) {
    this.data = data;
    this.config = config ?? {};
    this.spacingMode = this.getSpacingMode();
  }

  // -----------------------------------------------------------------------
  // TemplateHelper interface
  // -----------------------------------------------------------------------

  get requiredFields(): string[] {
    return ["personalInfo"];
  }

  get templateType(): "resume" {
    return "resume";
  }

  validateData(): void {
    const requiredSections = ["personalInfo"];
    for (const section of requiredSections) {
      if (!(section in this.data)) {
        throw new Error(`Missing required section: ${section}`);
      }
    }
    const info = asRecord(this.data["personalInfo"]);
    for (const field of ["name", "email"]) {
      if (!(field in info) || !info[field]) {
        throw new Error(`Missing required field: personalInfo.${field}`);
      }
    }
  }

  render(): string {
    return this.generateResume();
  }

  analyzeDocument(): Record<string, unknown> {
    return this.buildDocumentAnalysis();
  }

  // -----------------------------------------------------------------------
  // Spacing helpers
  // -----------------------------------------------------------------------

  private getSpacingMode(): string {
    if (this.config && "spacing_mode" in this.config) {
      return asString(this.config["spacing_mode"]);
    }
    if ("spacing_mode" in this.data) {
      return asString(this.data["spacing_mode"]) || "compact";
    }
    if ("spacingMode" in this.data) {
      return asString(this.data["spacingMode"]) || "compact";
    }
    return "compact";
  }

  generateSpacingConfig(): string {
    const mode = this.spacingMode.toLowerCase();

    if (mode === "compact") {
      return [
        '// Compact Mode: Optimized for 1-page resumes',
        '#set page(paper: "us-letter", margin: (top: 0.5cm, bottom: 0.5cm, left: 0.6cm, right: 0.6cm))',
        '#set text(font: "Charter", size: 10pt)',
        '#set par(justify: false, leading: 0.5em)',
      ].join("\n");
    }
    if (mode === "ultra-compact") {
      return [
        '// Ultra-Compact Mode: Maximum content density',
        '#set page(paper: "us-letter", margin: (top: 0.4cm, bottom: 0.4cm, left: 0.5cm, right: 0.5cm))',
        '#set text(font: "Charter", size: 9.5pt)',
        '#set par(justify: false, leading: 0.45em)',
      ].join("\n");
    }
    // normal
    return [
      '// Normal Mode: Standard spacing for readability',
      '#set page(paper: "us-letter", margin: (top: 0.8cm, bottom: 0.8cm, left: 0.8cm, right: 0.8cm))',
      '#set text(font: "Charter", size: 10pt)',
      '#set par(justify: false, leading: 0.6em)',
    ].join("\n");
  }

  // -----------------------------------------------------------------------
  // Section header helper
  // -----------------------------------------------------------------------

  generateSectionWithHeader(
    sectionName: string,
    contentFn: () => string,
    headerName?: string,
  ): string {
    const content = contentFn();
    if (!content) return "";
    const header =
      headerName ??
      sectionName
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
    return `= ${header}\n${content}`;
  }

  // -----------------------------------------------------------------------
  // Personal Info / Header
  // -----------------------------------------------------------------------

  generatePersonalInfo(): string {
    const info = asRecord(this.data["personalInfo"]);
    const lines: string[] = [];
    lines.push("#align(center)[");

    // Name
    const name = typstEscape(asString(info["name"]));
    lines.push(`  #text(size: 20pt, weight: "bold")[${name}]`);
    lines.push("  #v(2pt)");

    // Professional title / headline
    const title = asString(
      getFieldWithFallback<string>(
        info,
        "title",
        ["headline", "professionalTitle"],
        "",
      ),
    );
    if (title) {
      lines.push(`  #text(size: 10pt)[_${typstEscape(title)}_]`);
      lines.push("  #v(2pt)");
    }

    // Build contact parts
    const contactParts: string[] = [];

    const location = asString(info["location"]);
    if (location) {
      contactParts.push(typstEscape(location));
    }

    // Email (required)
    const email = asString(info["email"]);
    contactParts.push(`#link("mailto:${email}")[${typstEscape(email)}]`);

    const phone = asString(info["phone"]);
    if (phone) {
      contactParts.push(`#link("tel:${phone}")[${typstEscape(phone)}]`);
    }

    const website = asString(info["website"]);
    const websiteDisplay = asString(info["website_display"]);
    if (website && websiteDisplay) {
      contactParts.push(`#link("${website}")[${typstEscape(websiteDisplay)}]`);
    }

    const linkedin = asString(info["linkedin"]);
    const linkedinDisplay = asString(info["linkedin_display"]);
    if (linkedin && linkedinDisplay) {
      contactParts.push(
        `#link("${linkedin}")[${typstEscape(linkedinDisplay)}]`,
      );
    }

    const github = asString(info["github"]);
    const githubDisplay = asString(info["github_display"]);
    if (github && githubDisplay) {
      contactParts.push(`#link("${github}")[${typstEscape(githubDisplay)}]`);
    }

    const twitter = asString(info["twitter"]);
    const twitterDisplay = asString(info["twitter_display"]);
    if (twitter && twitterDisplay) {
      contactParts.push(
        `#link("${twitter}")[${typstEscape(twitterDisplay)}]`,
      );
    }

    const x = asString(info["x"]);
    const xDisplay = asString(info["x_display"]);
    if (x && xDisplay) {
      contactParts.push(`#link("${x}")[${typstEscape(xDisplay)}]`);
    }

    if (contactParts.length > 0) {
      lines.push(`  ${contactParts.join(" | ")}`);
    }

    lines.push("]");
    lines.push("#v(0.1cm)");
    return lines.join("\n");
  }

  // -----------------------------------------------------------------------
  // Professional Summary
  // -----------------------------------------------------------------------

  generateProfessionalSummary(): string {
    const summary = asString(this.data["professionalSummary"]);
    if (!summary) return "";
    return typstEscape(summary);
  }

  // -----------------------------------------------------------------------
  // Education
  // -----------------------------------------------------------------------

  generateEducation(): string {
    const education = asArray(this.data["education"]);
    if (education.length === 0) return "";

    const sections: string[] = [];
    for (const raw of education) {
      const edu = asRecord(raw);

      const degree = typstEscape(
        asString(
          getFieldWithFallback<string>(
            edu,
            "degree",
            ["title", "qualification"],
            "Degree",
          ),
        ),
      );
      let institution = asString(
        getFieldWithFallback<string>(
          edu,
          "institution",
          ["school", "university", "college"],
          "Institution",
        ),
      );
      const url = asString(edu["url"]);
      if (url) {
        institution = `#link("${url}")[${typstEscape(institution)}]`;
      } else {
        institution = typstEscape(institution);
      }

      const startDate = asString(edu["startDate"]);
      const endDate = asString(
        getFieldWithFallback<string>(
          edu,
          "endDate",
          ["end_date", "date", "graduationDate"],
          "",
        ),
      );
      let dateRange: string;
      if (startDate && endDate) {
        dateRange = `${typstEscape(startDate)} -- ${typstEscape(endDate)}`;
      } else {
        dateRange = typstEscape(endDate || startDate);
      }

      const courses = asArray(
        getFieldWithFallback<unknown[]>(
          edu,
          "notableCourseWorks",
          ["courses", "coursework", "details"],
          [],
        ),
      );
      const projects = asArray(
        getFieldWithFallback<unknown[]>(
          edu,
          "projects",
          ["academicProjects"],
          [],
        ),
      );
      const focus = asString(
        getFieldWithFallback<string>(
          edu,
          "focus",
          ["major", "specialization", "concentration"],
          "",
        ),
      );

      const entryLines: string[] = [];
      entryLines.push(
        `*${degree}* -- ${institution} #h(1fr) ${dateRange}`,
      );

      entryLines.push(`- *Focus:* ${typstEscape(focus) || "N/A"}`);
      entryLines.push(
        `- *Courses:* ${courses.length > 0 ? courses.map((c) => typstEscape(asString(c))).join(", ") : "N/A"}`,
      );
      entryLines.push(
        `- *Projects:* ${projects.length > 0 ? projects.map((p) => typstEscape(asString(p))).join(", ") : "N/A"}`,
      );

      sections.push(entryLines.join("\n"));
    }
    return sections.join("\n#v(0.3cm)\n");
  }

  // -----------------------------------------------------------------------
  // Experience
  // -----------------------------------------------------------------------

  generateExperience(): string {
    const experience = asArray(this.data["experience"]);
    if (experience.length === 0) return "";

    const sections: string[] = [];
    for (const raw of experience) {
      const exp = asRecord(raw);

      const startDate = asString(exp["startDate"]);
      const endDate = asString(
        getFieldWithFallback<string>(exp, "endDate", ["end_date"], "Present"),
      );
      const dateRange = startDate
        ? `${typstEscape(startDate)} -- ${typstEscape(endDate)}`
        : typstEscape(endDate);

      const achievements = asArray(
        getFieldWithFallback<unknown[]>(
          exp,
          "achievements",
          ["details", "responsibilities", "duties"],
          [],
        ),
      );

      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(
            exp,
            "title",
            ["position", "role"],
            "Position",
          ),
        ),
      );
      let company = asString(
        getFieldWithFallback<string>(
          exp,
          "company",
          ["employer", "organization"],
          "Company",
        ),
      );
      const url = asString(exp["url"]);
      if (url) {
        company = `#link("${url}")[${typstEscape(company)}]`;
      } else {
        company = typstEscape(company);
      }

      const entryLines: string[] = [];
      entryLines.push(`*${title}*, ${company} #h(1fr) ${dateRange}`);
      for (const ach of achievements) {
        entryLines.push(`- ${typstEscape(asString(ach))}`);
      }
      sections.push(entryLines.join("\n"));
    }
    return sections.join("\n#v(0.3cm)\n");
  }

  // -----------------------------------------------------------------------
  // Projects
  // -----------------------------------------------------------------------

  generateProjects(): string {
    const projects = asArray(this.data["projects"]);
    if (projects.length === 0) return "";

    const sections: string[] = [];
    for (const raw of projects) {
      const proj = asRecord(raw);

      let name = asString(
        getFieldWithFallback<string>(
          proj,
          "name",
          ["title", "project_name"],
          "Project",
        ),
      );
      const url = asString(proj["url"]);
      if (url) {
        name = `#link("${url}")[${typstEscape(name)}]`;
      } else {
        name = `*${typstEscape(name)}*`;
      }

      const description = getFieldWithFallback<unknown>(
        proj,
        "description",
        ["summary", "desc"],
        "",
      );
      let descText: string;
      if (Array.isArray(description)) {
        descText = description.map((d) => typstEscape(asString(d))).join(", ");
      } else {
        descText = typstEscape(asString(description));
      }

      const tools = asArray(
        getFieldWithFallback<unknown[]>(
          proj,
          "tools",
          ["technologies", "tech_stack", "stack"],
          [],
        ),
      );
      const achievements = asArray(
        getFieldWithFallback<unknown[]>(
          proj,
          "achievements",
          ["accomplishments", "results", "outcomes"],
          [],
        ),
      );

      const entryLines: string[] = [];
      entryLines.push(`${name} -- _${descText}_`);

      if (tools.length > 0) {
        entryLines.push(
          `- *Tools:* ${tools.map((t) => typstEscape(asString(t))).join(", ")}`,
        );
      }

      if (achievements.length > 0) {
        entryLines.push("- *Achievements:*");
        for (const ach of achievements) {
          entryLines.push(`  - ${typstEscape(asString(ach))}`);
        }
      }

      sections.push(entryLines.join("\n"));
    }
    return sections.join("\n#v(0.3cm)\n");
  }

  // -----------------------------------------------------------------------
  // Certifications
  // -----------------------------------------------------------------------

  generateCertifications(): string {
    const certifications = getFieldWithFallback<unknown>(
      this.data,
      "certifications",
      ["certificates", "credentials", "licenses"],
      undefined,
    );
    if (!certifications) return "";

    if (
      typeof certifications === "object" &&
      !Array.isArray(certifications) &&
      certifications !== null
    ) {
      // Categorized dict format
      const catSections: string[] = [];
      for (const [category, certs] of Object.entries(
        certifications as DataObject,
      )) {
        const certList = asArray(certs);
        if (certList.length === 0) continue;

        let categoryName = category
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase());
        categoryName = categoryName
          .replace(/Ai Ml/gi, "AI/ML")
          .replace(/Ai\/Ml/gi, "AI/ML")
          .replace(/ And /g, " & ");

        const certItems = certList.map((c) => this.formatCertificationWithLink(c));
        catSections.push(
          `*${typstEscape(categoryName)}:* ${certItems.join(", ")}`,
        );
      }
      if (catSections.length === 0) return "";
      return catSections.join("\n\n");
    }

    // Flat list format
    const certList = asArray(certifications);
    if (certList.length === 0) return "";
    const certItems = certList.map((c) => this.formatCertificationWithLink(c));
    return certItems.join(", ");
  }

  private formatCertificationWithLink(cert: unknown): string {
    if (typeof cert === "string") {
      return typstEscape(cert);
    }
    if (typeof cert === "object" && cert !== null) {
      const obj = cert as DataObject;
      const name = asString(
        getFieldWithFallback<string>(
          obj,
          "name",
          ["title", "certification"],
          "",
        ),
      );
      const url = asString(
        getFieldWithFallback<string>(obj, "url", ["link", "href"], ""),
      );

      if (url && name) {
        return `#link("${url}")[${typstEscape(name)}]`;
      }
      if (name) {
        return typstEscape(name);
      }
      return typstEscape(String(cert));
    }
    return typstEscape(String(cert));
  }

  // -----------------------------------------------------------------------
  // Technologies & Skills
  // -----------------------------------------------------------------------

  generateTechnologiesAndSkills(): string {
    const skillsData = getFieldWithFallback<unknown>(
      this.data,
      "technologiesAndSkills",
      ["skills", "technologies", "tech_skills"],
      undefined,
    );
    if (!skillsData) return "";

    const sections: string[] = [];

    if (
      Array.isArray(skillsData) &&
      skillsData.every((s) => typeof s === "string")
    ) {
      // Simple string array
      sections.push(
        `*Skills:* ${(skillsData as string[]).map((s) => typstEscape(s)).join(", ")}`,
      );
    } else {
      const items = asArray(skillsData);
      for (const raw of items) {
        const skill = asRecord(raw);
        const category = typstEscape(
          asString(
            getFieldWithFallback<string>(
              skill,
              "category",
              ["name", "type"],
              "Skills",
            ),
          ),
        );
        const skillList = asArray(
          getFieldWithFallback<unknown[]>(
            skill,
            "skills",
            ["items", "technologies"],
            [],
          ),
        );
        if (skillList.length > 0) {
          sections.push(
            `*${category}:* ${skillList.map((s) => typstEscape(asString(s))).join(", ")}`,
          );
        }
      }
    }
    return sections.join("\n\n");
  }

  // -----------------------------------------------------------------------
  // Core Competencies
  // -----------------------------------------------------------------------

  generateCoreCompetencies(): string {
    const competencies = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "coreCompetencies",
        ["competencies", "keySkills", "expertise"],
        [],
      ),
    );
    if (competencies.length === 0) return "";

    return competencies
      .map((item) => `- ${typstEscape(asString(item))}`)
      .join("\n");
  }

  // -----------------------------------------------------------------------
  // Technical Skills
  // -----------------------------------------------------------------------

  generateTechnicalSkills(): string {
    const techSkills = getFieldWithFallback<unknown>(
      this.data,
      "technicalSkills",
      ["techSkills"],
      undefined,
    );
    if (!techSkills || typeof techSkills !== "object") return "";

    const sections: string[] = [];
    for (const [category, skills] of Object.entries(
      techSkills as DataObject,
    )) {
      const skillList = asArray(skills);
      if (skillList.length > 0) {
        const categoryName = category
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase());
        sections.push(
          `*${typstEscape(categoryName)}:* ${skillList.map((s) => typstEscape(asString(s))).join(", ")}`,
        );
      }
    }
    return sections.join("\n\n");
  }

  // -----------------------------------------------------------------------
  // Core Competencies & Technical Skills (merged)
  // -----------------------------------------------------------------------

  generateCoreCompetenciesAndTechnicalSkills(): string {
    const competencies = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "coreCompetencies",
        ["competencies", "keySkills", "expertise"],
        [],
      ),
    );

    if (competencies.length === 0) {
      // Fallback to technical skills
      const techSkills = getFieldWithFallback<unknown>(
        this.data,
        "technicalSkills",
        ["techSkills"],
        undefined,
      );
      if (!techSkills || typeof techSkills !== "object") return "";

      const items: string[] = [];
      for (const [category, skills] of Object.entries(
        techSkills as DataObject,
      )) {
        const skillList = asArray(skills);
        if (skillList.length > 0) {
          const categoryName = category
            .replace(/_/g, " ")
            .replace(/\b\w/g, (c) => c.toUpperCase());
          items.push(
            `- *${typstEscape(categoryName)}:* ${skillList.map((s) => typstEscape(asString(s))).join(", ")}`,
          );
        }
      }
      return items.join("\n");
    }

    // Show core competencies
    return competencies
      .map((item) => `- ${typstEscape(asString(item))}`)
      .join("\n");
  }

  // -----------------------------------------------------------------------
  // Skills Matrix
  // -----------------------------------------------------------------------

  generateSkillsMatrix(): string {
    const skillsMatrix = getFieldWithFallback<unknown>(
      this.data,
      "skillsMatrix",
      ["skillsByProficiency"],
      undefined,
    );
    if (!skillsMatrix || typeof skillsMatrix !== "object") return "";

    const proficiencyOrder = [
      "expert",
      "advanced",
      "intermediate",
      "familiar",
      "beginner",
    ];
    const matrix = skillsMatrix as DataObject;
    const sections: string[] = [];

    for (const level of proficiencyOrder) {
      const skills = asArray(matrix[level]);
      if (skills.length > 0) {
        const levelName = level.charAt(0).toUpperCase() + level.slice(1);
        sections.push(
          `*${typstEscape(levelName)}:* ${skills.map((s) => typstEscape(asString(s))).join(", ")}`,
        );
      }
    }
    return sections.join("\n\n");
  }

  // -----------------------------------------------------------------------
  // Articles & Publications
  // -----------------------------------------------------------------------

  generateArticlesAndPublications(): string {
    const publications = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "articlesAndPublications",
        ["publications", "articles", "papers"],
        [],
      ),
    );
    if (publications.length === 0) return "";

    const items: string[] = [];
    for (const raw of publications) {
      const pub = asRecord(raw);
      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(pub, "title", ["name"], "Publication"),
        ),
      );
      const date = typstEscape(
        asString(
          getFieldWithFallback<string>(
            pub,
            "date",
            ["published_date", "year"],
            "",
          ),
        ),
      );
      items.push(`- *${title}* -- ${date}`);
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Achievements
  // -----------------------------------------------------------------------

  generateAchievements(): string {
    const achievements = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "achievements",
        ["accomplishments", "awards", "honors"],
        [],
      ),
    );
    if (achievements.length === 0) return "";

    return achievements
      .map((item) => `- ${typstEscape(asString(item))}`)
      .join("\n");
  }

  // -----------------------------------------------------------------------
  // Awards & Honors
  // -----------------------------------------------------------------------

  generateAwardsAndHonors(): string {
    const awards = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "awardsAndHonors",
        ["awards", "honors", "recognition"],
        [],
      ),
    );
    if (awards.length === 0) return "";

    const items: string[] = [];
    for (const raw of awards) {
      if (typeof raw === "string") {
        items.push(`- ${typstEscape(raw)}`);
      } else {
        const award = asRecord(raw);
        const title = typstEscape(
          asString(
            getFieldWithFallback<string>(
              award,
              "title",
              ["name", "award"],
              "Award",
            ),
          ),
        );
        const issuer = typstEscape(
          asString(
            getFieldWithFallback<string>(
              award,
              "issuer",
              ["organization", "from"],
              "",
            ),
          ),
        );
        const date = typstEscape(
          asString(
            getFieldWithFallback<string>(award, "date", ["year"], ""),
          ),
        );

        let awardStr = `*${title}*`;
        if (issuer) awardStr += ` -- ${issuer}`;
        if (date) awardStr += `, ${date}`;
        items.push(`- ${awardStr}`);
      }
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Leadership Experience
  // -----------------------------------------------------------------------

  generateLeadershipExperience(): string {
    const leadership = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "leadershipExperience",
        ["leadership"],
        [],
      ),
    );
    if (leadership.length === 0) return "";

    const sections: string[] = [];
    for (const raw of leadership) {
      const exp = asRecord(raw);

      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(
            exp,
            "title",
            ["position", "role"],
            "Leadership Role",
          ),
        ),
      );
      let organization = asString(
        getFieldWithFallback<string>(exp, "organization", ["company"], ""),
      );
      const url = asString(exp["url"]);
      if (url) {
        organization = `#link("${url}")[${typstEscape(organization)}]`;
      } else {
        organization = typstEscape(organization);
      }

      const startDate = asString(exp["startDate"]);
      const endDate = asString(
        getFieldWithFallback<string>(exp, "endDate", ["end_date"], "Present"),
      );
      const dateRange = startDate
        ? `${typstEscape(startDate)} -- ${typstEscape(endDate)}`
        : typstEscape(endDate);

      const achievements = asArray(
        getFieldWithFallback<unknown[]>(
          exp,
          "achievements",
          ["details", "responsibilities"],
          [],
        ),
      );

      const entryLines: string[] = [];
      entryLines.push(`*${title}*, ${organization} #h(1fr) ${dateRange}`);
      for (const ach of achievements) {
        entryLines.push(`- ${typstEscape(asString(ach))}`);
      }
      sections.push(entryLines.join("\n"));
    }
    return sections.join("\n#v(0.3cm)\n");
  }

  // -----------------------------------------------------------------------
  // Relevant Coursework
  // -----------------------------------------------------------------------

  generateRelevantCoursework(): string {
    const coursework = getFieldWithFallback<unknown>(
      this.data,
      "relevantCoursework",
      ["coursework", "courses"],
      undefined,
    );
    if (!coursework) return "";

    const items = asArray(coursework);
    if (items.length === 0) return "";

    if (typeof items[0] === "string") {
      // Simple list of course names
      return items.map((c) => typstEscape(asString(c))).join(", ");
    }

    // Structured coursework with details
    const courseLines: string[] = [];
    for (const raw of items) {
      const course = asRecord(raw);
      const name = typstEscape(
        asString(
          getFieldWithFallback<string>(
            course,
            "name",
            ["title", "courseName"],
            "Course",
          ),
        ),
      );
      const description = asString(course["description"]);
      if (description) {
        courseLines.push(`- *${name}:* ${typstEscape(description)}`);
      } else {
        courseLines.push(`- *${name}*`);
      }
    }
    return courseLines.join("\n");
  }

  // -----------------------------------------------------------------------
  // Open Source Contributions
  // -----------------------------------------------------------------------

  generateOpenSourceContributions(): string {
    const contributions = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "openSourceContributions",
        ["openSource", "ossContributions"],
        [],
      ),
    );
    if (contributions.length === 0) return "";

    const sections: string[] = [];
    for (const raw of contributions) {
      const contrib = asRecord(raw);
      const project = typstEscape(
        asString(
          getFieldWithFallback<string>(
            contrib,
            "project",
            ["name", "repository"],
            "Project",
          ),
        ),
      );
      const description = typstEscape(
        asString(
          getFieldWithFallback<string>(contrib, "description", ["summary"], ""),
        ),
      );
      const url = asString(contrib["url"]);
      const contribList = asArray(
        getFieldWithFallback<unknown[]>(
          contrib,
          "contributions",
          ["details"],
          [],
        ),
      );

      const entryLines: string[] = [];
      if (url) {
        entryLines.push(
          `*${project}* (#link("${url}")[${typstEscape(url)}]) -- _${description}_`,
        );
      } else {
        entryLines.push(`*${project}* -- _${description}_`);
      }

      for (const c of contribList) {
        entryLines.push(`- ${typstEscape(asString(c))}`);
      }

      sections.push(entryLines.join("\n"));
    }
    return sections.join("\n#v(0.3cm)\n");
  }

  // -----------------------------------------------------------------------
  // Research Experience
  // -----------------------------------------------------------------------

  generateResearchExperience(): string {
    const research = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "researchExperience",
        ["research"],
        [],
      ),
    );
    if (research.length === 0) return "";

    const sections: string[] = [];
    for (const raw of research) {
      const exp = asRecord(raw);

      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(
            exp,
            "title",
            ["position", "role"],
            "Researcher",
          ),
        ),
      );
      const institution = typstEscape(
        asString(
          getFieldWithFallback<string>(
            exp,
            "institution",
            ["organization", "lab"],
            "",
          ),
        ),
      );
      const startDate = asString(exp["startDate"]);
      const endDate = asString(
        getFieldWithFallback<string>(exp, "endDate", ["end_date"], "Present"),
      );
      const dateRange = startDate
        ? `${typstEscape(startDate)} -- ${typstEscape(endDate)}`
        : typstEscape(endDate);

      const description = asArray(
        getFieldWithFallback<unknown[]>(
          exp,
          "description",
          ["summary", "details"],
          [],
        ),
      );

      const entryLines: string[] = [];
      entryLines.push(
        `*${title}*, ${institution} #h(1fr) ${dateRange}`,
      );
      for (const desc of description) {
        entryLines.push(`- ${typstEscape(asString(desc))}`);
      }
      sections.push(entryLines.join("\n"));
    }
    return sections.join("\n#v(0.3cm)\n");
  }

  // -----------------------------------------------------------------------
  // Publications (peer-reviewed)
  // -----------------------------------------------------------------------

  generatePublications(): string {
    const publications = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "publications",
        ["academicPublications", "papers"],
        [],
      ),
    );
    if (publications.length === 0) return "";

    const items: string[] = [];
    for (const raw of publications) {
      const pub = asRecord(raw);
      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(pub, "title", ["name"], "Publication"),
        ),
      );
      const authors = asString(pub["authors"]);
      const venue = asString(
        getFieldWithFallback<string>(
          pub,
          "venue",
          ["journal", "conference"],
          "",
        ),
      );
      const date = asString(
        getFieldWithFallback<string>(
          pub,
          "date",
          ["year", "published"],
          "",
        ),
      );
      const url = asString(pub["url"]);

      let pubStr = `*${title}*`;
      if (authors) pubStr += `. ${typstEscape(authors)}`;
      if (venue) pubStr += `. _${typstEscape(venue)}_`;
      if (date) pubStr += `, ${typstEscape(date)}`;
      if (url) pubStr += `. #link("${url}")[Link]`;

      items.push(`- ${pubStr}`);
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Technical Writing
  // -----------------------------------------------------------------------

  generateTechnicalWriting(): string {
    const writing = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "technicalWriting",
        ["articles", "blogPosts"],
        [],
      ),
    );
    if (writing.length === 0) return "";

    const items: string[] = [];
    for (const raw of writing) {
      const article = asRecord(raw);
      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(
            article,
            "title",
            ["name"],
            "Article",
          ),
        ),
      );
      const platform = typstEscape(asString(article["platform"]));
      const date = typstEscape(
        asString(
          getFieldWithFallback<string>(
            article,
            "date",
            ["published", "year"],
            "",
          ),
        ),
      );
      const url = asString(article["url"]);

      let articleStr = `*${title}*`;
      if (platform) articleStr += ` -- ${platform}`;
      if (date) articleStr += `, ${date}`;
      if (url) articleStr += `. #link("${url}")[Link]`;

      items.push(`- ${articleStr}`);
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Speaking Engagements
  // -----------------------------------------------------------------------

  generateSpeakingEngagements(): string {
    const speaking = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "speakingEngagements",
        ["speaking", "talks", "conferences"],
        [],
      ),
    );
    if (speaking.length === 0) return "";

    const items: string[] = [];
    for (const raw of speaking) {
      const talk = asRecord(raw);
      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(
            talk,
            "title",
            ["name", "topic"],
            "Talk",
          ),
        ),
      );
      const event = typstEscape(
        asString(
          getFieldWithFallback<string>(
            talk,
            "event",
            ["conference", "venue"],
            "",
          ),
        ),
      );
      const date = typstEscape(
        asString(getFieldWithFallback<string>(talk, "date", ["year"], "")),
      );
      const location = typstEscape(asString(talk["location"]));

      let talkStr = `*${title}*`;
      if (event) talkStr += ` -- ${event}`;
      if (location) talkStr += `, ${location}`;
      if (date) talkStr += ` (${date})`;

      items.push(`- ${talkStr}`);
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Teaching Experience
  // -----------------------------------------------------------------------

  generateTeachingExperience(): string {
    const teaching = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "teachingExperience",
        ["teaching"],
        [],
      ),
    );
    if (teaching.length === 0) return "";

    const sections: string[] = [];
    for (const raw of teaching) {
      const exp = asRecord(raw);

      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(
            exp,
            "title",
            ["position", "role"],
            "Instructor",
          ),
        ),
      );
      const institution = typstEscape(
        asString(
          getFieldWithFallback<string>(
            exp,
            "institution",
            ["organization", "school"],
            "",
          ),
        ),
      );
      const startDate = asString(exp["startDate"]);
      const endDate = asString(
        getFieldWithFallback<string>(exp, "endDate", ["end_date"], "Present"),
      );
      const dateRange = startDate
        ? `${typstEscape(startDate)} -- ${typstEscape(endDate)}`
        : typstEscape(endDate);

      const courses = asArray(
        getFieldWithFallback<unknown[]>(
          exp,
          "courses",
          ["subjects", "classes"],
          [],
        ),
      );
      const details = asArray(
        getFieldWithFallback<unknown[]>(
          exp,
          "details",
          ["description", "achievements"],
          [],
        ),
      );

      const entryLines: string[] = [];
      entryLines.push(
        `*${title}*, ${institution} #h(1fr) ${dateRange}`,
      );

      if (courses.length > 0) {
        entryLines.push(
          `- *Courses:* ${courses.map((c) => typstEscape(asString(c))).join(", ")}`,
        );
      }
      for (const detail of details) {
        entryLines.push(`- ${typstEscape(asString(detail))}`);
      }

      sections.push(entryLines.join("\n"));
    }
    return sections.join("\n#v(0.3cm)\n");
  }

  // -----------------------------------------------------------------------
  // Mentorship
  // -----------------------------------------------------------------------

  generateMentorship(): string {
    const mentorship = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "mentorship",
        ["mentoringExperience"],
        [],
      ),
    );
    if (mentorship.length === 0) return "";

    const bullets: string[] = [];
    for (const raw of mentorship) {
      if (typeof raw === "string") {
        bullets.push(`- ${typstEscape(raw)}`);
      } else {
        const item = asRecord(raw);
        const description = typstEscape(
          asString(
            getFieldWithFallback<string>(
              item,
              "description",
              ["summary", "details"],
              "",
            ),
          ),
        );
        const count = asString(item["menteeCount"]);
        const duration = typstEscape(asString(item["duration"]));

        let mentorStr = description;
        if (count) mentorStr += ` (${typstEscape(count)} mentees)`;
        if (duration) mentorStr += ` -- ${duration}`;
        bullets.push(`- ${mentorStr}`);
      }
    }
    return bullets.join("\n");
  }

  // -----------------------------------------------------------------------
  // Volunteering
  // -----------------------------------------------------------------------

  generateVolunteering(): string {
    const volunteering = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "volunteering",
        ["volunteerExperience", "communityService"],
        [],
      ),
    );
    if (volunteering.length === 0) return "";

    const sections: string[] = [];
    for (const raw of volunteering) {
      if (typeof raw === "string") {
        sections.push(`- ${typstEscape(raw)}`);
      } else {
        const vol = asRecord(raw);
        const role = typstEscape(
          asString(
            getFieldWithFallback<string>(
              vol,
              "role",
              ["title", "position"],
              "Volunteer",
            ),
          ),
        );
        const organization = typstEscape(
          asString(
            getFieldWithFallback<string>(vol, "organization", ["org"], ""),
          ),
        );
        const startDate = asString(vol["startDate"]);
        const endDate = asString(
          getFieldWithFallback<string>(vol, "endDate", ["end_date"], "Present"),
        );
        const dateRange = startDate
          ? `${typstEscape(startDate)} -- ${typstEscape(endDate)}`
          : typstEscape(endDate);

        const description = asArray(
          getFieldWithFallback<unknown[]>(
            vol,
            "description",
            ["details"],
            [],
          ),
        );

        const entryLines: string[] = [];
        entryLines.push(
          `*${role}*, ${organization} #h(1fr) ${dateRange}`,
        );
        for (const desc of description) {
          entryLines.push(`- ${typstEscape(asString(desc))}`);
        }
        sections.push(entryLines.join("\n"));
      }
    }
    return sections.join("\n#v(0.3cm)\n");
  }

  // -----------------------------------------------------------------------
  // Languages
  // -----------------------------------------------------------------------

  generateLanguages(): string {
    const languages = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "languages",
        ["spokenLanguages"],
        [],
      ),
    );
    if (languages.length === 0) return "";

    const langItems: string[] = [];
    for (const raw of languages) {
      if (typeof raw === "string") {
        langItems.push(typstEscape(raw));
      } else {
        const lang = asRecord(raw);
        const language = typstEscape(
          asString(
            getFieldWithFallback<string>(lang, "language", ["name"], "Language"),
          ),
        );
        const proficiency = typstEscape(
          asString(
            getFieldWithFallback<string>(
              lang,
              "proficiency",
              ["level", "fluency"],
              "",
            ),
          ),
        );
        if (proficiency) {
          langItems.push(`${language} (${proficiency})`);
        } else {
          langItems.push(language);
        }
      }
    }
    return langItems.join(", ");
  }

  // -----------------------------------------------------------------------
  // Professional Affiliations
  // -----------------------------------------------------------------------

  generateProfessionalAffiliations(): string {
    const affiliations = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "professionalAffiliations",
        ["affiliations", "memberships"],
        [],
      ),
    );
    if (affiliations.length === 0) return "";

    const items: string[] = [];
    for (const raw of affiliations) {
      if (typeof raw === "string") {
        items.push(`- ${typstEscape(raw)}`);
      } else {
        const affil = asRecord(raw);
        const organization = typstEscape(
          asString(
            getFieldWithFallback<string>(
              affil,
              "organization",
              ["name"],
              "Organization",
            ),
          ),
        );
        const role = typstEscape(asString(affil["role"]) || "Member");
        const date = typstEscape(
          asString(
            getFieldWithFallback<string>(
              affil,
              "date",
              ["year", "since"],
              "",
            ),
          ),
        );

        let affilStr = `*${organization}* -- ${role}`;
        if (date) affilStr += ` (${date})`;
        items.push(`- ${affilStr}`);
      }
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Patents
  // -----------------------------------------------------------------------

  generatePatents(): string {
    const patents = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "patents",
        ["intellectualProperty"],
        [],
      ),
    );
    if (patents.length === 0) return "";

    const items: string[] = [];
    for (const raw of patents) {
      const patent = asRecord(raw);
      const title = typstEscape(
        asString(
          getFieldWithFallback<string>(patent, "title", ["name"], "Patent"),
        ),
      );
      const patentNumber = typstEscape(asString(patent["patentNumber"]));
      const status = typstEscape(asString(patent["status"]));
      const date = typstEscape(
        asString(
          getFieldWithFallback<string>(
            patent,
            "date",
            ["year", "filed"],
            "",
          ),
        ),
      );

      let patentStr = `*${title}*`;
      if (patentNumber) patentStr += ` (Patent No. ${patentNumber})`;
      if (status) patentStr += ` -- ${status}`;
      if (date) patentStr += `, ${date}`;

      items.push(`- ${patentStr}`);
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Industry Expertise
  // -----------------------------------------------------------------------

  generateIndustryExpertise(): string {
    const expertise = asArray(
      getFieldWithFallback<unknown[]>(
        this.data,
        "industryExpertise",
        ["industryExperience", "domains"],
        [],
      ),
    );
    if (expertise.length === 0) return "";

    const items: string[] = [];
    for (const raw of expertise) {
      if (typeof raw === "string") {
        items.push(`- ${typstEscape(raw)}`);
      } else {
        const industry = asRecord(raw);
        const name = typstEscape(
          asString(
            getFieldWithFallback<string>(
              industry,
              "name",
              ["industry", "domain"],
              "Industry",
            ),
          ),
        );
        const years = asString(industry["years"]);
        const description = typstEscape(asString(industry["description"]));

        let industryStr = `*${name}*`;
        if (years) industryStr += ` (${typstEscape(years)} years)`;
        if (description) industryStr += `: ${description}`;

        items.push(`- ${industryStr}`);
      }
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Referral
  // -----------------------------------------------------------------------

  generateReferral(): string {
    const referral = getFieldWithFallback<unknown>(
      this.data,
      "referral",
      ["referredBy"],
      undefined,
    );
    if (!referral) return "";

    if (typeof referral === "string") {
      return typstEscape(referral);
    }

    const ref = asRecord(referral);
    const name = asString(
      getFieldWithFallback<string>(ref, "name", ["referralName"], ""),
    );
    if (!name) return "";

    const title = typstEscape(
      asString(getFieldWithFallback<string>(ref, "title", ["position"], "")),
    );
    const company = typstEscape(
      asString(
        getFieldWithFallback<string>(ref, "company", ["organization"], ""),
      ),
    );
    const relationship = typstEscape(asString(ref["relationship"]));

    let referralStr = `Referred by *${typstEscape(name)}*`;
    if (title) referralStr += `, ${title}`;
    if (company) referralStr += ` at ${company}`;
    if (relationship) referralStr += ` (${relationship})`;

    return referralStr;
  }

  // -----------------------------------------------------------------------
  // References
  // -----------------------------------------------------------------------

  generateReferences(): string {
    const references = getFieldWithFallback<unknown>(
      this.data,
      "references",
      ["professionalReferences"],
      undefined,
    );

    if (!references) {
      const refText = asString(this.data["referencesAvailable"]);
      if (refText) return typstEscape(refText);
      return "";
    }

    if (typeof references === "string") {
      return typstEscape(references);
    }

    const refList = asArray(references);
    if (refList.length === 0) return "";

    const items: string[] = [];
    for (const raw of refList) {
      const ref = asRecord(raw);
      const name = typstEscape(
        asString(
          getFieldWithFallback<string>(ref, "name", ["referenceName"], ""),
        ),
      );
      const title = typstEscape(
        asString(getFieldWithFallback<string>(ref, "title", ["position"], "")),
      );
      const company = typstEscape(
        asString(
          getFieldWithFallback<string>(ref, "company", ["organization"], ""),
        ),
      );
      const email = asString(ref["email"]);
      const phone = typstEscape(asString(ref["phone"]));

      let refStr = `*${name}*`;
      if (title) refStr += `, ${title}`;
      if (company) refStr += ` at ${company}`;

      const contactParts: string[] = [];
      if (email) {
        contactParts.push(
          `#link("mailto:${email}")[${typstEscape(email)}]`,
        );
      }
      if (phone) contactParts.push(phone);

      if (contactParts.length > 0) {
        refStr += ` (${contactParts.join(", ")})`;
      }

      items.push(`- ${refStr}`);
    }
    return items.join("\n");
  }

  // -----------------------------------------------------------------------
  // Full document generation
  // -----------------------------------------------------------------------

  private generateResume(): string {
    const personalInfo = this.generatePersonalInfo();
    const spacingConfig = this.generateSpacingConfig();

    // Determine whether to merge competencies + technical skills
    const hasCoreCompetencies =
      asArray(
        getFieldWithFallback<unknown[]>(
          this.data,
          "coreCompetencies",
          ["competencies", "keySkills", "expertise"],
          [],
        ),
      ).length > 0;

    const hasTechnicalSkills = (() => {
      const ts = getFieldWithFallback<unknown>(
        this.data,
        "technicalSkills",
        ["techSkills"],
        undefined,
      );
      if (!ts || typeof ts !== "object") return false;
      return Object.keys(ts as DataObject).length > 0;
    })();

    let coreCompetencies: string;
    let technicalSkills: string;

    if (hasCoreCompetencies && hasTechnicalSkills) {
      coreCompetencies = this.generateSectionWithHeader(
        "core_competencies_and_technical_skills",
        () => this.generateCoreCompetenciesAndTechnicalSkills(),
        "Core Competencies & Technical Skills",
      );
      technicalSkills = "";
    } else {
      coreCompetencies = this.generateSectionWithHeader(
        "core_competencies",
        () => this.generateCoreCompetencies(),
        "Core Competencies",
      );
      technicalSkills = this.generateSectionWithHeader(
        "technical_skills",
        () => this.generateTechnicalSkills(),
        "Technical Skills",
      );
    }

    const professionalSummary = this.generateSectionWithHeader(
      "professional_summary",
      () => this.generateProfessionalSummary(),
      "Professional Summary",
    );
    const leadershipExperience = this.generateSectionWithHeader(
      "leadership_experience",
      () => this.generateLeadershipExperience(),
      "Leadership Experience",
    );
    const experience = this.generateSectionWithHeader(
      "experience",
      () => this.generateExperience(),
      "Experience",
    );
    const education = this.generateSectionWithHeader(
      "education",
      () => this.generateEducation(),
      "Education",
    );
    const relevantCoursework = this.generateSectionWithHeader(
      "relevant_coursework",
      () => this.generateRelevantCoursework(),
      "Relevant Coursework",
    );
    const skillsMatrix = this.generateSectionWithHeader(
      "skills_matrix",
      () => this.generateSkillsMatrix(),
      "Skills Matrix",
    );
    const technologiesAndSkills = this.generateSectionWithHeader(
      "technologies_and_skills",
      () => this.generateTechnologiesAndSkills(),
      "Technologies & Skills",
    );
    const projects = this.generateSectionWithHeader(
      "projects",
      () => this.generateProjects(),
      "Projects",
    );
    const openSourceContributions = this.generateSectionWithHeader(
      "open_source_contributions",
      () => this.generateOpenSourceContributions(),
      "Open Source Contributions",
    );
    const researchExperience = this.generateSectionWithHeader(
      "research_experience",
      () => this.generateResearchExperience(),
      "Research Experience",
    );
    const publications = this.generateSectionWithHeader(
      "publications",
      () => this.generatePublications(),
      "Publications",
    );
    const technicalWriting = this.generateSectionWithHeader(
      "technical_writing",
      () => this.generateTechnicalWriting(),
      "Technical Writing",
    );
    const articlesAndPublications = this.generateSectionWithHeader(
      "articles_and_publications",
      () => this.generateArticlesAndPublications(),
      "Articles & Publications",
    );
    const speakingEngagements = this.generateSectionWithHeader(
      "speaking_engagements",
      () => this.generateSpeakingEngagements(),
      "Speaking Engagements",
    );
    const awardsAndHonors = this.generateSectionWithHeader(
      "awards_and_honors",
      () => this.generateAwardsAndHonors(),
      "Awards & Honors",
    );
    const achievements = this.generateSectionWithHeader(
      "achievements",
      () => this.generateAchievements(),
      "Achievements",
    );
    const certifications = this.generateSectionWithHeader(
      "certifications",
      () => this.generateCertifications(),
      "Certifications",
    );
    const teachingExperience = this.generateSectionWithHeader(
      "teaching_experience",
      () => this.generateTeachingExperience(),
      "Teaching Experience",
    );
    const mentorship = this.generateSectionWithHeader(
      "mentorship",
      () => this.generateMentorship(),
      "Mentorship",
    );
    const volunteering = this.generateSectionWithHeader(
      "volunteering",
      () => this.generateVolunteering(),
      "Volunteering & Community Service",
    );
    const languages = this.generateSectionWithHeader(
      "languages",
      () => this.generateLanguages(),
      "Languages",
    );
    const professionalAffiliations = this.generateSectionWithHeader(
      "professional_affiliations",
      () => this.generateProfessionalAffiliations(),
      "Professional Affiliations",
    );
    const patents = this.generateSectionWithHeader(
      "patents",
      () => this.generatePatents(),
      "Patents & Intellectual Property",
    );
    const industryExpertise = this.generateSectionWithHeader(
      "industry_expertise",
      () => this.generateIndustryExpertise(),
      "Industry Expertise",
    );
    const referral = this.generateSectionWithHeader(
      "referral",
      () => this.generateReferral(),
      "Referral",
    );
    const references = this.generateSectionWithHeader(
      "references",
      () => this.generateReferences(),
      "References",
    );

    // Assemble all sections -- only non-empty strings contribute
    const allSections = [
      professionalSummary,
      coreCompetencies,
      leadershipExperience,
      experience,
      education,
      relevantCoursework,
      technicalSkills,
      skillsMatrix,
      technologiesAndSkills,
      projects,
      openSourceContributions,
      researchExperience,
      publications,
      technicalWriting,
      articlesAndPublications,
      speakingEngagements,
      awardsAndHonors,
      achievements,
      certifications,
      teachingExperience,
      mentorship,
      volunteering,
      languages,
      professionalAffiliations,
      patents,
      industryExpertise,
      referral,
      references,
    ].filter((s) => s.length > 0);

    const headingShow = [
      "#show heading: it => [",
      '  #v(0.2cm)',
      '  #text(weight: "bold", size: 12pt)[#it.body]',
      '  #v(1pt)',
      '  #line(length: 100%, stroke: 0.5pt)',
      '  #v(0.15cm)',
      "]",
    ].join("\n");

    const parts: string[] = [
      spacingConfig,
      headingShow,
      "",
      personalInfo,
      "",
      ...allSections.map((s) => s + "\n"),
    ];

    return parts.join("\n");
  }

  // -----------------------------------------------------------------------
  // Document analysis (optional interface method)
  // -----------------------------------------------------------------------

  private buildDocumentAnalysis(): Record<string, unknown> {
    const sectionsToAnalyze: Array<[string, string]> = [
      ["professionalSummary", "Professional Summary"],
      ["coreCompetencies", "Core Competencies"],
      ["leadershipExperience", "Leadership Experience"],
      ["experience", "Experience"],
      ["education", "Education"],
      ["relevantCoursework", "Relevant Coursework"],
      ["technicalSkills", "Technical Skills"],
      ["skillsMatrix", "Skills Matrix"],
      ["technologiesAndSkills", "Technologies & Skills"],
      ["projects", "Projects"],
      ["openSourceContributions", "Open Source Contributions"],
      ["researchExperience", "Research Experience"],
      ["publications", "Publications"],
      ["technicalWriting", "Technical Writing"],
      ["articlesAndPublications", "Articles & Publications"],
      ["speakingEngagements", "Speaking Engagements"],
      ["awardsAndHonors", "Awards & Honors"],
      ["achievements", "Achievements"],
      ["certifications", "Certifications"],
      ["teachingExperience", "Teaching Experience"],
      ["mentorship", "Mentorship"],
      ["volunteering", "Volunteering"],
      ["languages", "Languages"],
      ["professionalAffiliations", "Professional Affiliations"],
      ["patents", "Patents"],
      ["industryExpertise", "Industry Expertise"],
    ];

    let totalWords = 0;
    let totalChars = 0;
    let totalLines = 0;
    const sectionAnalysis: Record<string, unknown>[] = [];

    for (const [fieldName, displayName] of sectionsToAnalyze) {
      const sectionData = this.data[fieldName];
      if (sectionData) {
        const metrics = this.analyzeSectionContent(sectionData, displayName);
        sectionAnalysis.push(metrics);

        totalWords += metrics.wordCount as number;
        totalChars += metrics.characterCount as number;
        totalLines += metrics.estimatedLines as number;
      }
    }

    // Estimate pages based on spacing mode
    let linesPerPage: number;
    if (this.spacingMode === "ultra-compact") {
      linesPerPage = 58;
    } else if (this.spacingMode === "compact") {
      linesPerPage = 52;
    } else {
      linesPerPage = 45;
    }
    const estimatedPages = Math.max(
      1,
      Math.ceil(totalLines / linesPerPage),
    );

    const recommendations = this.generateRecommendations(
      totalWords,
      totalLines,
      estimatedPages,
    );

    return {
      spacingMode: this.spacingMode,
      spacingConfig: this.getSpacingValues(),
      contentMetrics: {},
      sectionAnalysis,
      totalMetrics: {
        totalWords,
        totalCharacters: totalChars,
        totalLinesEstimate: totalLines,
        estimatedPages,
      },
      recommendations,
    };
  }

  private getSpacingValues(): Record<string, string> {
    if (this.spacingMode === "compact") {
      return {
        marginTop: "0.5cm",
        marginBottom: "0.5cm",
        marginLeft: "0.6cm",
        marginRight: "0.6cm",
        sectionSpacingBefore: "0.2cm",
        sectionSpacingAfter: "0.15cm",
        itemTopSep: "0.05cm",
        itemParseSep: "0.05cm",
        itemSep: "0pt",
      };
    }
    if (this.spacingMode === "ultra-compact") {
      return {
        marginTop: "0.4cm",
        marginBottom: "0.4cm",
        marginLeft: "0.5cm",
        marginRight: "0.5cm",
        sectionSpacingBefore: "0.15cm",
        sectionSpacingAfter: "0.1cm",
        itemTopSep: "0.03cm",
        itemParseSep: "0.03cm",
        itemSep: "0pt",
      };
    }
    // normal
    return {
      marginTop: "0.8cm",
      marginBottom: "0.8cm",
      marginLeft: "0.8cm",
      marginRight: "0.8cm",
      sectionSpacingBefore: "0.3cm",
      sectionSpacingAfter: "0.2cm",
      itemTopSep: "0.10cm",
      itemParseSep: "0.10cm",
      itemSep: "0pt",
    };
  }

  private analyzeSectionContent(
    content: unknown,
    sectionName: string,
  ): Record<string, unknown> {
    const text = this.extractTextFromContent(content);
    const words = text.split(/\s+/).filter((w) => w.length > 0);
    const wordCount = words.length;
    const charCount = text.length;

    const charsPerLine = 75;
    let estimatedLines = Math.max(
      1,
      Math.ceil(charCount / charsPerLine),
    );
    // Add overhead for section header and spacing
    estimatedLines += 2;

    return {
      sectionName,
      wordCount,
      characterCount: charCount,
      estimatedLines,
      averageWordLength:
        wordCount > 0 ? Math.round((charCount / wordCount) * 100) / 100 : 0,
      density:
        wordCount > 100 ? "high" : wordCount > 50 ? "medium" : "low",
    };
  }

  private extractTextFromContent(content: unknown): string {
    if (typeof content === "string") {
      return content;
    }
    if (Array.isArray(content)) {
      return content
        .map((item) => this.extractTextFromContent(item))
        .join(" ");
    }
    if (content !== null && typeof content === "object") {
      const skipKeys = new Set([
        "url",
        "website",
        "linkedin",
        "github",
        "email",
        "phone",
      ]);
      return Object.entries(content as DataObject)
        .filter(([key]) => !skipKeys.has(key))
        .map(([, value]) => this.extractTextFromContent(value))
        .join(" ");
    }
    return "";
  }

  private generateRecommendations(
    totalWords: number,
    totalLines: number,
    estimatedPages: number,
  ): string[] {
    const recommendations: string[] = [];

    if (estimatedPages > 2) {
      recommendations.push(
        `Content is estimated to span ${estimatedPages} pages. ` +
          "Consider switching to 'ultra-compact' spacing mode or reducing content.",
      );
    }

    if (estimatedPages > 1.5 && this.spacingMode === "normal") {
      recommendations.push(
        "Current spacing is 'normal'. Switching to 'compact' mode " +
          "could reduce document to 1-2 pages.",
      );
    }

    if (totalWords > 800) {
      recommendations.push(
        `Document has ${totalWords} words. For optimal readability, ` +
          "consider keeping it under 700 words for 1-page resumes.",
      );
    }

    if (totalLines > 100 && this.spacingMode === "compact") {
      recommendations.push(
        "Document has many lines even in compact mode. " +
          "Consider using bullet points instead of paragraphs, or switching to 'ultra-compact' mode.",
      );
    }

    if (recommendations.length === 0) {
      recommendations.push(
        `Document is well-optimized at ~${estimatedPages} pages with ${totalWords} words.`,
      );
    }

    return recommendations;
  }
}
