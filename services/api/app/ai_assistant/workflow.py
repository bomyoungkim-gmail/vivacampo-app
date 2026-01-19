from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import structlog
from app.ai_assistant.providers import create_provider, Message
from app.ai_assistant.tools import TOOLS, SENSITIVE_TOOLS, execute_tool
from app.ai_assistant.prompts import get_system_prompt
from app.config import settings

logger = structlog.get_logger()


class AIAssistantWorkflow:
    """
    AI Assistant workflow engine with Human-in-the-Loop support.
    
    Simplified workflow (not using LangGraph for MVP):
    1. User sends message
    2. AI processes with tools
    3. If sensitive tool called -> create approval request
    4. If approved -> execute tool
    5. Continue conversation
    """
    
    def __init__(self, thread_id: str, tenant_id: str, db: Session):
        self.thread_id = thread_id
        self.tenant_id = tenant_id
        self.db = db
        
        # Load thread info
        thread = self._load_thread()
        self.provider_name = thread.get('provider', settings.ai_assistant_provider)
        self.model = thread.get('model', settings.ai_assistant_model)
        
        # Create LLM provider
        self.provider = create_provider(
            self.provider_name,
            settings.ai_assistant_api_key,
            self.model
        )
        
        # Load conversation history
        self.messages = self._load_messages()
    
    def _load_thread(self) -> Dict:
        """Load thread from database"""
        sql = text("""
            SELECT provider, model, status
            FROM ai_assistant_threads
            WHERE id = :thread_id AND tenant_id = :tenant_id
        """)
        
        result = self.db.execute(sql, {
            "thread_id": self.thread_id,
            "tenant_id": self.tenant_id
        }).fetchone()
        
        if not result:
            raise ValueError("Thread not found")
        
        return {
            "provider": result.provider,
            "model": result.model,
            "status": result.status
        }
    
    def _load_messages(self) -> List[Message]:
        """Load conversation history from checkpoints"""
        sql = text("""
            SELECT state_json
            FROM ai_assistant_checkpoints
            WHERE thread_id = :thread_id AND tenant_id = :tenant_id
            ORDER BY step ASC
        """)
        
        result = self.db.execute(sql, {
            "thread_id": self.thread_id,
            "tenant_id": self.tenant_id
        }).fetchall()
        
        messages = []
        for row in result:
            state = json.loads(row.state_json)
            for msg in state.get('messages', []):
                messages.append(Message(msg['role'], msg['content']))
        
        return messages
    
    def _save_checkpoint(self, step: int, state: Dict):
        """Save checkpoint to database"""
        sql = text("""
            INSERT INTO ai_assistant_checkpoints
            (tenant_id, thread_id, step, state_json)
            VALUES (:tenant_id, :thread_id, :step, :state)
            ON CONFLICT (tenant_id, thread_id, step) DO UPDATE
            SET state_json = :state
        """)
        
        self.db.execute(sql, {
            "tenant_id": self.tenant_id,
            "thread_id": self.thread_id,
            "step": step,
            "state": json.dumps(state)
        })
        self.db.commit()
    
    def process_message(self, user_message: str, language: str = "pt-BR") -> Dict[str, Any]:
        """
        Process user message and generate response.
        
        Returns:
            Dict with response or approval_required status
        """
        logger.info("processing_message", thread_id=self.thread_id, message_length=len(user_message))
        
        # Add system prompt if first message
        if not self.messages:
            system_prompt = get_system_prompt(language)
            self.messages.append(Message("system", system_prompt))
        
        # Add user message
        self.messages.append(Message("user", user_message))
        
        # Generate response with tools
        response = self.provider.generate_with_tools(
            self.messages,
            TOOLS,
            temperature=0.7
        )
        
        # Check if tool call
        if response.get("type") == "tool_call":
            tool_calls = response.get("tool_calls", [])
            
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("arguments", {})
                
                # Check if sensitive tool
                if tool_name in SENSITIVE_TOOLS:
                    # Create approval request
                    approval_id = self._create_approval_request(
                        tool_name,
                        tool_args
                    )
                    
                    # Update thread status
                    self._update_thread_status("WAITING_HUMAN")
                    
                    return {
                        "type": "approval_required",
                        "approval_id": approval_id,
                        "tool_name": tool_name,
                        "tool_arguments": tool_args,
                        "message": f"A ação '{tool_name}' requer aprovação humana."
                    }
                
                else:
                    # Execute tool directly
                    tool_result = execute_tool(tool_name, tool_args, self.db)
                    
                    # Add tool result to messages
                    self.messages.append(Message(
                        "assistant",
                        f"Tool {tool_name} executed: {json.dumps(tool_result)}"
                    ))
                    
                    # Generate final response
                    final_response = self.provider.generate(
                        self.messages,
                        temperature=0.7
                    )
                    
                    self.messages.append(Message("assistant", final_response))
                    
                    # Save checkpoint
                    self._save_checkpoint(len(self.messages), {
                        "messages": [{"role": m.role, "content": m.content} for m in self.messages]
                    })
                    
                    return {
                        "type": "text",
                        "content": final_response
                    }
        
        else:
            # Text response
            content = response.get("content", "")
            self.messages.append(Message("assistant", content))
            
            # Save checkpoint
            self._save_checkpoint(len(self.messages), {
                "messages": [{"role": m.role, "content": m.content} for m in self.messages]
            })
            
            return {
                "type": "text",
                "content": content
            }
    
    def _create_approval_request(self, tool_name: str, tool_args: Dict) -> str:
        """Create approval request in database"""
        sql = text("""
            INSERT INTO ai_assistant_approvals
            (tenant_id, thread_id, requested_by_system, tool_name, tool_payload, decision)
            VALUES (:tenant_id, :thread_id, true, :tool_name, :tool_payload, 'PENDING')
            RETURNING id
        """)
        
        result = self.db.execute(sql, {
            "tenant_id": self.tenant_id,
            "thread_id": self.thread_id,
            "tool_name": tool_name,
            "tool_payload": json.dumps(tool_args)
        })
        self.db.commit()
        
        approval_id = result.fetchone()[0]
        logger.info("approval_request_created", approval_id=approval_id, tool_name=tool_name)
        
        return str(approval_id)
    
    def _update_thread_status(self, status: str):
        """Update thread status"""
        sql = text("""
            UPDATE ai_assistant_threads
            SET status = :status, updated_at = now()
            WHERE id = :thread_id AND tenant_id = :tenant_id
        """)
        
        self.db.execute(sql, {
            "status": status,
            "thread_id": self.thread_id,
            "tenant_id": self.tenant_id
        })
        self.db.commit()
    
    def process_approval(self, approval_id: str, decision: str, decided_by_membership_id: str, note: Optional[str] = None):
        """
        Process approval decision.
        
        Args:
            approval_id: ID of the approval request
            decision: "APPROVED" or "REJECTED"
            decided_by_membership_id: ID of the membership who decided
            note: Optional note
        """
        logger.info("processing_approval", approval_id=approval_id, decision=decision)
        
        # Update approval
        sql = text("""
            UPDATE ai_assistant_approvals
            SET decision = :decision,
                decided_by_membership_id = :decided_by,
                decision_note = :note,
                decided_at = now()
            WHERE id = :approval_id AND tenant_id = :tenant_id
            RETURNING tool_name, tool_payload
        """)
        
        result = self.db.execute(sql, {
            "decision": decision,
            "decided_by": decided_by_membership_id,
            "note": note,
            "approval_id": approval_id,
            "tenant_id": self.tenant_id
        }).fetchone()
        
        if not result:
            raise ValueError("Approval not found")
        
        tool_name = result.tool_name
        tool_payload = json.loads(result.tool_payload)
        
        if decision == "APPROVED":
            # Execute tool
            tool_result = execute_tool(tool_name, tool_payload, self.db)
            
            # Add to messages
            self.messages.append(Message(
                "assistant",
                f"Tool {tool_name} was approved and executed: {json.dumps(tool_result)}"
            ))
            
            # Generate final response
            final_response = self.provider.generate(
                self.messages,
                temperature=0.7
            )
            
            self.messages.append(Message("assistant", final_response))
            
            # Save checkpoint
            self._save_checkpoint(len(self.messages), {
                "messages": [{"role": m.role, "content": m.content} for m in self.messages]
            })
            
            # Update thread status
            self._update_thread_status("OPEN")
            
            return {
                "type": "text",
                "content": final_response
            }
        
        else:
            # Rejected
            self.messages.append(Message(
                "assistant",
                f"A ação '{tool_name}' foi rejeitada. Como posso ajudar de outra forma?"
            ))
            
            # Save checkpoint
            self._save_checkpoint(len(self.messages), {
                "messages": [{"role": m.role, "content": m.content} for m in self.messages]
            })
            
            # Update thread status
            self._update_thread_status("OPEN")
            
            return {
                "type": "text",
                "content": "Ação rejeitada. Como posso ajudar de outra forma?"
            }
        
        self.db.commit()
