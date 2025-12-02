# Frontend - HRMS Core

This folder will contain the frontend application for the HRMS system.

## Options for Frontend Framework

You can choose from various frontend technologies:

### Option 1: React.js
- Modern component-based framework
- Great for complex UIs
- Large ecosystem

### Option 2: Vue.js
- Progressive framework
- Easy to learn
- Good for rapid development

### Option 3: Django Templates + HTMX
- Server-side rendering with Django templates
- HTMX for dynamic interactions
- Simpler setup, less complex build process

### Option 4: Next.js
- React-based framework
- Server-side rendering
- Great for SEO and performance

## Getting Started

Once you choose a frontend framework, you can initialize it here:

```bash
cd frontend

# For React
npx create-react-app hrms-frontend
# or
npm create vite@latest hrms-frontend -- --template react

# For Vue
npm create vue@latest hrms-frontend

# For Next.js
npx create-next-app@latest hrms-frontend
```

## API Integration

The frontend will communicate with the Django backend via REST API:
- Base URL: `http://localhost:8000/api/`
- Authentication: Token-based or JWT
- Data format: JSON