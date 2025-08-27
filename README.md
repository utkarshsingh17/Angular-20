import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface ApiUser {
  id?: number;
  name: string;
  email: string;
  password: string; // mock only
  role: 'admin' | 'learner';
  createdAt?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private static SESSION_KEY = 'app_session_user_v1';
  private API = 'http://localhost:3000';

  currentUserSig = signal<Omit<ApiUser, 'password'> | null>(this.readSession());

  constructor(private http: HttpClient) {}

  private readSession() {
    try { return JSON.parse(localStorage.getItem(AuthService.SESSION_KEY) || 'null'); } catch { return null; }
  }
  private writeSession(user: Omit<ApiUser, 'password'> | null) {
    if (user) localStorage.setItem(AuthService.SESSION_KEY, JSON.stringify(user));
    else localStorage.removeItem(AuthService.SESSION_KEY);
  }

  async register(payload: {name: string; email: string; password: string; role: 'admin'|'learner'}): Promise<string | null> {
    try {
      // uniqueness check
      const exists = await firstValueFrom(this.http.get<ApiUser[]>(`${this.API}/users`, { params: { email: payload.email.toLowerCase() } }));
      if (exists.length) return 'Email already registered';

      const toCreate: ApiUser = {
        name: payload.name.trim(),
        email: payload.email.trim().toLowerCase(),
        password: payload.password,
        role: payload.role,
        createdAt: new Date().toISOString()
      };
      await firstValueFrom(this.http.post<ApiUser>(`${this.API}/users`, toCreate));
      return null;
    } catch (e) {
      return 'Failed to register. Is the API running?';
    }
  }

  async login(email: string, password: string): Promise<string | null> {
    try {
      const users = await firstValueFrom(this.http.get<ApiUser[]>(`${this.API}/users`, { params: { email: email.toLowerCase(), password } }));
      const user = users[0];
      if (!user) return 'Invalid email or password';
      const { password: _pw, ...publicUser } = user as any;
      this.writeSession(publicUser);
      this.currentUserSig.set(publicUser);
      return null;
    } catch (e) {
      return 'Login failed. Is the API running?';
    }
  }

  logout() {
    this.writeSession(null);
    this.currentUserSig.set(null);
  }

  isLoggedIn() { return !!this.currentUserSig(); }
  role() { return this.currentUserSig()?.role; }
}
