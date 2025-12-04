from .db import get_database


class LLMService:
    """Service for generating AI-powered refactoring suggestions."""
    
    # Suggestion templates based on smell types
    SUGGESTION_TEMPLATES = {
        "High Complexity": {
            "title": "Reduce Cyclomatic Complexity",
            "rationale": "High complexity makes code harder to test and maintain. Consider breaking down complex conditionals.",
            "snippet": "# Extract complex conditions into helper methods\ndef is_valid_state():\n    return condition1 and condition2\n\nif is_valid_state():\n    # simplified logic",
            "priority": "High",
            "est_hours": 3
        },
        "Long Function": {
            "title": "Extract Function",
            "rationale": "Long functions are hard to understand and test. Break into smaller, focused functions.",
            "snippet": "# Before: one long function\n# After: multiple focused functions\ndef process_data(data):\n    validated = validate(data)\n    transformed = transform(validated)\n    return save(transformed)",
            "priority": "High",
            "est_hours": 2
        },
        "Deep Nesting": {
            "title": "Flatten Nested Code",
            "rationale": "Deep nesting reduces readability. Use early returns or guard clauses.",
            "snippet": "# Use early returns\ndef process(item):\n    if not item:\n        return None\n    if not item.valid:\n        return None\n    # Main logic here (less nested)",
            "priority": "Medium",
            "est_hours": 2
        },
        "Too Many Parameters": {
            "title": "Use Parameter Object",
            "rationale": "Too many parameters make functions hard to call and maintain.",
            "snippet": "@dataclass\nclass RequestConfig:\n    url: str\n    timeout: int\n    headers: dict\n\ndef make_request(config: RequestConfig):",
            "priority": "Medium",
            "est_hours": 2
        },
        "God Class": {
            "title": "Split Into Smaller Classes",
            "rationale": "Large classes violate single responsibility. Extract related functionality.",
            "snippet": "# Extract related methods into focused classes\nclass UserValidator:\n    def validate(self, user): ...\n\nclass UserRepository:\n    def save(self, user): ...",
            "priority": "High",
            "est_hours": 6
        },
        "Missing Docstring": {
            "title": "Add Documentation",
            "rationale": "Missing documentation makes code harder to understand and maintain.",
            "snippet": 'def calculate_risk(metrics: dict) -> float:\n    """Calculate risk score based on code metrics.\n    \n    Args:\n        metrics: Dictionary of code metrics\n    \n    Returns:\n        Risk score between 0 and 100\n    """',
            "priority": "Low",
            "est_hours": 1
        },
        "Long File": {
            "title": "Split File Into Modules",
            "rationale": "Long files are hard to navigate. Split into logical modules.",
            "snippet": "# Move related classes to separate files\n# user_service.py -> user_validator.py, user_repository.py\nfrom .user_validator import UserValidator\nfrom .user_repository import UserRepository",
            "priority": "Medium",
            "est_hours": 4
        },
        "Debug Code": {
            "title": "Remove Debug Statements",
            "rationale": "Debug code should not be in production. Use proper logging instead.",
            "snippet": "import logging\nlogger = logging.getLogger(__name__)\n\n# Instead of print() or console.log\nlogger.debug('Processing item: %s', item)",
            "priority": "Low",
            "est_hours": 1
        },
        "TODO Comment": {
            "title": "Resolve TODO Comments",
            "rationale": "Unresolved TODOs indicate incomplete work that should be addressed.",
            "snippet": "# TODO: Implement error handling -> DONE\ntry:\n    result = process(data)\nexcept ProcessingError as e:\n    logger.error('Failed: %s', e)\n    raise",
            "priority": "Low",
            "est_hours": 1
        }
    }
    
    @staticmethod
    async def fetch_suggestions(file_id: str, limit: int):
        """
        Generate refactoring suggestions based on detected smells for a file.
        """
        db = get_database()
        file_path = file_id.replace('_', '/')  # Reverse the path encoding
        
        # Try to find smells for this file
        smells = []
        try:
            if hasattr(db, '_db') and db._db is not None:
                # Search for smells matching this file path (handle both / and \)
                cursor = db._db.smells.find({
                    "$or": [
                        {"path": {"$regex": file_path.replace('/', '.'), "$options": "i"}},
                        {"path": {"$regex": file_id, "$options": "i"}}
                    ]
                })
                smells = await cursor.to_list(length=100)
        except Exception as e:
            print(f"Error fetching smells for suggestions: {e}")
            smells = []
        
        suggestions = []
        seen_types = set()
        
        for smell in smells:
            smell_type = smell.get('type', '')
            if smell_type in seen_types:
                continue
            seen_types.add(smell_type)
            
            template = LLMService.SUGGESTION_TEMPLATES.get(smell_type)
            if template:
                suggestion = {
                    "title": template["title"],
                    "rationale": f"{template['rationale']} (Line {smell.get('line', 'N/A')}: {smell.get('message', '')})",
                    "snippet": template["snippet"],
                    "priority": template["priority"],
                    "est_hours": template["est_hours"]
                }
                suggestions.append(suggestion)
        
        # If no specific suggestions, provide general ones
        if not suggestions:
            suggestions = [
                {
                    "title": "Add Unit Tests",
                    "rationale": "Improve code coverage and catch regressions early",
                    "snippet": "def test_function_name():\n    result = function_name(input)\n    assert result == expected",
                    "priority": "Medium",
                    "est_hours": 2
                },
                {
                    "title": "Add Type Hints",
                    "rationale": "Type hints improve code readability and IDE support",
                    "snippet": "def process(data: dict[str, Any]) -> Result:\n    ...",
                    "priority": "Low",
                    "est_hours": 1
                }
            ]
        
        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "Low"), 2))
        
        return {
            "file_id": file_id,
            "path": file_path,
            "suggestions": suggestions[:limit]
        }
