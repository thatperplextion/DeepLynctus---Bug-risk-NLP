"""
AI Chatbot Service - Code review assistant with intelligent risk filtering.
Focuses on critical and high-priority issues while ignoring minor warnings.
"""

from datetime import datetime
from typing import Dict, List, Any


class CodeReviewChatbot:
    """AI-powered code review assistant with smart risk filtering."""
    
    # Risk thresholds - only show issues above these levels
    CRITICAL_RISK_THRESHOLD = 80
    HIGH_RISK_THRESHOLD = 60
    MEDIUM_RISK_THRESHOLD = 40
    IGNORE_BELOW_THRESHOLD = 30  # Ignore trivial issues below this
    
    # Severity levels to focus on
    IMPORTANT_SEVERITIES = {"critical", "high"}
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.conversation_history: List[Dict] = []
        self.context: Dict[str, Any] = {}
        
    async def load_context(self):
        """Load project context for the chatbot, filtering for important issues only."""
        from services.db import db
        
        project = await db.get_project(self.project_id)
        if project:
            self.context["project"] = {
                "name": project.get("name", "Unknown"),
                "repo_url": project.get("repo_url", "")
            }
        
        # Get metrics and filter by risk threshold
        metrics = await db.get_metrics(self.project_id)
        if metrics:
            # Only include files with significant risk
            important_metrics = [m for m in metrics if m.get("risk_score", 0) >= self.IGNORE_BELOW_THRESHOLD]
            sorted_metrics = sorted(important_metrics, key=lambda x: x.get("risk_score", 0), reverse=True)
            
            self.context["top_files"] = [
                {
                    "path": m.get("path", ""),
                    "risk": m.get("risk_score", 0),
                    "tier": self._get_risk_tier(m.get("risk_score", 0))
                }
                for m in sorted_metrics[:5]
            ]
            self.context["total_files"] = len(metrics)
            self.context["important_files_count"] = len(important_metrics)
        
        # Get smells and filter for critical/high severity only
        smells = await db.get_smells(self.project_id)
        if smells:
            # Filter to only show critical and high severity issues
            important_smells = [
                s for s in smells 
                if s.get("severity", "").lower() in self.IMPORTANT_SEVERITIES
            ]
            
            self.context["total_smells"] = len(smells)
            self.context["important_smells"] = len(important_smells)
            self.context["ignored_trivial_issues"] = len(smells) - len(important_smells)
            
            self.context["recent_critical_issues"] = [
                {
                    "type": s.get("type", ""),
                    "path": s.get("path", ""),
                    "message": s.get("message", ""),
                    "severity": s.get("severity", "").upper()
                }
                for s in important_smells[:10]
            ]
            
            # Count by severity - only critical/high
            self.context["critical_issues"] = sum(
                1 for s in smells if s.get("severity", "").lower() == "critical"
            )
            self.context["high_issues"] = sum(
                1 for s in smells if s.get("severity", "").lower() == "high"
            )
        
        # Calculate quality score based on important issues only
        risks = await db.get_risks(self.project_id)
        if risks:
            important_risks = [r for r in risks if r.get("risk_score", 0) >= self.IGNORE_BELOW_THRESHOLD]
            if important_risks:
                avg_risk = sum(r.get("risk_score", 0) for r in important_risks) / len(important_risks)
            else:
                avg_risk = 0
            self.context["quality_score"] = max(0, 100 - avg_risk)
            self.context["critical_risk_files"] = [
                r for r in risks if r.get("risk_score", 0) >= self.CRITICAL_RISK_THRESHOLD
            ]
    
    def _get_risk_tier(self, risk_score: float) -> str:
        """Get risk tier based on score."""
        if risk_score >= self.CRITICAL_RISK_THRESHOLD:
            return "🔴 CRITICAL"
        elif risk_score >= self.HIGH_RISK_THRESHOLD:
            return "🟠 HIGH"
        elif risk_score >= self.MEDIUM_RISK_THRESHOLD:
            return "🟡 MEDIUM"
        return "🟢 LOW"
    
    async def chat(self, message: str, file_context: str = None) -> Dict[str, Any]:
        """Process a chat message and return an intelligent response."""
        if not self.context:
            await self.load_context()
        
        # Generate response based on message patterns
        response = self._generate_response(message)
        
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_response(self, message: str) -> str:
        """Generate an intelligent response focusing on important issues."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["quality", "score", "health", "status"]):
            score = self.context.get("quality_score", "N/A")
            critical = self.context.get("critical_issues", 0)
            high = self.context.get("high_issues", 0)
            important = self.context.get("important_smells", 0)
            ignored = self.context.get("ignored_trivial_issues", 0)
            
            if critical == 0 and high == 0:
                return f"""✅ **Project Quality: EXCELLENT**

Your quality score is **{score:.1f}%** - Great work! 🎉

📊 **Summary:**
- Critical Issues: **0** ✓
- High Priority Issues: **0** ✓
- Total Files Analyzed: {self.context.get("total_files", 0)}
- Ignored Minor Issues: {ignored}

**Status:** No significant issues requiring immediate attention. Your codebase is healthy!"""
            
            elif critical == 0:
                return f"""⚠️ **Project Quality: GOOD**

Your quality score is **{score:.1f}%** - Almost perfect! 📈

📊 **Summary:**
- Critical Issues: **0** ✓
- High Priority Issues: **{high}** ⚠️ (needs attention)
- Important Issues: {important}
- Trivial Issues Ignored: {ignored}

**Action Items:**
Focus on fixing the **{high} high-priority issues** to improve quality further. Minor issues are being ignored as they have negligible impact."""
            
            else:
                return f"""🚨 **Project Quality: REQUIRES ATTENTION**

Your quality score is **{score:.1f}%** - Urgent action needed! 🔴

📊 **Summary:**
- **Critical Issues: {critical}** 🔴 (URGENT!)
- **High Priority Issues: {high}** 🟠
- Important Issues: {important}
- Trivial Issues (ignored): {ignored}

**⚡ IMMEDIATE ACTION:**
Fix the **{critical} CRITICAL issues** first - they represent significant bugs or security risks. Then address the **{high} high-priority issues**.

**Minor issues ({ignored}) are ignored** as they have negligible impact on code quality."""
        
        if any(word in message_lower for word in ["risk", "risky", "dangerous", "critical"]):
            critical_files = self.context.get("critical_risk_files", [])
            top_files = self.context.get("top_files", [])
            
            if not critical_files and not top_files:
                return """✅ **No Critical Risks Detected**

Your codebase is free from critical and high-risk files. Excellent work! 🎉"""
            
            if critical_files:
                critical_list = "\n".join([
                    f"🔴 `{f['path']}` (Risk: **{f.get('risk_score', 0):.0f}%**)"
                    for f in critical_files[:5]
                ])
                return f"""🚨 **CRITICAL FILES - URGENT ATTENTION REQUIRED**

These files pose significant security or stability risks:

{critical_list}

**Why Critical?**
- High cyclomatic complexity (hard to maintain/test)
- Potential security vulnerabilities
- Major bug probability detected by AI model
- Often involve external inputs or sensitive operations

**Action:** Review and refactor these files immediately."""
            
            if top_files:
                files_list = "\n".join([
                    f"{f['tier']} `{f['path']}` (Risk: {f['risk']:.0f}%)"
                    for f in top_files if f['risk'] >= self.HIGH_RISK_THRESHOLD
                ])
                
                if files_list:
                    return f"""⚠️ **HIGH-RISK FILES - ATTENTION NEEDED**

Files with significant complexity or risk factors:

{files_list}

**Why Important?**
- Elevated cyclomatic complexity
- Code duplication detected
- Increased likelihood of bugs
- May need refactoring

**Recommendation:** Plan refactoring for these files in your next sprint."""
                else:
                    return "✅ No high-risk files detected. Your codebase structure is healthy!"
            
            return "No significant risk data available yet. Analyze a repository first."
        
        if any(word in message_lower for word in ["fix", "solve", "resolve", "how", "help"]):
            critical_issues = self.context.get("recent_critical_issues", [])
            
            if critical_issues:
                issue = critical_issues[0]
                severity_color = "🔴" if issue.get("severity") == "CRITICAL" else "🟠"
                
                return f"""{severity_color} **PRIORITY FIX: {issue['type'].upper()}**

📍 Location: `{issue['path']}`
**Issue:** {issue['message']}

**Fix Strategy by Issue Type:**

1. **Security Vulnerabilities:**
   - Validate all user inputs
   - Use parameterized queries (SQL injection prevention)
   - Never use eval() or exec()
   - Implement proper authentication/authorization

2. **Complex Functions (High Cyclomatic Complexity):**
   - Break into smaller, focused functions (max 10-15 lines per function)
   - Extract conditional logic into separate functions
   - Use early returns to reduce nesting

3. **Code Duplication:**
   - Extract duplicated code into shared utilities
   - Use inheritance or composition for common patterns
   - Create helper functions/modules

4. **Memory/Performance Issues:**
   - Profile code to identify bottlenecks
   - Optimize algorithms (use better data structures)
   - Cache expensive computations

**Next Steps:** Would you like specific code examples for fixing this?"""
            
            return """🔧 **How to Improve Your Code**

Good news - no critical issues to fix right now! Here are general improvements:

1. **Reduce Complexity:** Aim for simple, focused functions
2. **Remove Duplication:** DRY principle - Don't Repeat Yourself
3. **Add Tests:** Increase test coverage for existing code
4. **Document Code:** Clear comments for complex logic
5. **Security:** Review authentication and input validation

**Tip:** Focus on critical and high-priority issues first. Ignore minor warnings."""
        
        if any(word in message_lower for word in ["issue", "problem", "bug", "smell", "error"]):
            critical_issues = self.context.get("recent_critical_issues", [])
            important_count = self.context.get("important_smells", 0)
            trivial_count = self.context.get("ignored_trivial_issues", 0)
            
            if critical_issues:
                issues_list = "\n".join([
                    f"{'🔴' if i.get('severity') == 'CRITICAL' else '🟠'} [{i['type']}] `{i['path']}`: {i['message'][:70]}..."
                    for i in critical_issues[:5]
                ])
                return f"""⚠️ **IMPORTANT ISSUES DETECTED**

{issues_list}

**Statistics:**
- Important Issues: **{important_count}** (shown above)
- Trivial Issues: {trivial_count} (ignored - low impact)

**Focus Strategy:**
Fix the important issues above. The {trivial_count} trivial issues have negligible impact and can be deferred."""
            
            if trivial_count > 0:
                return f"""✅ **EXCELLENT! No Critical Issues**

Your codebase has no critical or high-priority issues! 🎉

**Minor Stats:**
- Trivial/Low-Impact Issues: {trivial_count} (automatically ignored)

These are minor code style or documentation suggestions that don't affect functionality. Your code is in great shape! 🚀"""
            
            return "No issues found in your codebase. Excellent work! ✨"
        
        if any(word in message_lower for word in ["hello", "hi", "hey", "help", "start"]):
            critical = self.context.get("critical_issues", 0)
            high = self.context.get("high_issues", 0)
            
            status = "✅ HEALTHY" if critical == 0 and high == 0 else "⚠️ ACTION NEEDED"
            
            return f"""👋 **Deep Lynctus AI - Code Review Assistant**

**Your Project Status: {status}**

I'm your intelligent code review assistant. I focus on **important issues** and ignore minor warnings.

🔍 **Analysis**
- "What's my code quality?"
- "Show critical issues"
- "Which files are risky?"

🔧 **Fixes**
- "How do I fix critical issues?"
- "What should I prioritize?"
- "Explain this bug"

📈 **Insights**
- "Is my code secure?"
- "What needs refactoring?"
- "Any patterns to improve?"

💡 **Smart Filtering:**
I automatically ignore trivial issues and only highlight significant risks.

Just ask away! 🚀"""
        
        # Default response
        important_issues = self.context.get("important_smells", 0)
        critical = self.context.get("critical_issues", 0)
        
        if critical > 0:
            urgency = f"🔴 **{critical} CRITICAL ISSUES** require immediate attention!"
        elif important_issues > 0:
            urgency = f"🟠 **{important_issues} important issues** need to be addressed"
        else:
            urgency = "✅ **No critical issues** - Your code is healthy!"
        
        return f"""I'm here to help with your code! 

{urgency}

📊 **Quick Overview:**
- Files Analyzed: {self.context.get("total_files", "N/A")}
- Important Issues: {important_issues}
- Quality Score: {self.context.get("quality_score", "N/A"):.0f}%

Try asking me:
- "Show me critical issues"
- "How do I improve code quality?"
- "Which files are most risky?"
- "How do I fix [specific issue]?"

I focus on **real, important issues** and ignore trivial warnings. 🚀"""
    
    def clear_history(self):
        self.conversation_history = []


_chatbot_sessions: Dict[str, CodeReviewChatbot] = {}


async def get_chatbot(project_id: str) -> CodeReviewChatbot:
    if project_id not in _chatbot_sessions:
        chatbot = CodeReviewChatbot(project_id)
        await chatbot.load_context()
        _chatbot_sessions[project_id] = chatbot
    return _chatbot_sessions[project_id]


async def chat_with_assistant(project_id: str, message: str, file_context: str = None) -> Dict[str, Any]:
    chatbot = await get_chatbot(project_id)
    return await chatbot.chat(message, file_context)


async def clear_chat_session(project_id: str):
    if project_id in _chatbot_sessions:
        _chatbot_sessions[project_id].clear_history()
