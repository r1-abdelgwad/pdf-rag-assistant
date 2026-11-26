"""Tests of the RAG pipeline using fake store / LLM (no network, no model downloads)."""
from app.models import Hit
from app.services.chat import NO_DOCUMENTS_MESSAGE, answer_question
from app.services.llm import NOT_FOUND_MESSAGE


class FakeStore:
    def __init__(self, hits, count=1):
        self._hits, self._count = hits, count

    def count(self):
        return self._count

    def search(self, query, k, max_distance):
        self.last_query = query
        return self._hits


class FakeLLM:
    def __init__(self, answer="Some answer."):
        self._answer = answer
        self.answer_calls = 0

    def rewrite_question(self, question, history):
        return "standalone: " + question

    def answer(self, question, hits, history):
        self.answer_calls += 1
        return self._answer


HIT = Hit(source="a.pdf", page=2, text="Employees get 25 days of leave.", distance=0.3)


def test_empty_knowledge_base_does_not_call_llm():
    llm = FakeLLM()
    result = answer_question("hi", [], FakeStore([], count=0), llm)
    assert result.answer == NO_DOCUMENTS_MESSAGE and llm.answer_calls == 0


def test_answer_includes_sources():
    result = answer_question("How much leave?", [], FakeStore([HIT, HIT]), FakeLLM())
    assert len(result.sources) == 1  # same document + page is listed once
    assert result.sources[0]["document"] == "a.pdf" and result.sources[0]["page"] == 2


def test_not_found_answer_has_no_sources():
    result = answer_question("Who won the world cup?", [], FakeStore([HIT]), FakeLLM(NOT_FOUND_MESSAGE))
    assert result.sources == []


def test_no_relevant_passages_means_no_sources():
    result = answer_question("hello", [], FakeStore([]), FakeLLM("Hi! Ask me about your documents."))
    assert result.sources == []


def test_follow_up_is_rewritten_before_search():
    store = FakeStore([HIT])
    history = [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}]
    answer_question("and for contractors?", history, store, FakeLLM())
    assert store.last_query == "standalone: and for contractors?"
