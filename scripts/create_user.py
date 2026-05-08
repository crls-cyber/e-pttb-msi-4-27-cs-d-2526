#!/usr/bin/env python3
"""Create a user via CLI."""
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import User, Role

# Database URL from environment
POSTGRES_USER = os.getenv('POSTGRES_USER', 'pentest')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'pentest_toolbox')

DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'


def create_user(username, password, email, role_name):
    """Create a new user."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if user exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return
        
        # Get role
        role = session.query(Role).filter_by(name=role_name).first()
        if not role:
            print(f"❌ Role '{role_name}' not found!")
            return
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        user.roles.append(role)
        
        session.add(user)
        session.commit()
        
        print(f"✅ User '{username}' created successfully with role '{role_name}'!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a user')
    parser.add_argument('--username', required=True, help='Username')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--email', help='Email address')
    parser.add_argument('--role', default='analyst', help='Role name (default: analyst)')
    
    args = parser.parse_args()
    
    create_user(args.username, args.password, args.email, args.role)
