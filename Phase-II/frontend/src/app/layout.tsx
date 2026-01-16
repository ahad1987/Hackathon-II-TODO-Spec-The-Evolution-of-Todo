/**
 * Root layout for the Next.js application.
 * Provides AuthProvider, ChatProvider, and global styling.
 */

import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { AuthProvider } from '@/lib/auth-context';
import { ChatProvider } from '@/chatbot/contexts/ChatContext';
import { ChatWidget } from '@/chatbot/components/ChatWidget';
import '@/styles/globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'TaskFlow — Smart TODO App with AI Chatbot',
  description: 'TaskFlow is a smart TODO app with an AI chatbot that helps you create, manage, and complete tasks using natural language. Fast, secure, and productivity-focused.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-slate-50">
        <AuthProvider>
          <ChatProvider>
            {children}
            <ChatWidget />
          </ChatProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
