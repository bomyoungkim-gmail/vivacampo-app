from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()

# Define tools available to the AI assistant
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "explain_signal",
            "description": "Explain why an opportunity signal was generated and what it means for the farmer",
            "parameters": {
                "type": "object",
                "properties": {
                    "signal_id": {
                        "type": "string",
                        "description": "The ID of the signal to explain"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["pt-BR", "en"],
                        "description": "Language for the explanation"
                    }
                },
                "required": ["signal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_actions",
            "description": "Suggest specific actions the farmer should take based on a signal",
            "parameters": {
                "type": "object",
                "properties": {
                    "signal_id": {
                        "type": "string",
                        "description": "The ID of the signal"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context from the farmer"
                    }
                },
                "required": ["signal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_notification",
            "description": "Create a notification to send to the farmer (email/SMS/push). REQUIRES HUMAN APPROVAL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Email or phone number"
                    },
                    "channel": {
                        "type": "string",
                        "enum": ["email", "sms", "push"],
                        "description": "Notification channel"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Notification subject/title"
                    },
                    "message": {
                        "type": "string",
                        "description": "Notification message body"
                    }
                },
                "required": ["recipient", "channel", "subject", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_webhook",
            "description": "Trigger a webhook to integrate with external systems. REQUIRES HUMAN APPROVAL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "webhook_id": {
                        "type": "string",
                        "description": "ID of the configured webhook"
                    },
                    "payload": {
                        "type": "object",
                        "description": "Data to send to the webhook"
                    }
                },
                "required": ["webhook_id", "payload"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_work_order",
            "description": "Create a work order for field operations. REQUIRES HUMAN APPROVAL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "aoi_id": {
                        "type": "string",
                        "description": "Area of interest ID"
                    },
                    "task_type": {
                        "type": "string",
                        "description": "Type of task (inspection, maintenance, etc.)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the work order"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority level"
                    }
                },
                "required": ["aoi_id", "task_type", "description"]
            }
        }
    }
]

# Tools that require human approval
SENSITIVE_TOOLS = [
    "create_notification",
    "trigger_webhook",
    "create_work_order"
]


def execute_tool(tool_name: str, arguments: Dict[str, Any], db) -> Dict[str, Any]:
    """
    Execute a tool function.
    
    For sensitive tools, this will create an approval request instead of executing.
    """
    logger.info("executing_tool", tool_name=tool_name, arguments=arguments)
    
    if tool_name == "explain_signal":
        return explain_signal(arguments, db)
    
    elif tool_name == "suggest_actions":
        return suggest_actions(arguments, db)
    
    elif tool_name in SENSITIVE_TOOLS:
        # These require approval - should not be executed directly
        logger.warning("sensitive_tool_called_directly", tool_name=tool_name)
        return {
            "status": "pending_approval",
            "message": "This action requires human approval"
        }
    
    else:
        logger.error("unknown_tool", tool_name=tool_name)
        return {"error": f"Unknown tool: {tool_name}"}


def explain_signal(arguments: Dict[str, Any], db) -> Dict[str, Any]:
    """
    Explain a signal to the user.
    """
    from sqlalchemy import text
    
    signal_id = arguments.get("signal_id")
    language = arguments.get("language", "pt-BR")
    
    # Query signal
    sql = text("""
        SELECT signal_type, severity, confidence, score, evidence_json, 
               recommended_actions, aoi_id
        FROM opportunity_signals
        WHERE id = :signal_id
    """)
    
    result = db.execute(sql, {"signal_id": signal_id}).fetchone()
    
    if not result:
        return {"error": "Signal not found"}
    
    # Build explanation context
    context = {
        "signal_type": result.signal_type,
        "severity": result.severity,
        "confidence": result.confidence,
        "score": result.score,
        "evidence": result.evidence_json,
        "recommended_actions": result.recommended_actions
    }
    
    return {
        "status": "success",
        "context": context,
        "language": language
    }


def suggest_actions(arguments: Dict[str, Any], db) -> Dict[str, Any]:
    """
    Suggest actions based on signal and additional context.
    """
    from sqlalchemy import text
    
    signal_id = arguments.get("signal_id")
    user_context = arguments.get("context", "")
    
    # Query signal
    sql = text("""
        SELECT signal_type, recommended_actions, features_json
        FROM opportunity_signals
        WHERE id = :signal_id
    """)
    
    result = db.execute(sql, {"signal_id": signal_id}).fetchone()
    
    if not result:
        return {"error": "Signal not found"}
    
    return {
        "status": "success",
        "signal_type": result.signal_type,
        "base_actions": result.recommended_actions,
        "features": result.features_json,
        "user_context": user_context
    }
