# models.py
# Defines the database table structure as Python classes using SQLAlchemy.
# Each class maps to one table. Each class attribute maps to one column.
# This is the single source of truth for our database schema.

from sqlalchemy import (
    Column, String, Text, JSON
)
from sqlalchemy.orm import DeclarativeBase


# Base class that all models inherit from.
# SQLAlchemy uses this to track all tables in our database.
class Base(DeclarativeBase):
    pass


class Flashcard(Base):
    """
    Represents a single flashcard in the database.
    Maps directly to the flashcard dictionary our pipeline produces.
    """
    __tablename__ = "flashcards"

    # Primary key — the UUID we generate in the enrichment agent
    id = Column(String, primary_key=True)

    # Core word data
    german_word = Column(String, nullable=False, unique=True)
    english_translation = Column(String, nullable=False)
    word_class = Column(String)
    gender = Column(String)
    plural_form = Column(String)

    # Sentences and mnemonic — Text type for longer strings
    example_sentence_de = Column(Text)
    example_sentence_en = Column(Text)
    mnemonic = Column(Text)
    gender_tip = Column(Text)

    # Metadata
    source = Column(String)

    # JSON type stores Python lists and dicts directly
    # SQLAlchemy handles the conversion automatically
    tags = Column(JSON, default=list)

    # Spaced repetition fields
    difficulty = Column(String)
    next_review = Column(String)

    # Timestamp
    created_at = Column(String, nullable=False)

    def to_dict(self) -> dict:
        """
        Converts the SQLAlchemy model instance to a plain dictionary.
        Useful for sending data to the frontend via the API.
        """
        return {
            "id": self.id,
            "german_word": self.german_word,
            "english_translation": self.english_translation,
            "word_class": self.word_class,
            "gender": self.gender,
            "plural_form": self.plural_form,
            "example_sentence_de": self.example_sentence_de,
            "example_sentence_en": self.example_sentence_en,
            "mnemonic": self.mnemonic,
            "gender_tip": self.gender_tip,
            "source": self.source,
            "tags": self.tags or [],
            "difficulty": self.difficulty,
            "next_review": self.next_review,
            "created_at": self.created_at
        }