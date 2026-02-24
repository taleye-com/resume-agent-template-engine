import { z } from "zod";
import { PersonalInfoSchema } from "./personal-info.js";
import { ExperienceSchema } from "./experience.js";
import { EducationSchema } from "./education.js";

export const ProjectSchema = z.object({
  name: z.string().optional(),
  title: z.string().optional(),
  project_name: z.string().optional(),
  description: z.union([z.string(), z.array(z.string())]).optional(),
  summary: z.string().optional(),
  technologies: z.array(z.string()).optional(),
  tools: z.array(z.string()).optional(),
  tech_stack: z.array(z.string()).optional(),
  stack: z.array(z.string()).optional(),
  url: z.string().optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  achievements: z.array(z.string()).optional(),
  accomplishments: z.array(z.string()).optional(),
});

export const SkillsSchema = z.union([
  // Structured skills with categories
  z.array(
    z.object({
      category: z.string().optional(),
      name: z.string().optional(),
      type: z.string().optional(),
      skills: z.array(z.string()).optional(),
      items: z.array(z.string()).optional(),
      technologies: z.array(z.string()).optional(),
    }),
  ),
  // Simple skills array
  z.array(z.string()),
  // Dictionary-based skills
  z.record(z.array(z.string())),
]);

export const CertificationItemSchema = z.union([
  z.string(),
  z.object({
    name: z.string().optional(),
    title: z.string().optional(),
    certification: z.string().optional(),
    issuer: z.string().optional(),
    date: z.string().optional(),
    expiry: z.string().optional(),
    credential_id: z.string().optional(),
    url: z.string().optional(),
    link: z.string().optional(),
    href: z.string().optional(),
  }),
]);

export const CertificationsSchema = z.union([
  z.array(CertificationItemSchema),
  z.record(z.array(CertificationItemSchema)),
]);

export const PublicationSchema = z.object({
  title: z.string().optional(),
  name: z.string().optional(),
  authors: z.union([z.string(), z.array(z.string())]).optional(),
  venue: z.string().optional(),
  journal: z.string().optional(),
  conference: z.string().optional(),
  date: z.string().optional(),
  year: z.string().optional(),
  published: z.string().optional(),
  url: z.string().optional(),
  doi: z.string().optional(),
});

export const RecipientSchema = z.object({
  name: z.string().optional(),
  title: z.string().optional(),
  company: z.string().optional(),
  department: z.string().optional(),
  address: z.union([z.string(), z.array(z.string())]).optional(),
  street: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  zip: z.string().optional(),
  country: z.string().optional(),
});

export const ResumeDataSchema = z
  .object({
    personalInfo: PersonalInfoSchema,
    professionalSummary: z.string().optional(),
    experience: z.array(ExperienceSchema).optional(),
    education: z.array(EducationSchema).optional(),
    projects: z.array(ProjectSchema).optional(),
    skills: SkillsSchema.optional(),
    technologiesAndSkills: SkillsSchema.optional(),
    technologies: SkillsSchema.optional(),
    tech_skills: SkillsSchema.optional(),
    certifications: CertificationsSchema.optional(),
    certificates: CertificationsSchema.optional(),
    publications: z.array(PublicationSchema).optional(),
    articlesAndPublications: z.array(PublicationSchema).optional(),
    achievements: z.array(z.string()).optional(),
    awards: z.array(z.string()).optional(),
    languages: z.array(z.union([z.string(), z.record(z.string())])).optional(),
    interests: z.array(z.string()).optional(),
    // Extended sections
    coreCompetencies: z.array(z.string()).optional(),
    technicalSkills: z.record(z.array(z.string())).optional(),
    skillsMatrix: z.record(z.array(z.string())).optional(),
    leadershipExperience: z.array(z.any()).optional(),
    relevantCoursework: z.array(z.any()).optional(),
    openSourceContributions: z.array(z.any()).optional(),
    researchExperience: z.array(z.any()).optional(),
    technicalWriting: z.array(z.any()).optional(),
    speakingEngagements: z.array(z.any()).optional(),
    awardsAndHonors: z.array(z.any()).optional(),
    teachingExperience: z.array(z.any()).optional(),
    mentorship: z.array(z.any()).optional(),
    volunteering: z.array(z.any()).optional(),
    professionalAffiliations: z.array(z.any()).optional(),
    patents: z.array(z.any()).optional(),
    industryExpertise: z.array(z.any()).optional(),
    referral: z.any().optional(),
    references: z.any().optional(),
    referencesAvailable: z.string().optional(),
    spacing_mode: z.string().optional(),
    spacingMode: z.string().optional(),
  })
  .passthrough();

export type ResumeData = z.infer<typeof ResumeDataSchema>;
