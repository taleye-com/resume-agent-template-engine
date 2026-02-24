import { z } from "zod";
import { PersonalInfoSchema } from "./personal-info.js";
import { RecipientSchema } from "./resume-data.js";

export const CoverLetterDataSchema = z
  .object({
    personalInfo: PersonalInfoSchema,
    recipient: RecipientSchema.optional(),
    date: z.string().optional(),
    salutation: z.string().optional(),
    body: z.union([z.string(), z.array(z.string())]),
    closing: z.string().optional(),
    spacing_mode: z.string().optional(),
    spacingMode: z.string().optional(),
  })
  .passthrough();

export type CoverLetterData = z.infer<typeof CoverLetterDataSchema>;
