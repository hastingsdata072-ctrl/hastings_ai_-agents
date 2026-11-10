"""
Hastings RAG Studio — Streamlit entry point.

Milestone 4: Persistent chat, evaluation dashboard,
model selection, settings page.
"""

import streamlit as st

st.set_page_config(
    page_title="Hastings RAG Studio",
    page_icon="🧠",
    layout="wide",
)

# ── Available Groq models ─────────────────────────────────────────────────────

GROQ_MODELS = {
    "GPT OSS 120B (flagship)": "openai/gpt-oss-120b",
    "GPT OSS 20B (fast)":      "openai/gpt-oss-20b",
    "Llama 3.1 8B (fastest)":  "llama-3.1-8b-instant",
    "Llama 3.3 70B":           "llama-3.3-70b-versatile",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🧠 Hastings RAG Studio")
    st.caption("*Your documents. Your knowledge. Your intelligence.*")
    st.divider()
    page = st.radio(
        "Navigate",
        [
            "💬 Ask a Question",
            "🔬 RAG Lab",
            "📊 Evaluation",
            "📁 Knowledge Bases",
            "📤 Upload Documents",
            "⚙️ System Status",
            "🛠️ Settings",
        ],
        label_visibility="collapsed",
    )
    st.divider()

# ── System Status ─────────────────────────────────────────────────────────────

if page == "⚙️ System Status":
    st.header("⚙️ System Status")
    from src.health import run_health_checks

    labels = {
        "database":        "PostgreSQL Database",
        "pgvector":        "pgvector Extension",
        "embedding_model": "Embedding Model",
        "groq_key":        "Groq API Key",
    }
    with st.spinner("Running health checks…"):
        results = run_health_checks()

    all_ok = all(r["status"] == "ok" for r in results.values())
    st.success("All systems operational.") if all_ok else st.error("One or more components need attention.")
    st.divider()

    for key, label in labels.items():
        result = results[key]
        badge = "✅" if result["status"] == "ok" else "❌"
        c1, c2 = st.columns([1, 5])
        with c1:
            st.markdown(f"## {badge}")
        with c2:
            st.markdown(f"**{label}**")
            st.caption(result["message"]) if result["status"] == "ok" else st.error(result["message"])
        st.divider()

    if st.button("🔄 Refresh"):
        st.rerun()

# ── Settings ──────────────────────────────────────────────────────────────────

elif page == "🛠️ Settings":
    st.header("🛠️ Settings")
    st.markdown("These settings apply for the current session.")

    from src.config import config

    st.subheader("Retrieval defaults")
    new_top_k = st.slider("Default top-k passages", 1, 15, config.top_k)
    new_chunk_size = st.number_input("Chunk size (characters)", 200, 4000, config.chunk_size, step=100)
    new_chunk_overlap = st.number_input("Chunk overlap (characters)", 0, 500, config.chunk_overlap, step=50)

    st.subheader("Model")
    model_label = st.selectbox("Default Groq model", list(GROQ_MODELS.keys()))
    selected_model = GROQ_MODELS[model_label]
    st.caption(f"Model ID: `{selected_model}`")

    if st.button("💾 Save to session", type="primary"):
        st.session_state["settings"] = {
            "top_k": new_top_k,
            "chunk_size": new_chunk_size,
            "chunk_overlap": new_chunk_overlap,
            "groq_model": selected_model,
        }
        st.success("Settings saved for this session.")

    st.divider()
    st.subheader("Current .env values")
    st.code(f"""GROQ_MODEL={config.groq_model}
EMBEDDING_MODEL={config.embedding_model}
CHUNK_SIZE={config.chunk_size}
CHUNK_OVERLAP={config.chunk_overlap}
TOP_K={config.top_k}""", language="bash")
    st.caption("To persist settings across restarts, edit the .env file.")

# ── Knowledge Bases ───────────────────────────────────────────────────────────

elif page == "📁 Knowledge Bases":
    st.header("📁 Knowledge Bases")
    from src.db.connection import get_connection
    from src.db.queries import (
        create_knowledge_base, delete_knowledge_base, delete_document,
        list_knowledge_bases, get_chunk_count, list_documents,
    )

    with st.expander("➕ Create a new knowledge base", expanded=False):
        with st.form("create_kb"):
            kb_name = st.text_input("Name", placeholder="e.g. Legal Documents 2026")
            kb_desc = st.text_area("Description (optional)", height=80)
            if st.form_submit_button("Create"):
                if not kb_name.strip():
                    st.error("Name is required.")
                else:
                    try:
                        with get_connection() as conn:
                            create_knowledge_base(conn, kb_name.strip(), kb_desc.strip())
                        st.success(f"'{kb_name}' created.")
                        st.rerun()
                    except Exception as e:
                        st.error("Name already exists." if "unique" in str(e).lower() else str(e))

    st.divider()

    with get_connection() as conn:
        kbs = list_knowledge_bases(conn)

    if not kbs:
        st.info("No knowledge bases yet. Create one above.")
    else:
        for kb in kbs:
            with get_connection() as conn:
                chunk_count = get_chunk_count(conn, kb["id"])
                docs = list_documents(conn, kb["id"])

            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"### {kb['name']}")
                    if kb.get("description"):
                        st.caption(kb["description"])
                    st.caption(f"{len(docs)} doc(s) · {chunk_count} chunks · Created {kb['created_at'].strftime('%Y-%m-%d')}")
                with c2:
                    if st.button("🗑️ Delete", key=f"delkb_{kb['id']}"):
                        st.session_state[f"confirm_{kb['id']}"] = True

                if st.session_state.get(f"confirm_{kb['id']}"):
                    st.warning(f"Delete **{kb['name']}** and all its documents?")
                    y, n = st.columns(2)
                    with y:
                        if st.button("Yes, delete", key=f"yes_{kb['id']}"):
                            with get_connection() as conn:
                                delete_knowledge_base(conn, kb["id"])
                            st.session_state.pop(f"confirm_{kb['id']}", None)
                            st.rerun()
                    with n:
                        if st.button("Cancel", key=f"no_{kb['id']}"):
                            st.session_state.pop(f"confirm_{kb['id']}", None)
                            st.rerun()

                if docs:
                    with st.expander(f"📄 {len(docs)} document(s)"):
                        for doc in docs:
                            dc1, dc2 = st.columns([5, 1])
                            with dc1:
                                pages = f"{doc['page_count']}p · " if doc.get("page_count") else ""
                                st.markdown(f"**{doc['filename']}** — {pages}{doc['chunk_count']} chunks")
                            with dc2:
                                if st.button("🗑️", key=f"deldoc_{doc['id']}"):
                                    with get_connection() as conn:
                                        delete_document(conn, doc["id"])
                                    st.rerun()

# ── Upload Documents ──────────────────────────────────────────────────────────

elif page == "📤 Upload Documents":
    st.header("📤 Upload Documents")
    from src.db.connection import get_connection
    from src.db.queries import list_knowledge_bases
    from src.ingestion.pipeline import ingest_document

    with get_connection() as conn:
        kbs = list_knowledge_bases(conn)

    if not kbs:
        st.warning("Create a knowledge base first.")
    else:
        kb_map = {kb["name"]: kb["id"] for kb in kbs}
        selected = st.selectbox("Select knowledge base", list(kb_map.keys()))
        kb_id = kb_map[selected]

        files = st.file_uploader(
            "Choose files",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
        )

        if files and st.button("📥 Index selected files", type="primary"):
            for f in files:
                with st.status(f"Processing {f.name}…", expanded=True) as status:
                    result = ingest_document(kb_id, f.name, f.read())
                    if result.duplicate:
                        status.update(label=f"⚠️ {f.name} — already uploaded", state="error")
                        st.warning(result.message)
                    elif result.success:
                        status.update(label=f"✅ {f.name} — {result.chunk_count} chunks", state="complete")
                        st.success(result.message)
                    else:
                        status.update(label=f"❌ {f.name} — failed", state="error")
                        st.error(result.message)

# ── Ask a Question ────────────────────────────────────────────────────────────

elif page == "💬 Ask a Question":
    st.header("💬 Ask a Question")
    from src.db.connection import get_connection
    from src.db.queries import list_knowledge_bases, get_chunk_count
    from src.db.chat_history import (
        init_chat_tables, create_conversation, list_conversations,
        delete_conversation, add_message, get_messages,
        export_conversation_markdown, export_conversation_json,
        update_conversation_title,
    )
    from src.generation.groq_client import generate_answer
    from src.config import config

    # Ensure chat tables exist
    with get_connection() as conn:
        init_chat_tables(conn)
        kbs = list_knowledge_bases(conn)

    if not kbs:
        st.warning("Create a knowledge base and upload documents first.")
    else:
        settings = st.session_state.get("settings", {})
        default_model = settings.get("groq_model", config.groq_model)
        default_top_k = settings.get("top_k", config.top_k)

        with st.sidebar:
            kb_map = {kb["name"]: kb["id"] for kb in kbs}
            selected_kb = st.selectbox("Knowledge base", list(kb_map.keys()), key="chat_kb")
            kb_id = kb_map[selected_kb]

            with get_connection() as conn:
                chunk_count = get_chunk_count(conn, kb_id)
            st.caption(f"{chunk_count} chunks indexed")

            st.markdown("**Model**")
            model_label = st.selectbox(
                "Model", list(GROQ_MODELS.keys()),
                index=list(GROQ_MODELS.values()).index(default_model)
                      if default_model in GROQ_MODELS.values() else 0,
                key="chat_model",
            )
            selected_model = GROQ_MODELS[model_label]

            st.markdown("**Retrieval**")
            retrieval_mode = st.selectbox(
                "Mode",
                ["Vector only", "Hybrid (Vector + BM25)", "Hybrid + Rerank"],
                key="chat_retrieval",
            )
            top_k = st.slider("Passages", 1, 10, default_top_k, key="chat_topk")

            st.markdown("**Features**")
            use_query_rewrite = st.toggle("Query rewriting", value=False)
            use_compression   = st.toggle("Context compression", value=False)
            use_verification  = st.toggle("Citation verification", value=False)

            st.divider()
            st.markdown("**Conversations**")

            # Load conversations for this KB
            with get_connection() as conn:
                convos = list_conversations(conn, kb_id)

            if st.button("➕ New conversation"):
                with get_connection() as conn:
                    new_conv = create_conversation(conn, kb_id)
                st.session_state["active_conversation_id"] = new_conv["id"]
                st.rerun()

            for conv in convos:
                is_active = st.session_state.get("active_conversation_id") == conv["id"]
                label = f"{'▶ ' if is_active else ''}{conv['title'][:30]}"
                if st.button(label, key=f"conv_{conv['id']}"):
                    st.session_state["active_conversation_id"] = conv["id"]
                    st.rerun()

        # Set active conversation
        conv_id = st.session_state.get("active_conversation_id")
        if not conv_id or not any(c["id"] == conv_id for c in convos):
            if convos:
                conv_id = convos[0]["id"]
                st.session_state["active_conversation_id"] = conv_id
            else:
                with get_connection() as conn:
                    new_conv = create_conversation(conn, kb_id)
                conv_id = new_conv["id"]
                st.session_state["active_conversation_id"] = conv_id

        # Load messages from DB
        with get_connection() as conn:
            db_messages = get_messages(conn, conv_id)

        # Display messages
        for msg in db_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander("📚 Sources"):
                        for src in msg["sources"]:
                            pg = f", page {src['page_number']}" if src.get("page_number") else ""
                            st.markdown(f"**{src['label']}** — `{src['filename']}`{pg} *(score: {src['score']:.4f})*")
                            st.caption(src["content"][:400] + ("…" if len(src["content"]) > 400 else ""))
                            st.divider()
                if msg.get("meta"):
                    st.caption(msg["meta"])

        # Export buttons
        if db_messages:
            active_conv = next((c for c in convos if c["id"] == conv_id), None)
            conv_title = active_conv["title"] if active_conv else "Conversation"
            e1, e2, e3 = st.columns([1, 1, 5])
            with e1:
                md_export = export_conversation_markdown(db_messages, conv_title, selected_kb)
                st.download_button("⬇️ Markdown", md_export, file_name="conversation.md", mime="text/markdown")
            with e2:
                json_export = export_conversation_json(db_messages, conv_title, selected_kb)
                st.download_button("⬇️ JSON", json_export, file_name="conversation.json", mime="application/json")
            with e3:
                if st.button("🗑️ Delete conversation"):
                    with get_connection() as conn:
                        delete_conversation(conn, conv_id)
                    st.session_state.pop("active_conversation_id", None)
                    st.rerun()

        # Chat input
        if question := st.chat_input("Ask a question about your documents…"):
            if chunk_count == 0:
                st.warning("No documents indexed yet.")
            else:
                # Save user message
                with get_connection() as conn:
                    add_message(conn, conv_id, "user", question)
                    # Auto-title from first question
                    active_conv = next((c for c in convos if c["id"] == conv_id), None)
                    if active_conv and active_conv["title"] == "New conversation":
                        update_conversation_title(conn, conv_id, question[:60])

                with st.chat_message("user"):
                    st.markdown(question)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking…"):
                        retrieval_query = question
                        rewritten = None
                        if use_query_rewrite:
                            from src.retrieval.query_rewriter import rewrite_query
                            rewritten = rewrite_query(question, model=selected_model)
                            if rewritten != question:
                                retrieval_query = rewritten

                        if retrieval_mode == "Vector only":
                            from src.retrieval.vector_search import retrieve
                            chunks = retrieve(kb_id, retrieval_query, top_k=top_k)
                        elif retrieval_mode == "Hybrid (Vector + BM25)":
                            from src.retrieval.hybrid_search import hybrid_retrieve
                            chunks = hybrid_retrieve(kb_id, retrieval_query, top_k=top_k)
                        else:
                            from src.retrieval.hybrid_search import hybrid_retrieve
                            from src.retrieval.reranker import rerank
                            candidates = hybrid_retrieve(kb_id, retrieval_query, top_k=top_k * 2)
                            chunks = rerank(retrieval_query, candidates, top_k=top_k)

                        if use_compression and chunks:
                            from src.retrieval.context_compressor import compress_chunks
                            chunks = compress_chunks(retrieval_query, chunks)

                        result = generate_answer(question, chunks, model=selected_model)

                    st.markdown(result.answer)

                    if rewritten and rewritten != question:
                        st.caption(f"🔄 Rewritten: *{rewritten}*")

                    if use_verification and result.sources:
                        from src.generation.citation_verifier import verify_citations
                        vr = verify_citations(result.answer, chunks)
                        if vr.unsupported_count > 0:
                            st.warning(f"⚠️ {vr.unsupported_count} sentence(s) may not be fully supported. Support rate: {vr.support_rate*100:.0f}%")
                        else:
                            st.success(f"✅ All statements supported. Support rate: {vr.support_rate*100:.0f}%")

                    if result.sources:
                        with st.expander("📚 Sources"):
                            for src in result.sources:
                                pg = f", page {src['page_number']}" if src.get("page_number") else ""
                                st.markdown(f"**{src['label']}** — `{src['filename']}`{pg} *(score: {src['score']:.4f})*")
                                st.caption(src["content"][:400] + ("…" if len(src["content"]) > 400 else ""))
                                st.divider()

                    meta = f"Mode: {retrieval_mode} · Model: {result.model} · {result.prompt_tokens}/{result.completion_tokens} tokens"
                    st.caption(meta)

                # Save assistant message
                with get_connection() as conn:
                    add_message(conn, conv_id, "assistant", result.answer,
                                sources=result.sources, meta=meta)
                st.rerun()

# ── Evaluation Dashboard ──────────────────────────────────────────────────────

elif page == "📊 Evaluation":
    st.header("📊 Retrieval Evaluation")
    st.markdown("Measure retrieval quality with precision@k, recall@k, and MRR.")

    from src.db.connection import get_connection
    from src.db.queries import list_knowledge_bases
    from src.evaluation.eval_runner import run_evaluation

    with get_connection() as conn:
        kbs = list_knowledge_bases(conn)

    if not kbs:
        st.warning("Create a knowledge base and upload documents first.")
    else:
        kb_map = {kb["name"]: kb["id"] for kb in kbs}
        selected_kb = st.selectbox("Knowledge base", list(kb_map.keys()))
        kb_id = kb_map[selected_kb]

        st.subheader("Test questions")
        st.markdown("""
        Add questions and the IDs of relevant chunks. To find chunk IDs,
        ask questions in the RAG Lab and note which chunk IDs appear in results.
        """)

        # Manage test questions in session state
        if "eval_questions" not in st.session_state:
            st.session_state["eval_questions"] = []

        with st.form("add_eval_question"):
            q_text = st.text_input("Question")
            q_ids = st.text_input("Relevant chunk IDs (comma-separated)", placeholder="e.g. 1,2,5")
            if st.form_submit_button("Add question"):
                if q_text.strip():
                    try:
                        ids = [int(x.strip()) for x in q_ids.split(",") if x.strip()]
                        st.session_state["eval_questions"].append({
                            "question": q_text.strip(),
                            "relevant_chunk_ids": ids,
                        })
                        st.success("Question added.")
                        st.rerun()
                    except ValueError:
                        st.error("Chunk IDs must be integers separated by commas.")

        if st.session_state["eval_questions"]:
            st.markdown(f"**{len(st.session_state['eval_questions'])} question(s) in test set:**")
            for i, q in enumerate(st.session_state["eval_questions"]):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**Q{i+1}:** {q['question']}")
                    st.caption(f"Relevant chunk IDs: {q['relevant_chunk_ids']}")
                with c2:
                    if st.button("🗑️", key=f"del_eq_{i}"):
                        st.session_state["eval_questions"].pop(i)
                        st.rerun()

            st.divider()
            st.subheader("Run evaluation")

            eval_k = st.slider("Evaluation k", 1, 10, 5)
            modes = {
                "Vector only": "vector",
                "Hybrid (Vector + BM25)": "hybrid",
                "Hybrid + Rerank": "hybrid_rerank",
            }
            selected_modes = st.multiselect(
                "Retrieval modes to compare",
                list(modes.keys()),
                default=["Vector only", "Hybrid (Vector + BM25)"],
            )

            if st.button("▶️ Run evaluation", type="primary") and selected_modes:
                for mode_label in selected_modes:
                    mode_key = modes[mode_label]
                    with st.spinner(f"Evaluating {mode_label}…"):
                        result = run_evaluation(
                            kb_id,
                            st.session_state["eval_questions"],
                            retrieval_mode=mode_key,
                            k=eval_k,
                        )

                    st.subheader(f"📈 {mode_label}")
                    a = result.aggregate
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"Precision@{eval_k}", f"{a.mean_precision_at_k:.3f}")
                    m2.metric(f"Recall@{eval_k}", f"{a.mean_recall_at_k:.3f}")
                    m3.metric("MRR", f"{a.mrr:.3f}")

                    with st.expander("Per-query results"):
                        for qm in result.per_query:
                            st.markdown(f"**Q:** {qm.query}")
                            cols = st.columns(3)
                            cols[0].metric(f"P@{eval_k}", f"{qm.precision_at_k:.3f}")
                            cols[1].metric(f"R@{eval_k}", f"{qm.recall_at_k:.3f}")
                            cols[2].metric("RR", f"{qm.reciprocal_rank:.3f}")
                            st.divider()
        else:
            st.info("Add at least one question to run the evaluation.")

# ── RAG Intelligence Lab ──────────────────────────────────────────────────────

elif page == "🔬 RAG Lab":
    st.header("🔬 RAG Intelligence Lab")
    st.markdown("Inspect every step of the pipeline with latency metrics.")

    from src.db.connection import get_connection
    from src.db.queries import list_knowledge_bases, get_chunk_count

    with get_connection() as conn:
        kbs = list_knowledge_bases(conn)

    if not kbs:
        st.warning("Create a knowledge base and upload documents first.")
    else:
        with st.sidebar:
            kb_map = {kb["name"]: kb["id"] for kb in kbs}
            selected = st.selectbox("Knowledge base", list(kb_map.keys()), key="lab_kb")
            kb_id = kb_map[selected]
            with get_connection() as conn:
                chunk_count = get_chunk_count(conn, kb_id)
            st.caption(f"{chunk_count} chunks indexed")
            top_k = st.slider("Top K", 1, 10, 5, key="lab_k")
            use_rerank = st.toggle("Enable reranking", value=False, help="First run downloads ~66MB model")

            model_label = st.selectbox("Model", list(GROQ_MODELS.keys()), key="lab_model")
            lab_model = GROQ_MODELS[model_label]

        question = st.text_input("Enter a question to analyse", placeholder="What are the key findings?")

        if st.button("🔬 Run full pipeline analysis", type="primary") and question:
            from src.retrieval.vector_search import retrieve
            from src.retrieval.hybrid_search import hybrid_retrieve
            from src.retrieval.reranker import rerank
            from src.retrieval.query_rewriter import rewrite_query
            from src.retrieval.context_compressor import compress_chunks
            from src.generation.groq_client import generate_answer
            from src.generation.citation_verifier import verify_citations
            import time

            st.divider()

            # 1 Query rewriting
            st.subheader("1️⃣ Query Rewriting")
            with st.spinner("Rewriting query…"):
                t0 = time.time()
                rewritten = rewrite_query(question, model=lab_model)
                rewrite_ms = int((time.time() - t0) * 1000)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original**"); st.info(question)
            with col2:
                st.markdown("**Rewritten**"); st.success(rewritten if rewritten != question else "*(no change)*")
            st.caption(f"Latency: {rewrite_ms}ms")
            st.divider()

            # 2 Vector retrieval
            st.subheader("2️⃣ Vector Retrieval")
            with st.spinner("Vector search…"):
                t0 = time.time()
                vector_chunks = retrieve(kb_id, rewritten, top_k=top_k)
                vector_ms = int((time.time() - t0) * 1000)
            st.caption(f"{len(vector_chunks)} chunks in {vector_ms}ms")
            with st.expander("Vector results"):
                for i, c in enumerate(vector_chunks, 1):
                    pg = f", p{c['page_number']}" if c.get("page_number") else ""
                    st.markdown(f"**#{i}** `{c['filename']}`{pg} — `{c['score']:.4f}`")
                    st.caption(c["content"][:200] + "…")
            st.divider()

            # 3 Hybrid retrieval
            st.subheader("3️⃣ Hybrid Retrieval (Vector + BM25 + RRF)")
            with st.spinner("Hybrid search…"):
                t0 = time.time()
                hybrid_chunks = hybrid_retrieve(kb_id, rewritten, top_k=top_k)
                hybrid_ms = int((time.time() - t0) * 1000)
            st.caption(f"{len(hybrid_chunks)} chunks in {hybrid_ms}ms")
            with st.expander("Hybrid results"):
                for i, c in enumerate(hybrid_chunks, 1):
                    pg = f", p{c['page_number']}" if c.get("page_number") else ""
                    st.markdown(f"**#{i}** `{c['filename']}`{pg} — RRF `{c['score']:.4f}`")
                    st.caption(c["content"][:200] + "…")
            st.divider()

            # 4 Reranking
            st.subheader("4️⃣ Cross-Encoder Reranking")
            if use_rerank:
                with st.spinner("Reranking…"):
                    t0 = time.time()
                    reranked_chunks = rerank(rewritten, hybrid_chunks, top_k=top_k)
                    rerank_ms = int((time.time() - t0) * 1000)
                st.caption(f"Reranked in {rerank_ms}ms")
                with st.expander("Reranked results"):
                    for i, c in enumerate(reranked_chunks, 1):
                        pg = f", p{c['page_number']}" if c.get("page_number") else ""
                        st.markdown(f"**#{i}** `{c['filename']}`{pg} — `{c.get('rerank_score', c['score']):.4f}`")
                        st.caption(c["content"][:200] + "…")
            else:
                reranked_chunks = hybrid_chunks
                rerank_ms = 0
                st.caption("Disabled — toggle 'Enable reranking' in the sidebar.")
            st.divider()

            # 5 Context compression
            st.subheader("5️⃣ Context Compression")
            with st.spinner("Compressing…"):
                t0 = time.time()
                compressed_chunks = compress_chunks(rewritten, reranked_chunks)
                compress_ms = int((time.time() - t0) * 1000)
            n_compressed = sum(1 for c in compressed_chunks if c.get("compressed"))
            st.caption(f"Compressed {n_compressed}/{len(compressed_chunks)} chunks in {compress_ms}ms")
            with st.expander("Compressed context"):
                for i, c in enumerate(compressed_chunks, 1):
                    label = f"compressed: {c['sentences_kept']}/{c['sentences_total']} sentences" if c.get("compressed") else "not compressed"
                    st.markdown(f"**#{i}** *({label})*")
                    st.caption(c["content"][:300] + "…")
            st.divider()

            # 6 Answer generation
            st.subheader("6️⃣ Answer Generation")
            with st.spinner("Generating…"):
                t0 = time.time()
                result = generate_answer(question, compressed_chunks, model=lab_model)
                gen_ms = int((time.time() - t0) * 1000)
            st.markdown(result.answer)
            st.caption(f"{gen_ms}ms · {result.prompt_tokens} prompt / {result.completion_tokens} completion tokens")
            st.divider()

            # 7 Citation verification
            st.subheader("7️⃣ Citation Verification")
            with st.spinner("Verifying…"):
                t0 = time.time()
                vresult = verify_citations(result.answer, compressed_chunks)
                verify_ms = int((time.time() - t0) * 1000)
            st.caption(f"{verify_ms}ms · Support rate: {vresult.support_rate*100:.0f}%")
            for sv in vresult.sentences:
                icon = "✅" if sv.supported else "⚠️"
                src = f" ← {sv.best_source}" if sv.best_source else ""
                st.markdown(f"{icon} *{sv.text[:120]}{'…' if len(sv.text) > 120 else ''}*{src} `{sv.confidence}`")
            st.divider()

            # Summary
            st.subheader("📊 Pipeline Summary")
            total_ms = rewrite_ms + vector_ms + hybrid_ms + rerank_ms + compress_ms + gen_ms + verify_ms
            metrics = {
                "Query rewrite": f"{rewrite_ms}ms",
                "Vector search": f"{vector_ms}ms",
                "Hybrid search": f"{hybrid_ms}ms",
                "Reranking": f"{rerank_ms}ms",
                "Compression": f"{compress_ms}ms",
                "Generation": f"{gen_ms}ms",
                "Verification": f"{verify_ms}ms",
                "Total latency": f"{total_ms}ms",
            }
            cols = st.columns(4)
            for idx, (label, val) in enumerate(metrics.items()):
                with cols[idx % 4]:
                    st.metric(label, val)
