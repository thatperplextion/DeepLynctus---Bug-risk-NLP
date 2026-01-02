# Deployment Guide

## Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB Atlas account or local MongoDB
- Git

## Backend Deployment (Render/Railway/Heroku)

### Step 1: Prepare Backend
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Set Environment Variables
Create `.env` file with:
```
MONGODB_URL=your_mongodb_connection_string
OPENAI_API_KEY=your_openai_key
JWT_SECRET=your_secret_key
```

### Step 3: Deploy to Render
1. Push code to GitHub
2. Connect Render to your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard

### Step 4: Deploy to Railway
```bash
railway login
railway init
railway up
```

## Frontend Deployment (Vercel/Netlify)

### Step 1: Build Frontend
```bash
cd frontend
npm install
npm run build
```

### Step 2: Deploy to Vercel
```bash
npm install -g vercel
vercel
```

Follow prompts and set:
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

### Step 3: Set Environment Variables
```
VITE_API_URL=https://your-backend.render.com
```

## Production Checklist

### Security
- [ ] Change all default secrets
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable authentication
- [ ] Review security scanning results

### Performance
- [ ] Enable caching
- [ ] Configure CDN
- [ ] Optimize database indexes
- [ ] Enable compression
- [ ] Set up monitoring

### Monitoring
- [ ] Configure logging
- [ ] Set up error tracking (Sentry)
- [ ] Enable application monitoring (New Relic/DataDog)
- [ ] Configure uptime monitoring

### Backups
- [ ] Enable MongoDB automated backups
- [ ] Set up file storage backups
- [ ] Test restore procedures

## Docker Deployment

### Backend Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:18 as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=${MONGODB_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - mongodb
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=http://backend:8000
  
  mongodb:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

## Kubernetes Deployment

### Backend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bugrisk-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bugrisk-backend
  template:
    metadata:
      labels:
        app: bugrisk-backend
    spec:
      containers:
      - name: backend
        image: your-registry/bugrisk-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: bugrisk-secrets
              key: mongodb-url
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (Nginx/AWS ALB)
- Deploy multiple backend instances
- Implement Redis for session management
- Use CDN for static assets

### Database Scaling
- Enable MongoDB sharding
- Use read replicas
- Implement connection pooling
- Create proper indexes

### Caching Strategy
- Redis for API responses
- Browser caching for static assets
- CDN caching for images
- Service worker for offline support

## Maintenance

### Regular Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt
npm update

# Run security audit
npm audit fix
pip-audit
```

### Database Maintenance
```bash
# Compact database
mongod --dbpath /data/db --repair

# Create indexes
db.scans.createIndex({ "project_id": 1, "timestamp": -1 })
```

## Troubleshooting

### Backend Not Starting
- Check environment variables
- Verify MongoDB connection
- Review logs: `tail -f logs/bugrisk.log`

### High Memory Usage
- Enable caching
- Optimize database queries
- Implement pagination
- Use streaming for large files

### Slow API Responses
- Check database indexes
- Enable query caching
- Optimize N+1 queries
- Use connection pooling
