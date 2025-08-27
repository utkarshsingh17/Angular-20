import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { User, PublicUser, Role } from './models/user';
import { Observable, throwError } from 'rxjs';
import { map, switchMap, tap } from 'rxjs/operators';
import { toObservable } from '@angular/core/rxjs-interop';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private static SESSION_KEY = 'app_session_user_v1';
  private API = 'http://localhost:3000';

  currentUserSig = signal<PublicUser | null>(this.readSession());

  user$ = toObservable(this.currentUserSig);
  role$ = this.user$.pipe(map(u => u?.role ?? null));
  isLoggedIn$ = this.user$.pipe(map(u => !!u));

  constructor(private http: HttpClient) {}

  private readSession(): PublicUser | null {
    try { return JSON.parse(localStorage.getItem(AuthService.SESSION_KEY) || 'null'); } catch { return null; }
  }
  private writeSession(user: PublicUser | null) {
    if (user) localStorage.setItem(AuthService.SESSION_KEY, JSON.stringify(user));
    else localStorage.removeItem(AuthService.SESSION_KEY);
  }

  register(payload: { username: string; email: string; password: string; role: Role; fullName?: string; track?: string | null; location?: string | null; }): Observable<void> {
    const normalizedEmail = payload.email.trim().toLowerCase();
    const params = new HttpParams().set('email', normalizedEmail);

    return this.http.get<User[]>(`${this.API}/users`, { params }).pipe(
      switchMap(users => {
        if (users.length) return throwError(() => new Error('Email already registered'));

        const toCreate: User = {
          username: payload.username.trim(),
          email: normalizedEmail,
          password: payload.password,
          fullName: payload.fullName?.trim(),
          track: payload.track ?? null,
          location: payload.location ?? null,
          role: payload.role,
          joinDate: new Date().toISOString(),
          avatarUrl: `https://i.pravatar.cc/150?u=${encodeURIComponent(payload.username.trim())}`,
          bio: null
        };

        return this.http.post<User>(`${this.API}/users`, toCreate).pipe(map(() => void 0));
      })
    );
  }

  login(email: string, password: string): Observable<void> {
    const params = new HttpParams().set('email', email.trim().toLowerCase()).set('password', password);

    return this.http.get<User[]>(`${this.API}/users`, { params }).pipe(
      map(users => users[0] ?? null),
      switchMap(user => {
        if (!user) return throwError(() => new Error('Invalid email or password'));
        const { password: _pw, ...publicUser } = user as any;
        this.writeSession(publicUser);
        this.currentUserSig.set(publicUser);
        return new Observable<void>(sub => { sub.next(); sub.complete(); });
      })
    );
  }

  logout() {
    this.writeSession(null);
    this.currentUserSig.set(null);
  }
}
..............................


export type Role = 'learner' | 'admin' | 'author';

export interface User {
  id?: number;
  username: string;
  email: string;
  password: string; // mock only
  fullName?: string;
  track?: string | null;
  avatarUrl?: string | null;
  joinDate?: string;
  role: Role;
  bio?: string | null;
  location?: string | null;
}

export type PublicUser = Omit<User, 'password'>;
