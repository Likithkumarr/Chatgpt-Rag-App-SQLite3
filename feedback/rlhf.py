import uuid
from db import get_last_chat_message, update_chat_message_feedback, save_feedback

# from config import CSV_FEEDBACK_FILE
# import os,csv
# def save_to_csv(username, prompt, response):
#     file_exists = os.path.isfile(CSV_FEEDBACK_FILE)
#     with open(CSV_FEEDBACK_FILE, mode='a', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         if not file_exists:
#             writer.writerow(["Timestamp", "Username", "Prompt", "Response"])
#         writer.writerow([datetime.now(), username, prompt, response])


def save_feedback_entry(session_id, messages, feedback):
    message = get_last_chat_message(session_id, role="assistant")
    if not message:
        return

    update_chat_message_feedback(message["id"], feedback)

    prompt_text = ""
    if len(messages) >= 2 and messages[-2].get("role") == "user":
        prompt_text = messages[-2].get("content", "")

    save_feedback(
        str(uuid.uuid4()),
        message["username"],
        session_id,
        prompt_text,
        message["content"],
        feedback,
    )


def handle_feedback(st):
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        c1, c2 = st.columns([1, 8])

        with c1:
            if st.button("👍"):
                save_feedback_entry(
                    st.session_state.current_session_id,
                    st.session_state.messages,
                    "good",
                )
                st.success("Saved as good feedback")

        with c2:
            if st.button("👎"):
                save_feedback_entry(
                    st.session_state.current_session_id,
                    st.session_state.messages,
                    "bad",
                )
                st.session_state.messages.pop()
                st.session_state.retry_trigger = True
                st.rerun()