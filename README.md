# GenAI Mental Health Chatbot

Team: David Long, Avery Im, Brody Curry, Chase Wolverton, Clayton Tucker

## Quickstart (local)

### 1) Start the backend (Flask)

```bash
cd backend
python -m pip install -r requirements.txt
python app.py

```
### 2) start frontend using node.js
```bash
cd frontend
npm install
npm start
```

## Running on EC2 (Cloud)

### 1) Log into the instance on the terminal
#### a) All team members have access to the .pem file required for this. Move it to your .ssh folder
```bash
mv ~/Downloads/mental-health-key-v2.pem ~/.ssh/
chmod 400 ~/.ssh/mental-health-key-v2.pem
```

#### b) Connect to the instance
```bash
ssh -i ~/.ssh/mental-health-key-v2.pem ubuntu@3.147.120.64
```

### 2) Navigate to the backend and launch the app
No need to manually start the frontend and backend. Backend has been adjusted to serve the frontend automatically when the app is started.
```bash
cd ~/app/backend
source venv/bin/activate
python app.py
```

### 3) Visit the site!
```
http://3.147.120.64:5050
```