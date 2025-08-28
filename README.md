export type Level = 'Beginner'|'Intermediate'|'Advanced';

export interface Course {
  id: string;
  title: string;
  provider: string;        // e.g., "LinkedIn Learning"
  thumbnail: string;
  progress?: number;       // 0-100
  rating: number;          // 0-5
  reviews: number;         // count
  enrolled: number;        // count
  level: Level;
  durationWeeks: number;
  publishedAt: string;     // ISO
  topics: string[];
  author: string;
  tagline: string;
  description: string;
  whatYouLearn: string[];
  skills: string[];
  sections: { title: string; time: string; lectures: { title: string; time: string }[] }[];
  testimonials?: { rating: number; text: string; name: string; avatar: string; org: string }[];
}

export interface User {
  name: string; role: 'Learner'|'Admin'|'Author'; avatar: string;
}
