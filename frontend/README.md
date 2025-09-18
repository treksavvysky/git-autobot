# Git Autobot Frontend

A modern Next.js frontend for the Git Autobot GitHub repository manager.

## Features

- 🚀 Modern, responsive UI built with Next.js 15 and Tailwind CSS
- 📱 Mobile-first design with beautiful components
- 🔐 Secure GitHub token authentication
- ⚡ Fast API integration with the FastAPI backend
- 🎨 Clean, professional interface with loading states and error handling

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- FastAPI backend running on `http://localhost:8000`

### Installation

1. Install dependencies:

```bash
npm install
```

2. Create environment configuration:

```bash
# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

3. Start the development server:

```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create a `.env.local` file in the frontend directory:

```env
# FastAPI Backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with navigation
│   ├── page.tsx           # Home page
│   └── repositories/      # Repositories page
├── components/            # Reusable UI components
│   ├── Navigation.tsx     # Top navigation bar
│   ├── RepositoryCard.tsx # Repository display card
│   ├── LoadingSpinner.tsx # Loading state component
│   └── ErrorMessage.tsx   # Error display component
├── lib/                   # Utility functions
│   └── api.ts            # API client for backend communication
└── types/                 # TypeScript type definitions
    └── repository.ts     # Repository and API types
```

## Usage

1. **Home Page**: Landing page with project overview and navigation
2. **Repositories Page**:
   - Enter your GitHub Personal Access Token (optional if set in backend)
   - View all your GitHub repositories in a responsive grid
   - Click "View on GitHub" to open repositories in new tabs

## API Integration

The frontend communicates with the FastAPI backend through:

- **GET /repos**: Fetches user repositories
- **Query Parameter**: `token` (optional GitHub Personal Access Token)

## Development

### Available Scripts

- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Heroicons (SVG)
- **Fonts**: Geist Sans & Geist Mono

## Deployment

The frontend can be deployed to any platform that supports Next.js:

- **Vercel** (recommended)
- **Netlify**
- **Railway**
- **Docker** (see Dockerfile in parent directory)

Make sure to set the `NEXT_PUBLIC_API_URL` environment variable to your deployed backend URL.
