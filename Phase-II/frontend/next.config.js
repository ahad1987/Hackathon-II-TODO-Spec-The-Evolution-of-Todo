/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  compress: true,
  poweredByHeader: false,

  // Environment variables - use HF Spaces backend in production
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || (process.env.NODE_ENV === 'production' ? 'https://ahad-00-todo-backend-api.hf.space' : 'http://localhost:8000'),
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || (process.env.NODE_ENV === 'production' ? 'https://ahad-00-todo-backend-api.hf.space' : 'http://localhost:8000'),
  },

  // Rewrites for API proxy (optional, but helps with CORS)
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/api/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
        },
      ],
    };
  },

  // CORS headers
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Credentials',
            value: 'true',
          },
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET,DELETE,PATCH,POST,PUT',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Accept,Accept-Version,Content-Length,Content-MD5,Content-Type,Date',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
