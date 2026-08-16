from rag.embeddings import embed_query, embed_texts


def test_embed_texts_returns_one_vector_per_input():
    vectors = embed_texts(["def foo(): pass", "class Bar: pass"])
    assert len(vectors) == 2
    assert all(len(v) > 0 for v in vectors)


def test_embed_texts_empty_input():
    assert embed_texts([]) == []


def test_embed_query_is_deterministic_for_same_text():
    a = embed_query("how does auth work")
    b = embed_query("how does auth work")
    assert a == b


def test_embed_query_differs_for_different_text():
    a = embed_query("authentication middleware")
    b = embed_query("database connection pooling")
    assert a != b
