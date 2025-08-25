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
