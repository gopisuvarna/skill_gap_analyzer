import json

import numpy as np
import pytest

from apps.roles.services import ranking_engine, scoring, similarity
from apps.roles.services.faiss_role_index import FAISSRoleIndex
from apps.roles.services.role_faiss_manager import RoleFAISSManager, VectorDBError
from apps.roles.services import faiss_role_index, role_faiss_manager, skill_intelligence
from apps.skills.services import skill_extractor, skill_matcher


class TestScoringAndRankingUtilities:
    def test_scoring_handles_matches_and_empty_inputs(self):
        assert scoring.skill_coverage({"python"}, {"python", "sql"}) == 0.5
        assert scoring.skill_coverage({"python"}, set()) == 0.0
        assert scoring.importance_weight({"python", "sql"}, {"python": 0.8}) == 0.8
        assert scoring.importance_weight({"java"}, {"python": 0.8}) == 0.0

    def test_similarity_tokenise_and_bm25_variants(self, monkeypatch):
        monkeypatch.setattr(similarity, "skill_importance", lambda token: 0.9 if token == "python" else 0.4)

        assert similarity.tokenise(["Python", "", "Cloud Security"]) == ["python", "cloud_security"]
        assert similarity.bm25_raw([], ["python"]) == 0.0
        assert similarity.bm25_raw(["python"], []) == 0.0
        assert similarity.bm25_raw(["python"], ["python", "sql"]) > 0
        assert similarity.bm25_raw(["missing"], ["python"]) == 0.0
        assert similarity.bm25_intelligence(["Python"], ["Python", "SQL"]) > 0
        assert similarity.bm25_intelligence([], ["Python"]) == 0.0

    def test_re_rank_sorts_and_limits_candidates(self, monkeypatch):
        monkeypatch.setattr(ranking_engine, "bm25_intelligence", lambda user, role: 0.5 if "Python" in role else 0.1)
        monkeypatch.setattr(ranking_engine, "bm25_raw", lambda user, role: 0.25)

        ranked = ranking_engine.re_rank(
            candidate_roles=[{"id": "2", "title": "SQL"}, {"id": "1", "title": "Python"}],
            user_skill_ids={"s1"},
            user_skill_names=["Python"],
            role_skills_map={
                "1": [{"skill_id": "s1", "skill_name": "Python", "importance_weight": 0.8}],
                "2": [{"skill_id": "s2", "skill_name": "SQL", "importance_weight": 0.4}],
            },
            top_k=1,
        )

        assert ranked == [
            {
                "id": "1",
                "title": "Python",
                "match_score": 0.735,
                "skill_coverage": 1.0,
                "importance_score": 0.8,
                "bm25_score": 0.5,
                "bm25_raw_score": 0.25,
            }
        ]


class TestSkillIntelligence:
    def setup_method(self):
        skill_intelligence._SKILL_SCORES = None

    def teardown_method(self):
        skill_intelligence._SKILL_SCORES = None

    def test_score_helpers_compute_normalized_values(self):
        docs = [
            {"python", "django", "sql"},
            {"python", "aws"},
            {"sql", "aws"},
        ]

        assert skill_intelligence._normalize_skills(" Python, SQL ,, ") == {"python", "sql"}
        assert skill_intelligence._normalize_skills(["AWS", "", 123]) == {"aws"}
        assert skill_intelligence._minmax({}) == {}
        assert skill_intelligence._minmax({"a": 2.0, "b": 2.0}) == {"a": 0.0, "b": 0.0}
        assert skill_intelligence._semantic_idf(docs)["django"] > skill_intelligence._semantic_idf(docs)["python"]
        assert skill_intelligence._market_demand(docs)["python"] == skill_intelligence._market_demand(docs)["sql"]
        assert skill_intelligence._graph_importance(docs)
        assert skill_intelligence._graph_importance([{"solo"}]) == {}
        assert "django" in skill_intelligence._tfidf_distinctiveness(docs)

    def test_get_skill_scores_uses_memory_cache_disk_cache_and_csv_fallbacks(self, tmp_path, monkeypatch):
        skill_intelligence._SKILL_SCORES = {"python": 0.7}
        assert skill_intelligence.get_skill_scores() == {"python": 0.7}

        cache = tmp_path / "skill_scores.json"
        cache.write_text(json.dumps({"sql": 0.4}), encoding="utf-8")
        monkeypatch.setattr(skill_intelligence, "_CACHE_PATH", cache)
        monkeypatch.setattr(skill_intelligence, "_CSV_PATH", tmp_path / "missing.csv")
        skill_intelligence._SKILL_SCORES = None
        assert skill_intelligence.get_skill_scores() == {"sql": 0.4}

        cache.write_text("{bad json", encoding="utf-8")
        skill_intelligence._SKILL_SCORES = None
        assert skill_intelligence.get_skill_scores() == {}

        csv_path = tmp_path / "roles.csv"
        csv_path.write_text('Skills\n"Python, Django"\n"Python, SQL"\n', encoding="latin1")
        monkeypatch.setattr(skill_intelligence, "_CSV_PATH", csv_path)
        skill_intelligence._SKILL_SCORES = None
        scores = skill_intelligence.get_skill_scores()
        assert {"python", "django", "sql"} <= set(scores)
        assert skill_intelligence.skill_importance("unknown_skill") == 0.1
        assert skill_intelligence.skill_importance("python") >= 0.1


class TestFaissManagers:
    def test_role_faiss_manager_create_load_search_and_errors(self, tmp_path, monkeypatch):
        monkeypatch.setattr(role_faiss_manager, "FAISS_DIR", tmp_path)
        manager = RoleFAISSManager()

        with pytest.raises(VectorDBError, match="mismatch"):
            manager.create_index(np.array([[1.0, 0.0]], dtype=np.float32), [])
        with pytest.raises(VectorDBError, match="Nothing to save"):
            manager._save()

        vectors = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        manager.create_index(vectors, [{"role": "python"}, {"role": "sql"}])
        assert manager.search(np.array([1.0, 0.0], dtype=np.float32), top_k=2)[0][1] == {"role": "python"}

        loaded = RoleFAISSManager()
        monkeypatch.setattr(loaded, "index_path", manager.index_path)
        monkeypatch.setattr(loaded, "metadata_path", manager.metadata_path)
        loaded.load()
        assert loaded.search(np.array([[0.0, 1.0]], dtype=np.float32), top_k=1)[0][1] == {"role": "sql"}

        missing = RoleFAISSManager()
        monkeypatch.setattr(missing, "index_path", tmp_path / "missing.index")
        with pytest.raises(VectorDBError, match="not found"):
            missing.load()

    def test_db_faiss_index_build_load_search_and_singleton(self, tmp_path, monkeypatch):
        monkeypatch.setattr(faiss_role_index, "INDEX_PATH", tmp_path / "roles.index")
        monkeypatch.setattr(faiss_role_index, "MAPPING_PATH", tmp_path / "roles.txt")
        monkeypatch.setattr(faiss_role_index, "_faiss_index", None)

        index = FAISSRoleIndex()
        index.build([], [])
        assert index.search([1.0, 0.0]) == []

        index.build([[1.0, 0.0], [0.0, 1.0]], ["role-1", "role-2"])
        assert index.search([1.0, 0.0], k=1)[0][0] == "role-1"

        loaded = FAISSRoleIndex()
        assert loaded.load() is True
        assert loaded.id_list == ["role-1", "role-2"]
        assert faiss_role_index.get_faiss_index().id_list == ["role-1", "role-2"]


class TestSkillExtractionServices:
    def teardown_method(self):
        skill_extractor.SkillExtractor._nlp = None
        skill_extractor.SkillExtractor._matcher = None

    def test_rule_based_extractor_returns_sorted_matches(self, monkeypatch):
        class Span:
            def __init__(self, text):
                self.text = text

        class FakeDoc:
            def __init__(self, words):
                self.words = words

            def __getitem__(self, item):
                return Span(" ".join(self.words[item]))

        def fake_initialize():
            skill_extractor.SkillExtractor._nlp = lambda text: FakeDoc(text.split())
            skill_extractor.SkillExtractor._matcher = lambda doc: [(None, 0, 1), (None, 1, 2)]

        monkeypatch.setattr(skill_extractor.SkillExtractor, "_initialize", fake_initialize)

        assert skill_extractor.SkillExtractor.extract("") == []
        assert skill_extractor.SkillExtractor.extract("Python Django") == ["django", "python"]

    def test_rule_based_initialize_wraps_spacy_model_errors(self, monkeypatch):
        skill_extractor.SkillExtractor._nlp = None
        monkeypatch.setattr(skill_extractor.spacy, "load", lambda name: (_ for _ in ()).throw(OSError("missing")))

        with pytest.raises(skill_extractor.SkillExtractorError, match="Failed to initialize"):
            skill_extractor.SkillExtractor._initialize()

    def test_llm_extractor_parses_json_and_handles_invalid_payloads(self, monkeypatch):
        class Message:
            content = "```json\n{\"skills\": [\"Python\", \"SQL\", \"python\"]}\n```"

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        monkeypatch.setattr(
            skill_extractor._groq_client.chat.completions,
            "create",
            lambda **kwargs: Response(),
        )

        assert sorted(skill_extractor.LLMSkillExtractor().extract("resume")) == ["python", "sql"]
        assert skill_extractor.LLMSkillExtractor().extract("") == []

        Message.content = "{\"skills\": \"python\"}"
        assert skill_extractor.LLMSkillExtractor().extract("resume") == []
        Message.content = "not json"
        assert skill_extractor.LLMSkillExtractor().extract("resume") == []

    def test_skill_tool_combines_and_normalizes_skills(self, monkeypatch):
        monkeypatch.setattr(skill_matcher.SkillTool.rule_extractor, "extract", lambda text: ["Python", "python", ""])
        monkeypatch.setattr(skill_matcher.SkillTool.llm_extractor, "extract", lambda text: ["Django", "SQL"])
        monkeypatch.setattr(skill_matcher, "normalize_skill", lambda skill: skill.strip().title())

        assert skill_matcher.SkillTool.run("", use_llm=True) == {
            "rule_based_skills": [],
            "llm_skills": [],
            "all_skills": [],
        }
        assert skill_matcher.SkillTool.run("resume", use_llm=True)["all_skills"] == ["", "Django", "Python", "SQL", "python"]
        assert skill_matcher.SkillTool.run("resume", use_llm=False)["llm_skills"] == []
        assert skill_matcher.extract_skills("", use_llm=True) == []
        assert skill_matcher.extract_skills("resume", use_llm=True) == ["Django", "Python", "Sql"]
