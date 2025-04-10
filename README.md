# 🚀 Viral Idea Finder & AI Title Generator

A powerful YouTube content intelligence tool that helps creators identify viral video ideas and generate high-converting titles using real-time video data and AI.

## 🔍 What It Does

- Fetches trending YouTube videos based on filters (topic, date, views, duration, etc.)
- Analyzes engagement metrics like CTR, view velocity, and engagement rate
- Detects trending topics and performs viral analysis using LangGraph
- Generates AI-powered video titles optimized for virality
- Allows users to save and manage videos with relevant analytics

---

## 📦 Features

- 🔎 **YouTube Search**: Query videos with filters (views, subscribers, duration, date)
- 📈 **Viral Metrics**: Calculates view-to-subscriber ratio, engagement rate, and velocity
- 🤖 **AI Title Generator**: Generates high-CTR titles based on video topic
- 🧠 **LangGraph Integration**: Runs viral detection and idea generation pipelines
- 💾 **Save & Retrieve**: Users can save favorite videos and revisit them later
- 🗃️ **PostgreSQL + SQLAlchemy**: Stores all videos and user interactions

---

## ⚙️ Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL, SQLAlchemy
- **YouTube API**: Video and channel data fetching
- **LangGraph**: Viral idea generation pipeline
- **AI Services**: Custom engagement and title generation modules
- **Authentication**: User management via token-based auth

---

## 🛠️ Setup

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/viral-idea-finder.git
cd viral-idea-finder
```

### 2. Create `.env` File

```env
YOUTUBE_API_KEY=your_youtube_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/yourdbname
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Run Migrations (if needed)

```bash
alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn main:app --reload
```

---

## 📂 Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/run_viral_analysis/` | Run the full viral analysis pipeline |
| `POST` | `/generate_titles/` | Generate AI-based video titles |
| `GET`  | `/search/` | Search YouTube videos with filters |
| `GET`  | `/video/{video_id}` | Get detailed info for a single video |
| `POST` | `/video/save/{video_id}` | Save a video to user's library |
| `GET`  | `/video/saved/` | Retrieve saved videos |
| `GET`  | `/user_titles/` | Fetch all AI-generated titles for the user |

---

## 🧠 Viral Metrics Calculated

- **View to Subscriber Ratio**  
- **Click-Through Rate (CTR)**  
- **Engagement Rate**  
- **View Velocity**

---

## 📌 Notes

- Shorts (under 60 seconds) are automatically filtered out.
- Videos are ranked based on engagement + virality scores.
- Requires an active YouTube Data API key.

---
