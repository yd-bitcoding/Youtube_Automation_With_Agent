
from datetime import datetime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text, BigInteger, DECIMAL

Base = declarative_base()

# Users Table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    role = Column(String, default="user") 
    login_history = relationship("UserLoginHistory", back_populates="user", cascade="all, delete-orphan") 
   

    saved_videos = relationship("UserSavedVideo", back_populates="user", cascade="all, delete-orphan")
    generated_titles = relationship("GeneratedTitle", back_populates="user", cascade="all, delete-orphan")
    

class UserLoginHistory(Base):
    __tablename__ = "user_login_history"
 
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    login_time = Column(DateTime, default=datetime.utcnow(), nullable=False)
    logout_time = Column(DateTime,  nullable=True ,default=None)
    user = relationship("User", back_populates="login_history")

# Channels Table
class Channel(Base):
    __tablename__ = "channels"

    channel_id = Column(String(50), primary_key=True)
    name = Column(Text, nullable=False)  
    total_subscribers = Column(BigInteger, default=0)
    total_videos = Column(BigInteger, default=0)
    country = Column(String(50))

    videos = relationship("Video", back_populates="channel", cascade="all, delete-orphan")

# Videos Table
class Video(Base):
    __tablename__ = "videos"

    video_id = Column(String(50), primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    channel_id = Column(String(50), ForeignKey("channels.channel_id", ondelete="CASCADE"), nullable=False)  
    channel_name = Column(Text, nullable=False)  
    thumbnail = Column(String(255))
    upload_date = Column(DateTime, nullable=False)
    views = Column(BigInteger, default=0)
    likes = Column(BigInteger, default=0)
    comments = Column(BigInteger, default=0)
    subscribers = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    view_to_subscriber_ratio = Column(Float, default=0.0) 
    view_velocity = Column(Float, default=0.0)
    video_url = Column(Text, nullable=False)
    
    channel = relationship("Channel", back_populates="videos")  

    trending_topics = relationship("TrendingTopic", back_populates="video", cascade="all, delete-orphan")
    saved_by_users = relationship("UserSavedVideo", back_populates="video", cascade="all, delete-orphan")

# Trending Topics Table
class TrendingTopic(Base):
    __tablename__ = "trending_topics"

    trend_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(50), ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False)
    trend_category = Column(String(100))
    trend_score = Column(Float)
    trend_growth = Column(Float)
    keyword = Column(String, unique=True, nullable=False)  
    count = Column(Integer, nullable=False, default=0)  

    video = relationship("Video", back_populates="trending_topics")


# User Saved Videos (Many-to-Many)
class UserSavedVideo(Base):
    __tablename__ = "user_saved_videos"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    video_id = Column(String(50), ForeignKey("videos.video_id", ondelete="CASCADE"), primary_key=True)
    folder_name = Column(String(100))
    saved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_videos")
    video = relationship("Video", back_populates="saved_by_users")

# Generated Titles Table
class GeneratedTitle(Base):
    __tablename__ = "generated_titles"


    id = Column(Integer, primary_key=True, index=True)
    video_topic = Column(String)
    titles = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)


    user = relationship("User", back_populates="generated_titles")


