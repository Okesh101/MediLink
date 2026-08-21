# app/services/ai/meddy.py

import json
import logging
# from groq import Groq
from app import db
from app.models.Patient import Patient
from app.models.AIConversation import AIConversation
from app.models.ChatMessage import ChatMessage
from app.services.ai.client import client
from app.services.ai.prompts import MEDDY_CHAT_SYSTEM_PROMPT
from app.services.ai.tools import GROQ_TOOLS, handle_tool_call

logger = logging.getLogger(__name__)

# Primary model for quality medical reasoning (largest available)
TEXT_MODEL = "openai/gpt-oss-120b"
# Fallback model for higher volume when rate limits are hit
FALLBACK_MODEL = "openai/gpt-oss-20b"


def handle_patient_chat_stream(patient_public_id: str, new_user_message: str):
    """
    Streams conversational responses back to the frontend using Server-Sent Events (SSE).
    Automatically fetches chat context and handles Groq tool calls against the database.
    """
    # 1. Fetch patient record
    patient = db.session.execute(
        db.select(Patient).filter_by(public_id=patient_public_id)
    ).scalar_one_or_none()

    if not patient:
        yield f"event: error\ndata: {json.dumps({'message': 'Patient not found.'})}\n\n"
        return

    # 2. Get or create active conversation
    conversation = db.session.execute(
        db.select(AIConversation)
        .filter_by(patient_public_id=patient_public_id, status='active')
        .order_by(AIConversation.created_at.desc())
    ).scalar_one_or_none()

    if not conversation:
        conversation = AIConversation(
            patient_public_id=patient_public_id, status='active')
        db.session.add(conversation)
        db.session.commit()
        db.session.refresh(conversation)

    # 3. Load past chat history (last 15 messages)
    history_records = db.session.execute(
        db.select(ChatMessage)
        .filter_by(conversation_id=conversation.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(15)
    ).scalars().all()

    # 3. Assemble Groq payload messages
    messages = [{"role": "system", "content": MEDDY_CHAT_SYSTEM_PROMPT}]
    for msg in history_records:
        messages.append({"role": msg.role, "content": msg.content})

    # Append current user message
    messages.append({"role": "user", "content": new_user_message})

    # Persist user message to DB
    _persist_chat_message(
        conversation.id, patient_public_id, "user", new_user_message)

    yield f"event: status\ndata: {json.dumps({'message': 'Processing request...'})}\n\n"

    try:
        # 4. First Groq request (allows AI to decide if DB tools are needed)
        response = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=messages,
            tools=GROQ_TOOLS,
            tool_choice="auto",
            temperature=0.6,
            max_completion_tokens=1024
        )

        response_message = response.choices[0].message

        # 5. Handle DB Tool Execution if Groq requests data
        if response_message.tool_calls:
            # Append assistant's intent to call tool
            if response_message.tool_calls:
                # Convert Pydantic object to dict or append structured role
                messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in response_message.tool_calls
                    ]
                })

                for tool_call in response_message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)

                    yield f"event: status\ndata: {json.dumps({'message': f'Searching medical database ({fn_name})...'})}\n\n"

                    tool_output = handle_tool_call(fn_name, fn_args)

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fn_name,
                        "content": json.dumps(tool_output)
                    })

            # Stream final response built with tool output
            stream_response = client.chat.completions.create(
                model=TEXT_MODEL,
                messages=messages,
                stream=True,
                temperature=0.6,
                max_completion_tokens=1024
            )
        else:
            # Stream direct text response
            stream_response = client.chat.completions.create(
                model=TEXT_MODEL,
                messages=messages,
                stream=True,
                temperature=0.6,
                max_completion_tokens=1024
            )

        # 6. Stream tokens chunk-by-chunk to client
        full_reply = ""
        for chunk in stream_response:
            delta = chunk.choices[0].delta.content
            if delta:
                full_reply += delta
                yield f"data: {json.dumps({'content': delta})}\n\n"

        # Save AI reply to ChatMessage history
        _persist_chat_message(
            conversation.id, patient_public_id, "assistant", full_reply)

    except Exception as e:
        logger.error(f"Chat execution failed: {e}", exc_info=True)
        yield f"event: error\ndata: {json.dumps({'message': 'An error occurred processing your request.'})}\n\n"

    yield "event: end\ndata: [DONE]\n\n"


def _persist_chat_message(conversation_id: str, patient_public_id: str, role: str, content: str):
    msg = ChatMessage(
        conversation_id=conversation_id,
        patient_public_id=patient_public_id,
        role=role,
        content=content
    )
    db.session.add(msg)
    db.session.commit()
