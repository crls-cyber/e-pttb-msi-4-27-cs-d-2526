"""Add started_at and completed_at columns to jobs table."""
from core.api.app import db, create_app
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Ajouter les colonnes si elles n'existent pas
    try:
        db.session.execute(text("""
            ALTER TABLE jobs 
            ADD COLUMN IF NOT EXISTS started_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;
        """))
        db.session.commit()
        print("✅ Colonnes started_at et completed_at ajoutées !")
    except Exception as e:
        print(f"❌ Erreur : {e}")
        db.session.rollback()
