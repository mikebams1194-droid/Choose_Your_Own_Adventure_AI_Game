// This tells your app: Use the Vercel Environment Variable if it exists, 
// otherwise use localhost (for when you're coding at home).
export const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";