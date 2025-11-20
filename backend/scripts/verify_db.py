# backend/scripts/verify_db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ai_ticket_platform.core.settings import initialize_settings
from ai_ticket_platform.database.generated_models import Base, Category, Intent, Article

# ensure ENVIRONMENT is set before running (export ENVIRONMENT=dev; source env_config/synced/.env.dev)
settings = initialize_settings()
engine = create_engine(
    f"{settings.MYSQL_SYNC_DRIVER}://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
)

def main():
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        # delete in dependency order
        session.query(Article).delete()
        session.query(Intent).delete()
        # delete categories bottom-up to satisfy parent FK
        for cat in session.query(Category).order_by(Category.level.desc()).all():
            session.delete(cat)
        session.commit()

        # insert categories
        cat1 = Category(name="Level1Cat", level=1, parent_id=None)
        cat2 = Category(name="Level2Cat", level=2, parent=cat1)
        cat3 = Category(name="Level3Cat", level=3, parent=cat2)
        session.add_all([cat1, cat2, cat3])
        session.flush()

        intent = Intent(
            name="Test Intent",
            category_level_1_id=cat1.id,
            category_level_2_id=cat2.id,
            category_level_3_id=cat3.id,
            area="support",
        )
        session.add(intent)
        session.flush()

        article = Article(
            intent_id=intent.id,
            type="faq",
            blob_path="/tmp/test",
            status="iteration",
            version=1,
        )
        session.add(article)
        session.commit()

        print("Inserted intent:", intent.id, intent.name)
        print("Inserted article:", article.id, article.status)

if __name__ == "__main__":
    main()
