'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Qp as TasksAPI, TASKS_REFRESH_EVENT } from '@/services/api';

interface Task {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  created_at: string;
}

interface TaskStats {
  total: number;
  completed: number;
  pending: number;
}

function CreateTaskForm({ onTaskCreated }: { onTaskCreated?: () => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Task title cannot be empty');
      return;
    }

    try {
      setError(null);
      setIsSubmitting(true);
      await TasksAPI.createTask({
        title: title.trim(),
        description: description.trim() || undefined,
      });
      setTitle('');
      setDescription('');
      setIsOpen(false);
      onTaskCreated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setTitle('');
    setDescription('');
    setError(null);
    setIsOpen(false);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="btn-primary flex items-center gap-2 text-base font-semibold py-3 px-6"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Create New Task
      </button>
    );
  }

  return (
    <div className="card p-6 sm:p-8 border-l-4 border-l-blue-600 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900">Create a new task</h3>
        <button
          onClick={handleCancel}
          disabled={isSubmitting}
          className="text-slate-500 hover:text-slate-700 disabled:opacity-50"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {error && (
        <div className="mb-5 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm font-medium">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="title" className="block text-sm font-semibold text-slate-900 mb-2">
            Task Title <span className="text-red-500">*</span>
          </label>
          <input
            id="title"
            type="text"
            maxLength={255}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="What do you need to accomplish?"
            disabled={isSubmitting}
            className="input-field"
            autoFocus
          />
          <p className="mt-1 text-xs text-slate-500">{title.length}/255 characters</p>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-semibold text-slate-900 mb-2">
            Description <span className="text-slate-400 font-normal">(Optional)</span>
          </label>
          <textarea
            id="description"
            maxLength={5000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add details about your task..."
            rows={4}
            disabled={isSubmitting}
            className="input-field resize-none"
          />
          <p className="mt-1 text-xs text-slate-500">{description.length}/5000 characters</p>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isSubmitting || !title.trim()}
            className="btn-primary font-semibold py-2.5"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Creating...
              </span>
            ) : (
              'Create Task'
            )}
          </button>
          <button
            type="button"
            onClick={handleCancel}
            disabled={isSubmitting}
            className="btn-secondary font-semibold py-2.5"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

function TaskCard({
  task,
  onDeleted,
  onUpdated,
}: {
  task: Task;
  onDeleted?: (id: string) => void;
  onUpdated?: (task: Task) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || '');
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleComplete = async () => {
    try {
      setIsUpdating(true);
      setError(null);
      const updated = await TasksAPI.updateTask(task.id, { completed: !task.completed });
      onUpdated?.(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleSave = async () => {
    if (!title.trim()) {
      setError('Task title cannot be empty');
      return;
    }

    try {
      setError(null);
      const updated = await TasksAPI.updateTask(task.id, {
        title: title.trim(),
        description: description.trim() || null,
      });
      onUpdated?.(updated);
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;

    try {
      setIsDeleting(true);
      setError(null);
      await TasksAPI.deleteTask(task.id);
      onDeleted?.(task.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete task');
      setIsDeleting(false);
    }
  };

  if (isEditing) {
    return (
      <div className="card p-6 border-l-4 border-l-blue-600 shadow-sm">
        <div className="space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm font-medium">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-semibold text-slate-900 mb-2">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="input-field"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-900 mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="input-field resize-none"
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={handleSave} className="btn-primary font-semibold py-2.5">
              Save Changes
            </button>
            <button
              onClick={() => {
                setTitle(task.title);
                setDescription(task.description || '');
                setIsEditing(false);
                setError(null);
              }}
              className="btn-secondary font-semibold py-2.5"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`card p-6 border-l-4 transition-all shadow-sm ${
        task.completed
          ? 'border-l-green-500 bg-gradient-to-r from-green-50/50 to-white'
          : 'border-l-blue-500 hover:shadow-md'
      }`}
    >
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm font-medium mb-4">
          {error}
        </div>
      )}
      <div className="flex flex-col gap-4">
        <div className="flex items-start gap-4">
          <input
            type="checkbox"
            checked={task.completed}
            onChange={toggleComplete}
            disabled={isUpdating}
            className="mt-1 w-5 h-5 rounded border-slate-300 text-blue-600 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 accent-blue-600"
            title={task.completed ? 'Mark as incomplete' : 'Mark as complete'}
          />
          <div className="flex-1 min-w-0">
            <h3
              className={`text-lg font-semibold ${
                task.completed ? 'text-slate-500 line-through' : 'text-slate-900'
              }`}
            >
              {task.title}
            </h3>
            {task.description && (
              <p
                className={`mt-2 text-sm ${
                  task.completed ? 'text-slate-400 line-through' : 'text-slate-600'
                }`}
              >
                {task.description}
              </p>
            )}
            <p className="mt-3 text-xs text-slate-500">
              Created{' '}
              {new Date(task.created_at).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}{' '}
              at{' '}
              {new Date(task.created_at).toLocaleTimeString(undefined, {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap pt-2">
          <button
            onClick={toggleComplete}
            disabled={isUpdating}
            className={`px-3 py-2 text-sm font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed ${
              task.completed
                ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
            }`}
          >
            {isUpdating ? 'Updating...' : task.completed ? 'Mark Incomplete' : 'Mark Complete'}
          </button>
          <button
            onClick={() => setIsEditing(true)}
            className="px-3 py-2 text-sm font-semibold bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition"
          >
            Edit
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="px-3 py-2 text-sm font-semibold bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

function TaskList({
  onTasksUpdate,
  onTasksLoaded,
  refreshKey,
}: {
  onTasksUpdate?: () => void;
  onTasksLoaded?: (tasks: Task[]) => void;
  refreshKey?: number;
}) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use refs to avoid infinite loops from callback dependencies
  const onTasksLoadedRef = useRef(onTasksLoaded);
  const onTasksUpdateRef = useRef(onTasksUpdate);

  // Keep refs updated
  useEffect(() => {
    onTasksLoadedRef.current = onTasksLoaded;
    onTasksUpdateRef.current = onTasksUpdate;
  });

  const loadTasks = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await TasksAPI.listTasks();
      const taskList = response?.tasks || response || [];
      setTasks(taskList);
      onTasksLoadedRef.current?.(taskList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
      setTasks([]);
    } finally {
      setIsLoading(false);
    }
  }, []); // No dependencies - uses refs

  // Initial load and refresh on key change
  useEffect(() => {
    loadTasks();
  }, [loadTasks, refreshKey]);

  // Listen for task refresh events from chatbot
  useEffect(() => {
    const handleTasksRefresh = () => {
      loadTasks();
    };

    window.addEventListener(TASKS_REFRESH_EVENT, handleTasksRefresh);

    return () => {
      window.removeEventListener(TASKS_REFRESH_EVENT, handleTasksRefresh);
    };
  }, [loadTasks]);

  const handleDeleted = (taskId: string) => {
    const updated = tasks.filter((t) => t.id !== taskId);
    setTasks(updated);
    onTasksLoadedRef.current?.(updated);
    onTasksUpdateRef.current?.();
  };

  const handleUpdated = (updatedTask: Task) => {
    const updated = tasks.map((t) => (t.id === updatedTask.id ? updatedTask : t));
    setTasks(updated);
    onTasksLoadedRef.current?.(updated);
    onTasksUpdateRef.current?.();
  };

  if (isLoading) {
    return (
      <div className="text-center py-16">
        <div className="inline-block">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4" />
        </div>
        <p className="text-slate-600 font-medium">Loading your tasks...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <div className="flex-1">
            <h3 className="font-semibold text-red-900 mb-1">Failed to load tasks</h3>
            <p className="text-red-800 text-sm mb-4">{error}</p>
            <button onClick={loadTasks} className="btn-danger text-sm font-semibold py-2">
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-lg mb-4">
          <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">No tasks yet</h3>
        <p className="text-slate-600 max-w-sm">
          You're all caught up! Create your first task to get started with organizing your goals.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tasks.map((task) => (
        <TaskCard key={task.id} task={task} onDeleted={handleDeleted} onUpdated={handleUpdated} />
      ))}
    </div>
  );
}

export default function TasksPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [mounted, setMounted] = useState(false);
  const [stats, setStats] = useState<TaskStats>({ total: 0, completed: 0, pending: 0 });
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const updateStats = (tasks: Task[]) => {
    const completed = tasks.filter((t) => t.completed).length;
    const pending = tasks.filter((t) => !t.completed).length;
    setStats({ total: tasks.length, completed, pending });
  };

  if (!mounted || isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <h1 className="text-2xl font-semibold text-slate-900 mb-2">Loading</h1>
          <p className="text-slate-600">Getting your tasks ready...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-slate-900 mb-2">Redirecting...</h1>
          <p className="text-slate-600">Please log in to continue.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <Link href="/" className="flex items-center gap-2 hover:opacity-75 transition">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">✓</span>
                </div>
                <span className="text-lg font-bold text-slate-900 hidden sm:inline">TaskFlow</span>
              </Link>
              <span className="text-sm text-slate-600 hidden md:inline">Manage your productivity</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-slate-900">{user?.email}</p>
                <p className="text-xs text-slate-500">Your workspace</p>
              </div>
              <button onClick={handleLogout} className="btn-danger text-sm py-2">
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-2">Your Tasks</h1>
          <p className="text-slate-600">Organize, prioritize, and accomplish your goals</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="card p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600 mb-1">Total Tasks</p>
                <div className="text-4xl font-bold text-slate-900">{stats.total}</div>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
              </div>
            </div>
          </div>

          <div className="card p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600 mb-1">Completed</p>
                <div className="text-4xl font-bold text-green-600">{stats.completed}</div>
                {stats.total > 0 && (
                  <p className="text-xs text-slate-500 mt-1">
                    {Math.round((stats.completed / stats.total) * 100)}% done
                  </p>
                )}
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
          </div>

          <div className="card p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600 mb-1">Pending</p>
                <div className="text-4xl font-bold text-amber-600">{stats.pending}</div>
                {stats.total > 0 && (
                  <p className="text-xs text-slate-500 mt-1">
                    {Math.round((stats.pending / stats.total) * 100)}% remaining
                  </p>
                )}
              </div>
              <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Tasks</h2>
          </div>
          <CreateTaskForm
            onTaskCreated={() => {
              setRefreshKey((k) => k + 1);
            }}
          />
        </div>

        <div className="card p-6 sm:p-8 shadow-sm">
          <TaskList key={refreshKey} onTasksLoaded={updateStats} />
        </div>
      </main>
    </div>
  );
}
