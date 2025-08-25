import { Component, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TaskPriority } from '../../core/models/task.model';
import { TaskService } from '../../core/services/task.service';
import { NgIf } from '@angular/common';

@Component({
  standalone: true,
  selector: 'app-home',
  imports: [ReactiveFormsModule, RouterLink, NgIf],
  template: `
  <div class="container container-narrow py-4">
    <h1 class="mb-3">Create New Task</h1>

    <form [formGroup]="form" (ngSubmit)="submit()" class="card shadow-sm">
      <div class="card-body">
        <div class="mb-3">
          <label class="form-label">Task Title *</label>
          <input class="form-control" formControlName="title" placeholder="Enter task title">
          @if(form.controls.title.touched && form.controls.title.invalid){
            <div class="text-danger small">Title is required (min 3 chars)</div>
          }
        </div>

        <div class="mb-3">
          <label class="form-label">Description</label>
          <textarea class="form-control" rows="3" formControlName="description" placeholder="Add task description..."></textarea>
        </div>

        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label">Priority</label>
            <select class="form-select" formControlName="priority">
              <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Status</label>
            <select class="form-select" formControlName="status">
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Due Date</label>
            <input type="date" class="form-control" formControlName="dueDate">
          </div>
        </div>
      </div>
      <div class="card-footer d-flex gap-2 justify-content-end bg-white">
        <a class="btn btn-outline-secondary" routerLink="/dashboard">View Dashboard</a>
        <button class="btn btn-primary" type="submit">Create Task</button>
      </div>
    </form>
  </div>
  `
})
export class HomeComponent {
  #fb = inject(FormBuilder);
  #tasks = inject(TaskService);

  form = this.#fb.group({
    title: ['', [Validators.required, Validators.minLength(3)]],
    description: [''],
    priority: ['medium' as TaskPriority],
    status: ['pending'],
    dueDate: ['']
  });

  submit() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.#tasks.add(this.form.value as any);
    this.form.reset({ priority: 'medium', status: 'pending' });
  }
}
    -_------------------------------


    import { Component, computed, signal, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { NgClass } from '@angular/common';
import { Task, TaskPriority, TaskStatus } from '../../core/models/task.model';
import { TaskService } from '../../core/services/task.service';

@Component({
  standalone: true,
  selector: 'app-dashboard',
  imports: [FormsModule, RouterLink, NgClass],
  template: `
  <div class="container container-narrow py-4">
    <div class="d-flex align-items-center gap-3 mb-3">
      <h1 class="m-0 flex-grow-1">Task Dashboard</h1>
      <a class="btn btn-outline-secondary" routerLink="/">Back to Home</a>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-12 col-md-4">
        <div class="card text-center shadow-sm"><div class="card-body">
          <div class="h5 m-0">Total Tasks</div>
          <div class="display-6">{{ all().length }}</div>
        </div></div>
      </div>
      <div class="col-6 col-md-4">
        <div class="card text-center shadow-sm"><div class="card-body">
          <div class="h6 m-0">Pending</div>
          <div class="h3">{{ all().filter(t=>t.status==='pending').length }}</div>
        </div></div>
      </div>
      <div class="col-6 col-md-4">
        <div class="card text-center shadow-sm"><div class="card-body">
          <div class="h6 m-0">Completed</div>
          <div class="h3">{{ all().filter(t=>t.status==='completed').length }}</div>
        </div></div>
      </div>
    </div>

    <div class="card shadow-sm mb-3">
      <div class="card-body row g-3">
        <div class="col-md-4"><input class="form-control" [(ngModel)]="query" placeholder="Search tasks..."></div>
        <div class="col-md-2">
          <select class="form-select" [(ngModel)]="status">
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
        </div>
        <div class="col-md-2">
          <select class="form-select" [(ngModel)]="priority">
            <option value="">All Priorities</option>
            <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
          </select>
        </div>
        <div class="col-md-2">
          <select class="form-select" [(ngModel)]="sortBy">
            <option value="created">Sort: Created</option>
            <option value="due">Sort: Due date</option>
            <option value="title">Sort: Title</option>
          </select>
        </div>
      </div>
    </div>

    <div class="list-group shadow-sm">
      @for (t of tasks(); track t.id) {
        <a class="list-group-item list-group-item-action">
          <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1">{{ t.title }}</h5>
            <small class="text-muted">Due: {{ t.dueDate || '—' }}</small>
          </div>
          <p class="mb-2 text-muted">{{ t.description || 'No description' }}</p>

          <div class="d-flex gap-2 align-items-center">
            <span class="badge text-bg-secondary text-capitalize">{{ t.status.replace('_',' ') }}</span>
            <span class="badge" [ngClass]="{
              'text-bg-danger': t.priority==='high',
              'text-bg-warning': t.priority==='medium',
              'text-bg-success': t.priority==='low'
            }">{{ t.priority }} priority</span>

            <div class="ms-auto d-flex gap-2">
              <a class="btn btn-sm btn-outline-primary" [routerLink]="['/task', t.id]">Open</a>
              <button class="btn btn-sm btn-outline-success" (click)="complete(t.id)" [disabled]="t.status==='completed'">Complete</button>
              <button class="btn btn-sm btn-outline-danger" (click)="del(t.id)">Delete</button>
            </div>
          </div>
        </a>
      }
    </div>
  </div>
  `
})
export class DashboardComponent {
  #svc = inject(TaskService);

  query = ''; status: ''|TaskStatus = ''; priority: ''|TaskPriority = ''; sortBy: 'created'|'due'|'title' = 'created';

  all = this.#svc.tasks;
  tasks = computed(() => {
    let list: Task[] = this.all();
    if (this.query.trim()) {
      const q = this.query.toLowerCase();
      list = list.filter(t => t.title.toLowerCase().includes(q) || (t.description ?? '').toLowerCase().includes(q));
    }
    if (this.status) list = list.filter(t => t.status === this.status);
    if (this.priority) list = list.filter(t => t.priority === this.priority);
    const sort = {
      created: (a: Task, b: Task) => b.createdAt.localeCompare(a.createdAt),
      due:     (a: Task, b: Task) => (b.dueDate ?? '').localeCompare(a.dueDate ?? ''),
      title:   (a: Task, b: Task) => a.title.localeCompare(b.title)
    }[this.sortBy];
    return [...list].sort(sort);
  });

  del(id: number) { if (confirm('Delete this task?')) this.#svc.remove(id); }
  complete(id: number) { this.#svc.complete(id); }
}
