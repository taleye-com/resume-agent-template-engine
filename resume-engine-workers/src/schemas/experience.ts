import { z } from "zod";

export const ExperienceSchema = z.object({
  position: z.string().optional(),
  title: z.string().optional(),
  role: z.string().optional(),
  company: z.string().optional(),
  employer: z.string().optional(),
  organization: z.string().optional(),
  location: z.string().optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional().default("Present"),
  end_date: z.string().optional(),
  description: z.string().optional(),
  achievements: z.array(z.string()).optional(),
  details: z.array(z.string()).optional(),
  responsibilities: z.array(z.string()).optional(),
  duties: z.array(z.string()).optional(),
  technologies: z.array(z.string()).optional(),
  url: z.string().optional(),
});

export type Experience = z.infer<typeof ExperienceSchema>;
