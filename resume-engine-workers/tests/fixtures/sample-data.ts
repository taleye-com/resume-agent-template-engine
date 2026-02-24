/**
 * Sample data fixtures for unit tests.
 * Ported from Python project test fixtures.
 */

export const SAMPLE_RESUME_DATA: Record<string, unknown> = {
  personalInfo: {
    name: "John Doe",
    email: "john.doe@example.com",
    phone: "+1 (555) 123-4567",
    location: "San Francisco, CA",
    website: "https://johndoe.dev",
    linkedin: "https://linkedin.com/in/johndoe",
    github: "https://github.com/johndoe",
    website_display: "johndoe.dev",
    linkedin_display: "linkedin.com/in/johndoe",
    github_display: "github.com/johndoe",
  },
  professionalSummary:
    "Experienced full-stack software engineer with 8+ years of expertise in building scalable web applications, microservices, and cloud-native solutions. Passionate about clean code, mentoring junior developers, and driving technical innovation.",
  experience: [
    {
      title: "Senior Software Engineer",
      company: "Tech Corp",
      location: "San Francisco, CA",
      startDate: "2020-01",
      endDate: "Present",
      achievements: [
        "Led migration of monolithic application to microservices architecture, reducing deployment time by 60%",
        "Designed and implemented real-time data pipeline processing 10M+ events daily using Kafka and Flink",
        "Mentored team of 5 junior engineers, conducting weekly code reviews and knowledge-sharing sessions",
        "Optimized database queries resulting in 40% improvement in API response times",
      ],
    },
    {
      title: "Software Engineer",
      company: "Startup Inc",
      location: "New York, NY",
      startDate: "2017-06",
      endDate: "2019-12",
      achievements: [
        "Built customer-facing dashboard serving 50K+ daily active users using React and Node.js",
        "Implemented CI/CD pipeline reducing release cycles from monthly to daily deployments",
        "Developed RESTful API handling 5K+ requests per second with 99.9% uptime",
      ],
    },
  ],
  education: [
    {
      degree: "Master of Science in Computer Science",
      institution: "Stanford University",
      graduationDate: "2017-06",
      gpa: "3.9/4.0",
    },
    {
      degree: "Bachelor of Science in Computer Science",
      institution: "University of California, Berkeley",
      graduationDate: "2015-05",
      gpa: "3.7/4.0",
    },
  ],
  skills: {
    technical: ["Python", "TypeScript", "JavaScript", "Go", "Rust", "SQL"],
    frameworks: ["React", "Next.js", "FastAPI", "Django", "Express.js"],
    cloud: ["AWS", "GCP", "Docker", "Kubernetes", "Terraform"],
    tools: [
      "Git",
      "Jenkins",
      "GitHub Actions",
      "Datadog",
      "PostgreSQL",
      "Redis",
    ],
  },
  certifications: {
    cloud: [
      "AWS Solutions Architect Professional",
      "Google Cloud Professional Developer",
    ],
    ai_ml: ["TensorFlow Developer Certificate"],
  },
  projects: [
    {
      name: "Open Source CLI Tool",
      description:
        "Built a developer productivity CLI tool with 2K+ GitHub stars",
      tools: ["Rust", "Clap", "Tokio"],
    },
  ],
};

export const SAMPLE_COVER_LETTER_DATA: Record<string, unknown> = {
  personalInfo: {
    name: "John Doe",
    email: "john.doe@example.com",
    phone: "+1 (555) 123-4567",
    location: "San Francisco, CA",
  },
  recipient: {
    name: "Jane Smith",
    title: "Engineering Director",
    company: "Innovative Tech Solutions",
  },
  body: [
    "I am writing to express my strong interest in the Senior Software Engineer position at Innovative Tech Solutions. With over 8 years of experience in full-stack development and a proven track record of delivering high-impact solutions, I am confident I can make significant contributions to your team.",
    "In my current role at Tech Corp, I have successfully led the migration of our monolithic application to a microservices architecture, reducing deployment time by 60%. I have also designed and implemented a real-time data pipeline capable of processing over 10 million events daily.",
    "I am particularly drawn to Innovative Tech Solutions' commitment to leveraging cutting-edge technology to solve complex problems. I believe my experience with cloud-native architectures, real-time data processing, and team leadership aligns perfectly with your organization's goals.",
    "I would welcome the opportunity to discuss how my skills and experience can contribute to the continued success of Innovative Tech Solutions. Thank you for considering my application.",
  ],
  closing: "Sincerely,",
};

export const MINIMAL_RESUME_DATA: Record<string, unknown> = {
  personalInfo: {
    name: "Test User",
    email: "test@example.com",
  },
};
