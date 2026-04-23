from __future__ import annotations

from typing import List, Optional

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Lab(Base):
    __tablename__ = "labs"

    lab_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(255))
    university: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    num_researchers: Mapped[int] = mapped_column(default=0)
    active_projects: Mapped[int] = mapped_column(default=0)
    avg_h_index: Mapped[float] = mapped_column(default=0.0)

    researchers: Mapped[List["Researcher"]] = relationship(
        back_populates="lab", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Lab(lab_id={self.lab_id}, name={self.name!r}, "
            f"university={self.university!r})>"
        )


class Cluster(Base):
    __tablename__ = "clusters"

    cluster_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    algorithm: Mapped[Optional[str]] = mapped_column(String(100))
    silhouette_score: Mapped[Optional[float]] = mapped_column(default=None)

    researchers: Mapped[List["Researcher"]] = relationship(back_populates="cluster")

    def __repr__(self) -> str:
        return (
            f"<Cluster(cluster_id={self.cluster_id}, name={self.name!r}, "
            f"algorithm={self.algorithm!r})>"
        )


class Researcher(Base):
    __tablename__ = "researchers"

    researcher_id: Mapped[int] = mapped_column(primary_key=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.lab_id"))
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(255))
    h_index: Mapped[int] = mapped_column(default=0)
    citation_count: Mapped[int] = mapped_column(default=0)
    publication_count: Mapped[int] = mapped_column(default=0)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    cluster_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("clusters.cluster_id"), nullable=True
    )

    lab: Mapped["Lab"] = relationship(back_populates="researchers")
    cluster: Mapped[Optional["Cluster"]] = relationship(back_populates="researchers")
    publications: Mapped[List["ResearcherPublication"]] = relationship(
        back_populates="researcher", cascade="all, delete-orphan"
    )
    expertise: Mapped[List["Expertise"]] = relationship(
        back_populates="researcher", cascade="all, delete-orphan"
    )
    collaborations_a: Mapped[List["Collaboration"]] = relationship(
        back_populates="researcher_a",
        foreign_keys="Collaboration.researcher_a_id",
        cascade="all, delete-orphan",
    )
    collaborations_b: Mapped[List["Collaboration"]] = relationship(
        back_populates="researcher_b",
        foreign_keys="Collaboration.researcher_b_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_researchers_lab_id", "lab_id"),
        Index("ix_researchers_cluster_id", "cluster_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Researcher(researcher_id={self.researcher_id}, name={self.name!r}, "
            f"lab_id={self.lab_id}, h_index={self.h_index})>"
        )


class Publication(Base):
    __tablename__ = "publications"

    publication_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    year: Mapped[Optional[int]] = mapped_column(default=None)
    citation_count: Mapped[int] = mapped_column(default=0)
    venue: Mapped[Optional[str]] = mapped_column(String(255))
    abstract: Mapped[Optional[str]] = mapped_column(String(5000))

    researchers: Mapped[List["ResearcherPublication"]] = relationship(
        back_populates="publication", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Publication(publication_id={self.publication_id}, "
            f"title={self.title!r}, year={self.year})>"
        )


class ResearcherPublication(Base):
    __tablename__ = "researcher_publications"

    researcher_id: Mapped[int] = mapped_column(
        ForeignKey("researchers.researcher_id"), primary_key=True
    )
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.publication_id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(20))

    researcher: Mapped["Researcher"] = relationship(back_populates="publications")
    publication: Mapped["Publication"] = relationship(back_populates="researchers")

    def __repr__(self) -> str:
        return (
            f"<ResearcherPublication(researcher_id={self.researcher_id}, "
            f"publication_id={self.publication_id}, role={self.role!r})>"
        )


class Expertise(Base):
    __tablename__ = "expertise"

    expertise_id: Mapped[int] = mapped_column(primary_key=True)
    researcher_id: Mapped[int] = mapped_column(ForeignKey("researchers.researcher_id"))
    area: Mapped[str] = mapped_column(String(255))
    keywords: Mapped[Optional[str]] = mapped_column(String(1000))
    tfidf_score: Mapped[float] = mapped_column(default=0.0)

    researcher: Mapped["Researcher"] = relationship(back_populates="expertise")

    def __repr__(self) -> str:
        return (
            f"<Expertise(expertise_id={self.expertise_id}, "
            f"researcher_id={self.researcher_id}, area={self.area!r})>"
        )


class Collaboration(Base):
    __tablename__ = "collaborations"

    collab_id: Mapped[int] = mapped_column(primary_key=True)
    researcher_a_id: Mapped[int] = mapped_column(
        ForeignKey("researchers.researcher_id")
    )
    researcher_b_id: Mapped[int] = mapped_column(
        ForeignKey("researchers.researcher_id")
    )
    similarity_score: Mapped[float] = mapped_column(default=0.0)
    utility_a: Mapped[float] = mapped_column(default=0.0)
    utility_b: Mapped[float] = mapped_column(default=0.0)
    nash_value: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    researcher_a: Mapped["Researcher"] = relationship(
        back_populates="collaborations_a", foreign_keys=[researcher_a_id]
    )
    researcher_b: Mapped["Researcher"] = relationship(
        back_populates="collaborations_b", foreign_keys=[researcher_b_id]
    )

    def __repr__(self) -> str:
        return (
            f"<Collaboration(collab_id={self.collab_id}, "
            f"a={self.researcher_a_id}, b={self.researcher_b_id}, "
            f"status={self.status!r})>"
        )
