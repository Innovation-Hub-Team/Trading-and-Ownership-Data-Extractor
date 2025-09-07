// API Configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-app-name.railway.app'  // Replace with your Railway URL
  : 'http://localhost:5003';

export default API_BASE_URL;
