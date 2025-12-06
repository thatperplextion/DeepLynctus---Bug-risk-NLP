"""
AI Chatbot Service - Code review assistant powered by LLM.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class CodeReviewChatbot:
    """AI-powered code review assistant."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.conversation_history: List[Dict] = []
        self.context: Dict[str, Any] = {}
        
    async def load_context(self):
        """Load project context for the chatbot."""
        from services.db import db
        
        # Load project info
        project = await db.projects.find_one({"_id": self.project_id})
        if project:
            self.context["project"] = {
                "name": project.get("name", "Unknown"),
                "repo_url": project.get("repo_url", ""),
                "languages": project.get("languages", [])
            }
        
        # Load recent metrics
        metrics = await db.metrics.find({"project_id": self.project_id}).limit(10).to_list(length=10)
        if metrics:
            self.context["top_files"] = [
                {"path": m["path"], "risk": m.get("risk_score", 0)}
                for m in sorted(metrics, key=lambda x: x.get("risk_score", 0), reverse=True)[:5]
            ]
        
        # Load recent smells
        smells = await db.smells.find({"project_id": self.project_id}).limit(20).to_list(length=20)
        if smells:
            self.context["recent_issues"] = [
                {"type": s["type"], "path": s["path"], "message": s.get("message", "")}
                for s in smells[:10]
            ]
        
        # Load summary stats
        summary = await db.scan_history.find_one(
            {"project_id": self.project_id},
            sort=[("timestamp", -1)]
        )
        if summary:
            self.context["summary"] = summary.get("metrics", {})
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with project context."""
        prompt = """You are Deep Lynctus AI, an expert code review assistant. You help developers understand their codebase, identify issues, and suggest improvements.

You have access to the following project context:
"""
        
        if self.context.get("project"):
            prompt += f"\n**Project:** {self.context['project'].get('name', 'Unknown')}"
            if self.context['project'].get('repo_url'):
                prompt += f"\n**Repository:** {self.context['project']['repo_url']}"
        
        if self.context.get("summary"):
            s = self.context["summary"]
            prompt += f"""

**Current Code Quality Metrics:**
- Quality Score: {s.get('quality_score', 'N/A')}%
- Total Files: {s.get('total_files', 'N/A')}
- Total Issues: {s.get('total_smells', 'N/A')}
- Critical Issues: {s.get('critical_issues', 'N/A')}
- High Priority Issues: {s.get('high_issues', 'N/A')}
"""
        
        if self.context.get("top_files"):
            prompt += "\n**Highest Risk Files:**\n"
            for f in self.context["top_files"]:
                prompt += f"- {f['path']} (Risk: {f['risk']})\n"
        
        if self.context.get("recent_issues"):
            prompt += "\n**Recent Issues Found:**\n"
            for issue in self.context["recent_issues"][:5]:
                prompt += f"- [{issue['type']}] {issue['path']}: {issue['message'][:100]}\n"
        
        prompt += """

**Your Capabilities:**
1. Explain code quality issues and why they matter
2. Suggest specific fixes and refactoring strategies
3. Prioritize which issues to fix first
4. Answer questions about the codebase structure
5. Provide best practices and coding standards advice
6. Help understand complex code patterns
7. Suggest testing strategies

Be concise, actionable, and friendly. Use code examples when helpful.
"""
        return prompt
    
    async def chat(self, message: str, file_context: str = None) -> Dict[str, Any]:
        """Process a chat message and return a response."""
        from services.llm_service import query_llm
        
        # Load context if not already loaded
        if not self.context:
            await self.load_context()
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        # Add conversation history (last 10 messages)
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        
        # Add file context if provided
        if file_context:
            messages.append({
                "role": "user",
                "content": f"[File Context]\n```\n{file_context[:2000]}\n```\n\n{message}"
            })
        else:
            messages.append({"role": "user", "content": message})
        
        # Query LLM
        try:
            response = await query_llm(
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            assistant_message = response.get("content", "I'm sorry, I couldn't process that request.")
            
            # Save to conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return {
                "success": True,
                "response": assistant_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Fallback response without LLM
            return await self._generate_fallback_response(message)
    
    async def _generate_fallback_response(self, message: str) -> Dict[str, Any]:
        """Generate a helpful response without LLM."""
        message_lower = message.lower()
        
        # Pattern matching for common questions
        if any(word in message_lower for word in ["quality", "score", "health"]):
            if self.context.get("summary"):
                score = self.context["summary"].get("quality_score", "N/A")
                issues = self.context["summary"].get("total_smells", 0)
                return {
                    "success": True,
                    "response": f"""📊 **Project Quality Overview**

Your current quality score is **{score}%** with **{issues}** total issues detected.

**Breakdown:**
- Critical Issues: {self.context["summary"].get("critical_issues", 0)}
- High Priority: {self.context["summary"].get("high_issues", 0)}

**Recommendation:** Focus on fixing critical issues first, as they often indicate security vulnerabilities or major bugs.""",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        if any(word in message_lower for word in ["risk", "risky", "dangerous"]):
            if self.context.get("top_files"):
                files_list = "\n".join([f"- `{f['path']}` (Risk: {f['risk']})" for f in self.context["top_files"]])
                return {
                    "success": True,
                    "response": f"""⚠️ **Highest Risk Files**

These files need the most attention:

{files_list}

**Why these files?** They have high cyclomatic complexity, potential security issues, or code smells that increase bug probability.""",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        if any(word in message_lower for word in ["fix", "solve", "resolve", "how to"]):
            if self.context.get("recent_issues"):
                issue = self.context["recent_issues"][0]
                return {
                    "success": True,
                    "response": f"""🔧 **Fixing Issues**

Your most critical issue is:
- **Type:** {issue['type']}
- **File:** `{issue['path']}`
- **Issue:** {issue['message']}

**General Fix Strategies:**
1. **For complexity issues:** Break large functions into smaller, focused ones
2. **For security issues:** Validate inputs, use parameterized queries, avoid eval()
3. **For code smells:** Apply SOLID principles and design patterns
4. **For duplication:** Extract common code into shared utilities

Would you like specific help with any of these issues?""",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        if any(word in message_lower for word in ["hello", "hi", "hey", "help"]):
            return {
                "success": True,
                "response": """👋 **Hello! I'm Deep Lynctus AI**

I'm your code review assistant. I can help you with:

🔍 **Analysis**
- "What's my code quality score?"
- "Which files are most risky?"
- "Show me the main issues"

🔧 **Fixes**
- "How do I fix [issue type]?"
- "What should I prioritize?"
- "Explain this code smell"

📈 **Insights**
- "How has quality changed?"
- "What patterns do you see?"
- "Suggest improvements"

Just ask me anything about your codebase!""",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Default response
        return {
            "success": True,
            "response": f"""I understand you're asking about: *"{message}"*

Based on your project analysis, here are some relevant insights:

📊 **Quick Stats:**
- Files Analyzed: {self.context.get("summary", {}).get("total_files", "N/A")}
- Issues Found: {self.context.get("summary", {}).get("total_smells", "N/A")}
- Quality Score: {self.context.get("summary", {}).get("quality_score", "N/A")}%

Try asking me:
- "What are the riskiest files?"
- "How can I improve code quality?"
- "Explain the critical issues"

I'm here to help you write better code! 🚀""",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []


# Store active chatbot sessions
_chatbot_sessions: Dict[str, CodeReviewChatbot] = {}


async def get_chatbot(project_id: str) -> CodeReviewChatbot:
    """Get or create a chatbot session for a project."""
    if project_id not in _chatbot_sessions:
        chatbot = CodeReviewChatbot(project_id)
        await chatbot.load_context()
        _chatbot_sessions[project_id] = chatbot
    return _chatbot_sessions[project_id]


async def chat_with_assistant(project_id: str, message: str, file_context: str = None) -> Dict[str, Any]:
    """Chat with the AI assistant."""
    chatbot = await get_chatbot(project_id)
    return await chatbot.chat(message, file_context)


async def clear_chat_session(project_id: str):
    """Clear a chat session."""
    if project_id in _chatbot_sessions:
        _chatbot_sessions[project_id].clear_history()
