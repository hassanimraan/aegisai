import streamlit as st

from rag.retriever import search_policies


st.set_page_config(
    page_title="RAG Test - AegisAI",
    page_icon="🔎",
    layout="wide"
)


st.title("🔎 AegisAI Policy RAG Test")

st.write(
    "Test retrieval of relevant PEIS policy sections "
    "from the pre-generated policy embeddings."
)

st.divider()


query = st.text_area(
    "Enter a policy question",
    value=(
        "A procurement request is worth PKR 4,800,000. "
        "How many vendor quotations are required and "
        "which approval authority is required?"
    ),
    height=120
)


top_k = st.slider(
    "Number of policy sections",
    min_value=1,
    max_value=10,
    value=5
)


if st.button(
    "🔎 Search Policies",
    type="primary"
):

    if not query.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        try:

            with st.spinner(
                "Searching policy knowledge base..."
            ):

                results = search_policies(
                    query,
                    top_k=top_k
                )

            st.success(
                f"Retrieved {len(results)} policy sections."
            )

            for index, result in enumerate(
                results,
                start=1
            ):

                st.markdown(
                    f"### {index}. "
                    f"{result['policy_id']} — "
                    f"{result['policy_name']}"
                )

                st.write(
                    f"**Section:** "
                    f"{result['section_id']} — "
                    f"{result['section_title']}"
                )

                st.write(
                    f"**Similarity:** "
                    f"{result['similarity']:.4f}"
                )

                st.info(
                    result["content"]
                )

                st.divider()

        except Exception as e:

            st.error(
                f"RAG test failed: {str(e)}"
            )
