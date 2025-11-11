FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first (for better caching)
COPY ./app/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY ./app/ .

# Expose the port Vite runs on
EXPOSE 5173

# Start the development server
CMD ["npm", "run", "dev"]