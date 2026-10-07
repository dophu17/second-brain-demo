from fastapi import APIRouter, Request, HTTPException, Header
from typing import Dict, Any
from app.services.hermes_agent import hermes_agent_service

router = APIRouter(prefix="/api/webhook", tags=["LINE Webhook"])

@router.post("")
async def line_webhook(request: Request, x_line_signature: str = Header(default="mock_sig")):
    """LINE Bot Webhook Handler tiếp nhận Voice STT & Text Input."""
    try:
        body = await request.json()
        events = body.get("events", [])
        
        responses = []
        for event in events:
            if event.get("type") == "message":
                msg_type = event["message"].get("type")
                if msg_type == "text":
                    user_text = event["message"].get("text", "")
                    ai_res = hermes_agent_service.process_chat(user_text)
                    responses.append({
                        "event_id": event.get("webhookEventId"),
                        "reply_text": ai_res.reply,
                        "tools_executed": ai_res.tool_calls_executed
                    })
                elif msg_type == "audio":
                    # Mock Voice STT processing
                    voice_text = "Họp với [[Kenichi]] về tiến độ [[Du_an_2]]"
                    ai_res = hermes_agent_service.process_chat(voice_text)
                    responses.append({
                        "event_id": event.get("webhookEventId"),
                        "voice_stt": voice_text,
                        "reply_text": ai_res.reply,
                        "tools_executed": ai_res.tool_calls_executed
                    })
                    
        return {"status": "success", "processed_events": responses}
    except Exception as e:
        return {"status": "ok", "message": f"Webhook mock processed: {e}"}
