"""Tests for Article schema validation"""
import pytest
from pydantic import ValidationError
from ai_ticket_platform.schemas.endpoints.article import ArticleCreate, ArticleUpdate, ArticleRead


class TestArticleCreate:
    """Test ArticleCreate validation"""

    def test_valid_creation(self):
        """Test valid article creation"""
        article = ArticleCreate(intent_id=1, type="micro")
        assert article.intent_id == 1
        assert article.type == "micro"
        assert article.status == "iteration"
        assert article.version == 1

    def test_intent_id_validation(self):
        """Test intent_id must be > 0"""
        with pytest.raises(ValidationError):
            ArticleCreate(intent_id=0, type="micro")
        with pytest.raises(ValidationError):
            ArticleCreate(intent_id=-1, type="micro")

    def test_type_enum(self):
        """Test type must be 'micro' or 'article'"""
        with pytest.raises(ValidationError):
            ArticleCreate(intent_id=1, type="invalid")

    def test_status_enum(self):
        """Test status must be valid enum value"""
        with pytest.raises(ValidationError):
            ArticleCreate(intent_id=1, type="micro", status="invalid")

    def test_version_validation(self):
        """Test version must be >= 1"""
        with pytest.raises(ValidationError):
            ArticleCreate(intent_id=1, type="micro", version=0)
        article = ArticleCreate(intent_id=1, type="micro", version=5)
        assert article.version == 5

    def test_feedback_max_length(self):
        """Test feedback respects 2000 char limit"""
        with pytest.raises(ValidationError):
            ArticleCreate(intent_id=1, type="micro", feedback="x" * 2001)
        article = ArticleCreate(intent_id=1, type="micro", feedback="x" * 2000)
        assert len(article.feedback) == 2000


class TestArticleUpdate:
    """Test ArticleUpdate validation"""

    def test_all_optional(self):
        """Test all fields are optional in update"""
        article = ArticleUpdate()
        assert article.status is None
        assert article.version is None

    def test_status_update(self):
        """Test status update validation"""
        for status in ["accepted", "iteration", "denied"]:
            article = ArticleUpdate(status=status)
            assert article.status == status


class TestArticleRead:
    """Test ArticleRead validation"""

    def test_blob_path_required(self):
        """Test blob_path is required in Read"""
        with pytest.raises(ValidationError):
            ArticleRead(
                id=1, intent_id=1, type="micro", status="iteration",
                version=1, created_at="2024-01-01T00:00:00"
            )

    def test_valid_read(self):
        """Test valid article read"""
        article = ArticleRead(
            id=1, intent_id=1, type="micro", blob_path="azure://path",
            status="iteration", version=1, created_at="2024-01-01T00:00:00"
        )
        assert article.id == 1
        assert article.blob_path == "azure://path"