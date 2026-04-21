"""
Offline pipeline to build FAISS index for IT roles from CSV.
Uses backend/apps/documents/data/IT_Job_Roles_Skills.csv and core embedding service.
convert IT job roles into embeddings and store them in a FAISS vector database for semantic search.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict

import pandas as pd
from django.conf import settings

from core.services.embedding_service import encode
from .role_faiss_manager import RoleFAISSManager

logger = logging.getLogger(__name__)

# Column name constants — single source of truth
COL_TITLE       = "Job Title"
COL_DESCRIPTION = "Job Description"
COL_SKILLS      = "Skills"
COL_CERTS       = "Certifications"
REQUIRED_COLS   = {COL_TITLE, COL_DESCRIPTION, COL_SKILLS}

DOCUMENTS_DATA_CSV = Path(settings.BASE_DIR) / "apps" / "documents" / "data" / "IT_Job_Roles_Skills.csv"


class RolePipelineException(Exception):
    """Pipeline / dataset error."""
    pass


class RoleEmbeddingPipeline:
    """Build FAISS index for IT roles from CSV (Job Title, Job Description, Skills)."""

    def __init__(self) -> None:
        self.dataset_path = DOCUMENTS_DATA_CSV
        if not self.dataset_path.exists():
            raise RolePipelineException(
                f"Dataset not found: {self.dataset_path} "
                f"(expected backend/apps/documents/data/IT_Job_Roles_Skills.csv)"
            )

    def run(self) -> None:
        logger.info("Loading roles dataset...")
        df = pd.read_csv(self.dataset_path, encoding="latin1")

        if not REQUIRED_COLS.issubset(df.columns):
            raise RolePipelineException(f"Dataset must contain columns: {REQUIRED_COLS}")

        df = df.dropna(subset=list(REQUIRED_COLS))
        logger.info("Loaded %s roles.", len(df))

        texts    = self._build_role_text(df)
        metadata = self._build_metadata(df)

        logger.info("Generating embeddings (batch, normalized)...")
        vectors = encode(texts, normalize=True, return_numpy=True)

        logger.info("Building FAISS index...")
        manager = RoleFAISSManager()
        manager.create_index(vectors, metadata)
        logger.info("FAISS build complete.")

    def _build_role_text(self, df: pd.DataFrame) -> List[str]:
        texts = []
        for _, row in df.iterrows():
            title  = str(row[COL_TITLE]).strip()
            desc   = str(row[COL_DESCRIPTION]).strip()
            skills = str(row[COL_SKILLS]).strip()
            texts.append(
                f"Job Title: {title}. "
                f"Job Description: {desc}. "
                f"Required Skills: {skills}."
            )
        return texts

    def _build_metadata(self, df: pd.DataFrame) -> List[Dict]:
        metadata = []
        has_certs = COL_CERTS in df.columns
        for _, row in df.iterrows():
            meta = {
                "role":        row[COL_TITLE],
                "skills":      row[COL_SKILLS],
                "description": row[COL_DESCRIPTION],
                "certifications": (
                    str(row[COL_CERTS]).strip()
                    if has_certs and pd.notna(row.get(COL_CERTS))
                    else ""
                ),
            }
            metadata.append(meta)
        return metadata