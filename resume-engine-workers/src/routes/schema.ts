import { Hono } from "hono";
import type { Env } from "../types/env.js";
import { InvalidParameterError } from "../errors/exceptions.js";

const app = new Hono<{ Bindings: Env }>();

const RESUME_EXAMPLE = {
  personalInfo: {
    name: "John Doe",
    email: "john@example.com",
    phone: "+1 (555) 123-4567",
    location: "New York, NY",
    website: "https://johndoe.dev",
    linkedin: "https://linkedin.com/in/johndoe",
    website_display: "johndoe.dev",
    linkedin_display: "linkedin.com/in/johndoe",
  },
  professionalSummary:
    "Experienced software engineer with 5+ years of expertise in full-stack development.",
  experience: [
    {
      position: "Senior Software Engineer",
      company: "Tech Corp",
      location: "New York, NY",
      startDate: "2020-01",
      endDate: "Present",
      achievements: [
        "Reduced system latency by 40%",
        "Led team of 5 engineers",
      ],
    },
  ],
  education: [
    {
      degree: "Bachelor of Science in Computer Science",
      institution: "University of Technology",
      graduationDate: "2019-05",
      gpa: "3.8/4.0",
    },
  ],
  skills: {
    technical: ["Python", "JavaScript", "React", "AWS"],
    soft: ["Leadership", "Communication"],
  },
};

const COVER_LETTER_EXAMPLE = {
  personalInfo: {
    name: "John Doe",
    email: "john@example.com",
    phone: "+1 (555) 123-4567",
    location: "New York, NY",
  },
  recipient: {
    name: "Jane Smith",
    title: "Hiring Manager",
    company: "Innovative Tech Solutions",
  },
  body: [
    "I am writing to express my strong interest in the Software Engineer position.",
    "My experience in full-stack development aligns perfectly with your requirements.",
  ],
};

app.get("/schema/:documentType", (c) => {
  const documentType = c.req.param("documentType");

  if (documentType === "resume") {
    return c.json({
      document_type: "resume",
      json_example: RESUME_EXAMPLE,
      description: "Complete schema and examples for resume generation",
    });
  }

  if (documentType === "cover_letter") {
    return c.json({
      document_type: "cover_letter",
      json_example: COVER_LETTER_EXAMPLE,
      description: "Complete schema and examples for cover letter generation",
    });
  }

  throw new InvalidParameterError("document_type", documentType);
});

app.get("/schema-yaml/:documentType", (c) => {
  const documentType = c.req.param("documentType");

  if (documentType !== "resume" && documentType !== "cover_letter") {
    throw new InvalidParameterError("document_type", documentType);
  }

  const example =
    documentType === "resume" ? RESUME_EXAMPLE : COVER_LETTER_EXAMPLE;

  return c.json({
    document_type: documentType,
    json_example: example,
    description: `Comprehensive example for ${documentType.replace("_", " ")} generation`,
    usage_notes: {
      required_fields: ["personalInfo"],
      optional_sections: [
        "All sections except personalInfo are optional",
        "Include only the sections relevant to your document",
      ],
      date_format: "Use YYYY-MM or YYYY-MM-DD format for dates",
      body_format:
        "For cover letters, body can be a string or array of paragraphs",
    },
  });
});

export default app;
