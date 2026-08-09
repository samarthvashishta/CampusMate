# Basic RAG evaluation using RAGAS.
#
# For a handful of sample questions (one or two per topic), we:
#   1. retrieve context chunks from ChromaDB (same as the real agents do)
#   2. ask the LLM to answer using only that context
#   3. hand the (question, context, answer) triple to RAGAS, which scores:
#       - Faithfulness      : is the answer actually backed by the context?
#       - Answer Relevancy  : does the answer actually address the question?
#
# Both scores are 0.0-1.0 (higher is better). This is a basic sanity
# check that the RAG pipeline is retrieving relevant data
#
# Note: RAGAS talks to the LLM through an OpenAI-style client, so we
# point it at Gemini's OpenAI-compatible endpoint instead of Google's
# native SDK - ragas's own native Gemini adapter has a known bug
# (sends an invalid safety setting Gemini rejects). This way is what
# RAGAS itself recommends as the workaround.
#
# Run with:  python -m rag.evaluate


import sys
import time
import types

# ragas imports ChatVertexAI just to do an isinstance() check, but that
# module was removed from the langchain-community version installed in
# this project. We don't use VertexAI at all, so a harmless stand-in
# module is enough to let ragas import normally.
stub = types.ModuleType("langchain_community.chat_models.vertexai")
stub.ChatVertexAI = type("ChatVertexAI", (), {})
sys.modules["langchain_community.chat_models.vertexai"] = stub

from openai import AsyncOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from ragas.embeddings import HuggingFaceEmbeddings as RagasEmbeddings
from ragas.llms import llm_factory
from ragas.metrics.collections import AnswerRelevancy, Faithfulness

from backend.rag.config import EMBEDDING_MODEL, GEMINI_API_KEY
from backend.rag.vectorstore import get_store

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0, api_key=GEMINI_API_KEY)

# RAGAS's own scoring LLM, talking to Gemini's OpenAI-compatible endpoint.
gemini_openai_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
# max_tokens is raised because RAGAS's own scoring calls (breaking the
# answer into statements, then checking each one) can get cut off on
# longer answers otherwise, which crashes the whole run.
ragas_llm = llm_factory(
    "gemini-3.1-flash-lite", provider="openai", client=gemini_openai_client, max_tokens=4096
)
ragas_embeddings = RagasEmbeddings(model=EMBEDDING_MODEL)

faithfulness_metric = Faithfulness(llm=ragas_llm)
relevancy_metric = AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings)

# A few sample questions, one or two per RAG topic that has real data.
TEST_QUESTIONS = [
    ("syllabus", "What is recursion in programming?"),
    ("placement", "What CGPA does TCS require for a Data Analyst role?"),
    ("pyqs", "Give an example of a previous year DBMS question."),
    ("wellness", "I am in stress."),
]


def get_text(response):
    content = response.content
    return content if isinstance(content, str) else content[0]["text"]


def run_evaluation():
    print(f"{'question':<55} {'faithfulness':>12} {'relevancy':>10}")
    print("-" * 80)

    faithfulness_scores = []
    relevancy_scores = []

    for i, (topic, question) in enumerate(TEST_QUESTIONS):
        if i > 0:
            # Free-tier Gemini keys allow ~15 requests/minute, and each
            # question triggers several RAGAS scoring calls - a short
            # pause between questions avoids hitting that limit.
            time.sleep(20)

        # Step 1: retrieve context, same as the real agents do.
        docs = get_store(topic).similarity_search(question, k=4)
        contexts = [doc.page_content for doc in docs]

        print("\n========== DEBUG ==========")
        print("Topic:", topic)
        print("Question:", question)
        print("Docs Retrieved:", len(docs))

        for i, d in enumerate(docs):
            print(f"\nChunk {i+1}:")
            print(d.page_content[:300])

        # Step 2: generate an answer using only that context.
        prompt = (
            f"Context:\n{chr(10).join(contexts)}\n\n"
            f"Question: {question}\n\n"
            "Answer using only the context above."
        )
        answer = get_text(llm.invoke(prompt))

        # Step 3: score with RAGAS. Wrapped in try/except so one question
        # having a scoring hiccup doesn't stop the rest of the report.
        try:
            faithfulness = faithfulness_metric.score(
                user_input=question, response=answer, retrieved_contexts=contexts
            ).value
            relevancy = relevancy_metric.score(user_input=question, response=answer).value
            faithfulness_scores.append(faithfulness)
            relevancy_scores.append(relevancy)
            print(f"{question:<55} {faithfulness:>12.2f} {relevancy:>10.2f}")
        except Exception as error:
            print(f"{question:<55} {'FAILED: ' + str(error)[:40]}")

    print("-" * 80)
    if faithfulness_scores:
        print(f"{'AVERAGE':<55} {sum(faithfulness_scores)/len(faithfulness_scores):>12.2f} "
              f"{sum(relevancy_scores)/len(relevancy_scores):>10.2f}")


if __name__ == "__main__":
    run_evaluation()