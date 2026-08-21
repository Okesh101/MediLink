# app/services/ai/summary.py

from app import db
from app.models.AIConversation import AIConversation
from app.services.ai.client import client


def generate_conversation_summary(conversation_id: str) -> str:
    conversation = db.session.execute(
        db.select(AIConversation).filter_by(id=conversation_id)
    ).scalar_one_or_none()

    if not conversation or not conversation.messages:
        return "No conversation history available."

    transcript = "\n".join(
        [f"{m.role.upper()}: {m.content}" for m in conversation.messages])

    prompt = f"""
    You are a medical scribe. Summarize the following patient interaction into a concise doctor hand-off report.

    Format requirements:
    - **Chief Complaints**: Key issues reported by patient
    - **Symptom Duration/Severity**: Timeline of symptoms
    - **Relevant Risk Factors**: Allergies or medical history mentioned
    - **Recommended Action**: Suggested medical specialty or urgency level

    TRANSCRIPT:
    {transcript}
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    summary_text = response.choices[0].message.content
    conversation.symptom_summary = summary_text
    conversation.status = "completed"
    db.session.commit()

    return summary_text
