'use client';

import React, { useEffect, useState } from 'react';
import { taskApi } from '@/lib/api-client';
import TaskItem from './TaskItem';

interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

interface TaskListProps {
  onTasksUpdate?: () => void;
  onTasksLoaded?: (tasks: Task[]) => void;
}

export default function TaskList({ onTasksUpdate, onTasksLoaded }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch tasks on mount
    fetchTasks();

    // Refetch tasks when page becomes visible (user switches back from another tab)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchTasks();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup listener on unmount
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await taskApi.listTasks();
      const tasksList = response?.tasks || response || [];
      setTasks(tasksList);
      if (onTasksLoaded) {
        onTasksLoaded(tasksList);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskDeleted = (taskId: string) => {
    const updatedTasks = tasks.filter(t => t.id !== taskId);
    setTasks(updatedTasks);
    if (onTasksLoaded) {
      onTasksLoaded(updatedTasks);
    }
    if (onTasksUpdate) {
      onTasksUpdate();
    }
  };

  const handleTaskUpdated = (updatedTask: Task) => {
    const updatedTasks = tasks.map(t => (t.id === updatedTask.id ? updatedTask : t));
    setTasks(updatedTasks);
    if (onTasksLoaded) {
      onTasksLoaded(updatedTasks);
    }
    if (onTasksUpdate) {
      onTasksUpdate();
    }
  };

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="inline-block">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
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
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <h3 className="font-semibold text-red-900 mb-1">Failed to load tasks</h3>
            <p className="text-red-800 text-sm mb-4">{error}</p>
            <button
              onClick={fetchTasks}
              className="btn-danger text-sm font-semibold py-2"
            >
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
          <svg
            className="w-8 h-8 text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
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
      {tasks.map(task => (
        <TaskItem
          key={task.id}
          task={task}
          onDeleted={handleTaskDeleted}
          onUpdated={handleTaskUpdated}
        />
      ))}
    </div>
  );
}
