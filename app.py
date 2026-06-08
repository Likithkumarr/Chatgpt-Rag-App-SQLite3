import streamlit as st
import re
from utils.session import init_session
from auth.login import login
from auth.register import register
from chat.chat_engine import get_llms
from chat.chat_ui import render_sidebar
from chat.history import get_history
from feedback.rlhf import handle_feedback
import json
from db import save_session, save_chat_message

init_session()

# AUTH
st.set_page_config(page_title="ChatBot with RAG and RLHF", page_icon="🤖", layout="wide")
if not st.session_state.logged_in:
    st.title("🔐 Multi-User Secure Chat")
    st.info("Don't have an account? Go to **Register**. Already have an account? Go to **Login**.")
    tab1, tab2 = st.tabs(["Login", "Register"])
 
    with tab1:
        login()
 
    with tab2:
        register()
 
else:
    current_name=st.session_state.display_name or st.session_state.username
    st.title(f"🤖 Welcome {current_name}")
      # ---------- SIDEBAR  ----------
    # uploaded_files = 
    render_sidebar()
    # LLM
    llm1,llm2=get_llms()
    # Messages
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])
 
    prompt = st.chat_input("Message...")
    
    if prompt or st.session_state.retry_trigger:
        if st.session_state.retry_trigger:
            user_query = st.session_state.messages[-1]["content"] 
            bad_answer = st.session_state.messages[-1]["content"]
            # if len(st.session_state.messages) >= 2:  
            #     user_query = st.session_state.messages[-2]["content"] 
            #     bad_answer = st.session_state.messages[-1]["content"]
            # else:
            #     st.error("No previous assistant response to retry.")
            #     st.session_state.retry_trigger = False
            #     st.stop()  # Stop execution if there's no response to retry
            st.warning("🔄 Generating a fresh, different response...")
            active_llm = llm2  
            instruction = f"""
            The user disliked your previous response. 
            PREVIOUS RESPONSE: {bad_answer}
            
            Provide a DIFFERENT perspective or more detail. 
            Do NOT repeat the same explanation or phrasing.
            """
        else:
            user_query = prompt
            active_llm = llm1
            instruction = "Be concise and helpful."
            name_match = re.search(r"(?:my name is|i am) (\w+)", user_query.lower())
            if name_match: st.session_state.display_name = name_match.group(1).capitalize()
            
            st.session_state.messages.append({"role": "user", "content": user_query})
            save_chat_message(
                st.session_state.current_session_id,
                st.session_state.username,
                "user",
                user_query,
            )
            with st.chat_message("user"): st.markdown(user_query)

        with st.chat_message("assistant"):
            all_past_interactions = get_history(st.session_state.username)
            doc_context = ""
            final_input=""
            used_doc_final = False # Reset this for every new message
            response = ""
            
            # Check if user is asking "What did I upload?"
            if "UPLOAD" in user_query.upper() and ("WHAT" in user_query.upper() or "NAME" in user_query.upper()):
                filenames = st.session_state.get('uploaded_filenames', [])
                if filenames:
                    response = f"You have uploaded the following documents: {', '.join(filenames)}"
                    st.info("📄 Using document metadata")
                    used_doc_final = True
                else:
                    response = "You haven't uploaded any documents in this session yet."
                    st.info("🤖 General AI response")
                    used_doc_final = True
            if st.session_state.retriever:
                docs = st.session_state.retriever.invoke(user_query)
                doc_context = ""
                use_doc = False
                # Replace your LLM call sections with this pattern:

                
                if docs and len(docs) > 0:
                    doc_context = "\n".join([d.page_content for d in docs])
                    # Simple check: is there a keyword match or enough content to try?
                    keyword_match = any(user_query.lower() in d.page_content.lower() for d in docs)
                    
                    if keyword_match or len(doc_context) > 100:
                        use_doc = True

                # --- STEP 1: TRY DOCUMENT RETRIEVAL ---
                if use_doc:
                    doc_prompt = f"""
                        You are strict Document QA System.
                        Context: {doc_context}
                        Question: {user_query}
                        Rules: Answer ONLY from context. If not found, say 'I don't know'.
                    """
                    try:
                        # Wrap the sensitive call in a try block
                        response_content = active_llm.invoke(doc_prompt).content
                        
                        if "I DON'T KNOW" not in response_content.upper() and "NOT CONTAIN" not in response_content.upper():
                            used_doc_final = True
                            response = response_content
                            st.info("📄 Using document")
                            
                    except Exception as e:
                        # Check if the error is specifically the content filter
                        if "content_filter" in str(e):
                            st.warning("⚠️ The retrieved document segments triggered Azure's safety filter. Falling back to general knowledge.")
                            used_doc_final = False  # Force fallback to Step 2
                        else:
                            # Re-raise if it's a different error (like API connection)
                            st.error(f"LLM Error: {e}")
                            st.stop()

                    # response_content = active_llm.invoke(doc_prompt).content
                    
                    # # Check if the LLM actually found an answer in the docs
                    # if "I DON'T KNOW" not in response_content.upper() and "NOT CONTAIN" not in response_content.upper():
                    #     used_doc_final = True
                    #     response = response_content
                    #     # DISPLAY MESSAGE: Using document
                    #     st.info("📄 Using document")

                # --- STEP 2: FALLBACK TO GENERAL AI ---
                if not used_doc_final:
                    ai_prompt = f"""{instruction}
                        You are a helpful assistant.
                        User name: {current_name}
                        Memory: {all_past_interactions}
                        Question: {user_query}
                    """
                    response = active_llm.invoke(ai_prompt).content
                    # DISPLAY MESSAGE: General AI response
                    st.info("🤖 General AI response")

            # Final output of the generated text
            st.write(response)
            if not final_input:
                final_input = f"""{instruction}
                    You are a helpful assistant.
                    User name: {current_name}
                    
                    YOUR MEMORY OF THIS USER (ALL PREVIOUS SESSIONS):
                    {all_past_interactions}
                    
                    Question: {user_query}
            """
            # response = active_llm.invoke(final_input).content
            # st.markdown(response)
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    response = active_llm.invoke(final_input).content
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_message(
            st.session_state.current_session_id,
            st.session_state.username,
            "assistant",
            response,
        )
        session_title = None
        if st.session_state.messages:
            first_user = next((m for m in st.session_state.messages if m["role"] == "user"), None)
            if first_user:
                session_title = first_user["content"][:40]

        save_session(
            st.session_state.current_session_id,
            st.session_state.username,
            json.dumps(st.session_state.messages),
            title=session_title,
        )
        st.session_state.retry_trigger = False
        st.rerun()

    # ---------- RLHF ----------
    handle_feedback(st)

