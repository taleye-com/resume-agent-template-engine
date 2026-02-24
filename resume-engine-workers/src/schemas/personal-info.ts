import { z } from "zod";

export const PersonalInfoSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().optional(),
  location: z.string().optional(),
  website: z.string().url().optional(),
  linkedin: z.string().url().optional(),
  github: z.string().url().optional(),
  twitter: z.string().url().optional(),
  x: z.string().url().optional(),
  title: z.string().optional(),
  headline: z.string().optional(),
  professionalTitle: z.string().optional(),
  website_display: z.string().optional(),
  linkedin_display: z.string().optional(),
  github_display: z.string().optional(),
  twitter_display: z.string().optional(),
  x_display: z.string().optional(),
});

export type PersonalInfo = z.infer<typeof PersonalInfoSchema>;
