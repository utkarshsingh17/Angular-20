import { computed, Injectable, signal } from '@angular/core';
import { COURSES } from './mock-data';
import { Course, Level } from './models';

type SortKey = 'latest'|'highestRating'|'highestReviewed'|'az'|'za';

@Injectable({ providedIn: 'root' })
export class CourseStore {
  readonly all = signal<Course[]>(COURSES);
  readonly q = signal<string>('');
  readonly selectedLevels = signal<Set<Level>>(new Set());
  readonly selectedRatings = signal<number | null>(null);   // >=
  readonly minWeeks = signal<number | null>(null);
  readonly maxWeeks = signal<number | null>(null);
  readonly author = signal<string | null>(null);
  readonly topics = signal<Set<string>>(new Set());
  readonly sort = signal<SortKey>('latest');
  readonly page = signal(1);
  readonly pageSize = 12;

  readonly suggestions = computed(() =>
    this.all().filter(c => c.title.toLowerCase().includes(this.q().toLowerCase())).slice(0, 6)
  );

  readonly filtered = computed(() => {
    const term = this.q().toLowerCase().trim();
    let res = this.all();
    if (term) res = res.filter(c => [c.title, c.tagline, c.topics.join(' ')].join(' ').toLowerCase().includes(term));
    if (this.selectedLevels().size) res = res.filter(c => this.selectedLevels().has(c.level));
    if (this.selectedRatings()) res = res.filter(c => c.rating >= (this.selectedRatings()!));
    if (this.minWeeks()) res = res.filter(c => c.durationWeeks >= this.minWeeks()!);
    if (this.maxWeeks()) res = res.filter(c => c.durationWeeks <= this.maxWeeks()!);
    if (this.author()) res = res.filter(c => c.author === this.author());
    if (this.topics().size) res = res.filter(c => c.topics.some(t => this.topics().has(t)));
    switch (this.sort()) {
      case 'latest': res = res.toSorted((a,b)=>+new Date(b.publishedAt)-+new Date(a.publishedAt)); break;
      case 'highestRating': res = res.toSorted((a,b)=>b.rating-a.rating); break;
      case 'highestReviewed': res = res.toSorted((a,b)=>b.reviews-a.reviews); break;
      case 'az': res = res.toSorted((a,b)=>a.title.localeCompare(b.title)); break;
      case 'za': res = res.toSorted((a,b)=>b.title.localeCompare(a.title)); break;
    }
    return res;
  });

  readonly paged = computed(() => {
    const start = (this.page()-1)*this.pageSize;
    return this.filtered().slice(start, start+this.pageSize);
  });

  resetFilters() {
    this.selectedLevels.set(new Set());
    this.selectedRatings.set(null);
    this.minWeeks.set(null);
    this.maxWeeks.set(null);
    this.author.set(null);
    this.topics.set(new Set());
    this.sort.set('latest'); this.page.set(1);
  }
}
