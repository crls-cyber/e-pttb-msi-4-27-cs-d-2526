#!/usr/bin/env python3
"""Initialize database schema and default roles."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from core.models import Base, Role

# Database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://pentest:CHANGE_ME_IN_PROD@localhost:5432/pentest_toolbox'
)

def init_db():
    """Create all tables and default roles."""
    print("🔧 Creating database tables...")
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("✅ Tables created successfully!")

    # Create default roles
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    default_roles = ['admin', 'analyst', 'viewer']
    for role_name in default_roles:
        if not session.query(Role).filter_by(name=role_name).first():
            role = Role(name=role_name)
            session.add(role)
            print(f"✅ Created role: {role_name}")

    session.commit()
    session.close()
    print("✅ Database initialization complete!")

if __name__ == '__main__':
    init_db()
