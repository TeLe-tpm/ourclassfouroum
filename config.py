import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'forum-4j-class-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///class_4j_forum.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False