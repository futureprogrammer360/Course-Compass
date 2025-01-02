import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import dotenv from 'dotenv';

dotenv.config({ path: '../.env' });

const API_URL = process.env.API_URL;

export default defineConfig({
  plugins: [react()],
  define: {
    'process.env.API_URL': JSON.stringify(API_URL)
  }
});
