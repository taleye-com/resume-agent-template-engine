import { z } from "zod";

export const EducationSchema = z.object({
  degree: z.string().optional(),
  title: z.string().optional(),
  qualification: z.string().optional(),
  institution: z.string().optional(),
  school: z.string().optional(),
  university: z.string().optional(),
  college: z.string().optional(),
  location: z.string().optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  end_date: z.string().optional(),
  graduationDate: z.string().optional(),
  date: z.string().optional(),
  gpa: z.string().optional(),
  coursework: z.array(z.string()).optional(),
  notableCourseWorks: z.array(z.string()).optional(),
  courses: z.array(z.string()).optional(),
  honors: z.array(z.string()).optional(),
  focus: z.string().optional(),
  major: z.string().optional(),
  specialization: z.string().optional(),
  concentration: z.string().optional(),
  projects: z.array(z.string()).optional(),
  academicProjects: z.array(z.string()).optional(),
  url: z.string().optional(),
});

export type Education = z.infer<typeof EducationSchema>;
