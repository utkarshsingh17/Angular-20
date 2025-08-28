import { Injectable, signal, computed, effect } from '@angular/core';

export interface User {
  username: string;
  email: string;
  password: string;
  role: 'admin' | 'author' | 'learner';
}

const USERS_KEY = 'users';
const CURRENT_KEY = 'currentUser';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private _users = signal<User[]>(this.loadUsers());
  private _currentUser = signal<User | null>(this.loadCurrentUser());

  users = this._users.asReadonly();
  currentUser = this._currentUser.asReadonly();
  isAuthenticated = computed(() => !!this._currentUser());

  constructor() {
    // persist automatically
    effect(() => {
      localStorage.setItem(USERS_KEY, JSON.stringify(this._users()));
    });
    effect(() => {
      const cu = this._currentUser();
      cu
        ? localStorage.setItem(CURRENT_KEY, JSON.stringify(cu))
        : localStorage.removeItem(CURRENT_KEY);
    });
  }

  signup(username: string, email: string, password: string, role: 'learner' = 'learner'): { ok: boolean; msg: string } {
    if (this._users().some(u => u.username === username || u.email === email)) {
      return { ok: false, msg: 'User already exists!' };
    }
    this._users.update(arr => [...arr, { username, email, password, role }]);
    return { ok: true, msg: 'Signup successful!' };
  }

  signin(username: string, password: string): { ok: boolean; msg: string } {
    const user = this._users().find(u => u.username === username && u.password === password);
    if (!user) return { ok: false, msg: 'Invalid credentials' };
    this._currentUser.set(user);
    return { ok: true, msg: 'Signin successful!' };
  }

  signout() {
    this._currentUser.set(null);
  }

  private loadUsers(): User[] {
    return JSON.parse(localStorage.getItem(USERS_KEY) || '[]');
  }
  private loadCurrentUser(): User | null {
    return JSON.parse(localStorage.getItem(CURRENT_KEY) || 'null');
  }
}
