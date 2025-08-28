import { Course, User } from './models';

export const userMock: User = {
  name: 'Utkarsh Singh', role: 'Learner',
  avatar: 'https://i.pravatar.cc/80?img=3'
};

export const COURSES: Course[] = [
  {
    id: 'gda-1',
    title: 'Google Data Analytics Course-1',
    provider: 'Coursera',
    thumbnail: 'https://picsum.photos/seed/gda1/640/360',
    progress: 21, rating: 4.8, reviews: 1278, enrolled: 45908,
    level: 'Beginner', durationWeeks: 8, publishedAt: '2024-12-20',
    topics: ['Data', 'Analytics', 'SQL'], author: 'Stephen Mason',
    tagline: 'Become a Prompt Engineering Expert.',
    description: 'Deep dive into analytics and prompt engineering...',
    whatYouLearn: ['SQL basics','Data viz','Dashboards'],
    skills: ['SQL','Data Studio','ETL'],
    sections: [
      { title: 'Introduction', time: '45 min',
        lectures: [{title: 'Welcome', time: '6 min'},{title:'Setup', time:'12 min'}] },
      { title: 'Dashboards', time: '1h 10m',
        lectures: [{title:'Charts', time:'18 min'}] }
    ],
    testimonials: [
      { rating: 4.8, text: 'Great program—career boost!', name:'Wade Warren', avatar:'https://i.pravatar.cc/60?img=5', org:'Learners for US' },
      { rating: 4.7, text: 'Loved the exercises.', name:'Jacob Jones', avatar:'https://i.pravatar.cc/60?img=9', org:'Learners for India' }
    ]
  },
  // add more with different levels/durations/publishedAt
];

export const lastViewedIds = ['gda-1'];
export const newlyLaunchedIds = ['gda-1']; // demo
