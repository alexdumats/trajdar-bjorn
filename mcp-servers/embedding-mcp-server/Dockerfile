FROM node:18-slim

WORKDIR /app

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy package.json and package-lock.json
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy source code
COPY src/ ./src/

# Install Python dependencies for sentence-transformers
RUN pip3 install sentence-transformers

# Expose port
EXPOSE 3000

# Start the server
CMD ["npm", "start"]