from .db import get_database


class LLMService:
    """Service for generating AI-powered refactoring suggestions."""
    
    # Comprehensive suggestion templates based on smell types
    SUGGESTION_TEMPLATES = {
        # ===== CRITICAL ISSUES (Priority: High) =====
        "High Complexity": {
            "title": "Reduce Cyclomatic Complexity",
            "rationale": "High complexity is a major bug predictor. Consider strategy pattern or decomposition.",
            "snippet": """# Extract complex conditions into strategy pattern
class ValidationStrategy:
    def validate(self, data): ...

class RuleBasedValidator(ValidationStrategy):
    def validate(self, data):
        return self._check_rules(data)

# Usage: validator.validate(data) instead of if/elif chains""",
            "priority": "High",
            "est_hours": 4
        },
        "Callback Hell": {
            "title": "Refactor to Async/Await or Promises",
            "rationale": "Deeply nested callbacks create 'pyramid of doom', making code hard to read and debug.",
            "snippet": """// Before: Callback Hell
getData(function(a) {
  getMoreData(a, function(b) {
    getEvenMore(b, function(c) { ... });
  });
});

// After: Async/Await
async function fetchAllData() {
  const a = await getData();
  const b = await getMoreData(a);
  const c = await getEvenMore(b);
  return c;
}""",
            "priority": "High",
            "est_hours": 3
        },
        "Empty Catch Block": {
            "title": "Add Proper Error Handling",
            "rationale": "Swallowing exceptions hides bugs and makes debugging nearly impossible.",
            "snippet": """// Before: Silent failure
try { riskyOperation(); } catch (e) {}

// After: Proper handling
try {
  riskyOperation();
} catch (error) {
  console.error('Operation failed:', error);
  // Re-throw, return default, or handle appropriately
  throw new AppError('Operation failed', { cause: error });
}""",
            "priority": "High",
            "est_hours": 2
        },
        "Potential Memory Leak": {
            "title": "Add Event Listener Cleanup",
            "rationale": "Event listeners without cleanup cause memory leaks in long-running applications.",
            "snippet": """// React: Use useEffect cleanup
useEffect(() => {
  const handler = () => { ... };
  window.addEventListener('resize', handler);
  return () => window.removeEventListener('resize', handler);
}, []);

// Vanilla JS: Use AbortController
const controller = new AbortController();
element.addEventListener('click', handler, { signal: controller.signal });
// Later: controller.abort(); // removes all listeners""",
            "priority": "High",
            "est_hours": 2
        },
        "Long Function": {
            "title": "Extract to Smaller Functions",
            "rationale": "Functions over 80 lines are hard to test and maintain. Apply Single Responsibility Principle.",
            "snippet": """// Before: Monolithic function
function processOrder(order) {
  // 100+ lines of validation, calculation, saving...
}

// After: Composed smaller functions
function processOrder(order) {
  const validated = validateOrder(order);
  const calculated = calculateTotals(validated);
  return saveOrder(calculated);
}

// Each function: 10-20 lines, single responsibility""",
            "priority": "High",
            "est_hours": 3
        },
        "God Class": {
            "title": "Split Into Focused Classes",
            "rationale": "God classes violate single responsibility and are a major maintenance burden.",
            "snippet": """// Before: UserManager does everything
class UserManager {
  validate() { }
  save() { }
  sendEmail() { }
  generateReport() { }
}

// After: Separate concerns
class UserValidator { validate(user) { } }
class UserRepository { save(user) { } }
class EmailService { sendWelcome(user) { } }""",
            "priority": "High",
            "est_hours": 6
        },
        
        # ===== IMPORTANT ISSUES (Priority: Medium) =====
        "Deep Nesting": {
            "title": "Flatten With Guard Clauses",
            "rationale": "Deep nesting increases cognitive load. Use early returns to reduce indentation.",
            "snippet": """// Before: Deeply nested
function process(item) {
  if (item) {
    if (item.valid) {
      if (item.data) {
        // actual logic
      }
    }
  }
}

// After: Guard clauses
function process(item) {
  if (!item) return null;
  if (!item.valid) return null;
  if (!item.data) return null;
  
  // actual logic at base indentation level
}""",
            "priority": "Medium",
            "est_hours": 2
        },
        "Nested Ternary": {
            "title": "Replace With If/Else or Helper Function",
            "rationale": "Nested ternaries are hard to read and maintain.",
            "snippet": """// Before: Nested ternary
const result = a ? (b ? x : y) : (c ? z : w);

// After: Clear if/else
function getResult(a, b, c) {
  if (a) return b ? x : y;
  return c ? z : w;
}

// Or use a lookup object
const results = { 'ab': x, 'a': y, 'c': z, 'default': w };""",
            "priority": "Medium",
            "est_hours": 1
        },
        "Magic Numbers": {
            "title": "Extract Named Constants",
            "rationale": "Magic numbers lack context and are error-prone during maintenance.",
            "snippet": """// Before: What does 86400 mean?
setTimeout(cleanup, 86400 * 1000);

// After: Self-documenting
const SECONDS_PER_DAY = 86400;
const MS_PER_SECOND = 1000;
setTimeout(cleanup, SECONDS_PER_DAY * MS_PER_SECOND);

// Or use an enum/config object
const TIMEOUTS = { daily: 86400000, hourly: 3600000 };""",
            "priority": "Medium",
            "est_hours": 1
        },
        "Duplicate String Literals": {
            "title": "Extract to Constants",
            "rationale": "Duplicate strings are maintenance hazards - change one, miss others.",
            "snippet": """// Before: String repeated everywhere
if (status === 'pending') { }
return { status: 'pending' };

// After: Single source of truth
const STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected'
};
if (status === STATUS.PENDING) { }""",
            "priority": "Medium",
            "est_hours": 1
        },
        "Too Many Parameters": {
            "title": "Use Options Object",
            "rationale": "Many parameters are hard to remember and error-prone.",
            "snippet": """// Before: Too many params
function createUser(name, email, age, role, dept, manager) { }

// After: Options object
function createUser({ name, email, age, role, dept, manager }) { }

// With TypeScript interface
interface CreateUserOptions {
  name: string;
  email: string;
  age?: number;
  role?: string;
}""",
            "priority": "Medium",
            "est_hours": 2
        },
        "Long File": {
            "title": "Split Into Modules",
            "rationale": "Large files are hard to navigate. Split by feature or responsibility.",
            "snippet": """// Before: utils.js (500+ lines)
// Contains: validation, formatting, API calls, etc.

// After: Separate modules
import { validateEmail, validatePhone } from './validation';
import { formatDate, formatCurrency } from './formatting';
import { fetchUser, createUser } from './api/users';""",
            "priority": "Medium",
            "est_hours": 4
        },
        
        # ===== MINOR ISSUES (Priority: Low) =====
        "Excessive Any Type": {
            "title": "Add Proper TypeScript Types",
            "rationale": "Using 'any' defeats TypeScript's purpose. Add proper types for safety.",
            "snippet": """// Before: any everywhere
function process(data: any): any { }

// After: Proper types
interface InputData {
  id: string;
  values: number[];
}
interface Result {
  success: boolean;
  message: string;
}
function process(data: InputData): Result { }""",
            "priority": "Medium",
            "est_hours": 2
        },
        "Debug Code": {
            "title": "Remove Debug Statements",
            "rationale": "console.log clutters output. Use proper logging for production.",
            "snippet": """// Before: Debug logs everywhere
console.log('got here', data);

// After: Proper logging
import { logger } from './logger';
logger.debug('Processing data', { id: data.id });
// Configure log levels per environment""",
            "priority": "Low",
            "est_hours": 1
        },
        "Commented Code": {
            "title": "Remove Dead Code",
            "rationale": "Commented code creates confusion. Use version control for history.",
            "snippet": """// Before: Commented code blocks
// function oldImplementation() {
//   // 50 lines of old code
// }

// After: Just delete it
// Git history preserves old implementations
// Add a commit message: "Remove deprecated oldImplementation"
""",
            "priority": "Low",
            "est_hours": 0.5
        },
        "Unresolved TODOs": {
            "title": "Address TODO Comments",
            "rationale": "TODOs represent technical debt. Track in issue tracker or resolve.",
            "snippet": """// Before: TODO sitting forever
// TODO: add error handling

// After: Actually implement it
try {
  await riskyOperation();
} catch (error) {
  handleError(error);
}

// Or create a tracked issue
// ISSUE-123: Add comprehensive error handling""",
            "priority": "Low",
            "est_hours": 1
        },
        "Missing Docstring": {
            "title": "Add Documentation",
            "rationale": "Documentation helps future maintainers understand intent.",
            "snippet": '''"""Calculate risk score based on code metrics.

Args:
    metrics: Dictionary containing loc, complexity, etc.
    weights: Optional custom weights for scoring.

Returns:
    Risk score between 0 and 100.
    
Raises:
    ValueError: If metrics are invalid.

Example:
    >>> calculate_risk({'loc': 100, 'complexity': 5})
    35.5
"""''',
            "priority": "Low",
            "est_hours": 1
        },
        "TODO Comment": {
            "title": "Resolve TODO Comments",
            "rationale": "Unresolved TODOs indicate incomplete work.",
            "snippet": """# TODO: Implement error handling -> DONE
try:
    result = process(data)
except ProcessingError as e:
    logger.error('Failed: %s', e)
    raise""",
            "priority": "Low",
            "est_hours": 1
        },
        
        # ===== PYTHON-SPECIFIC SMELLS =====
        "Bare Except": {
            "title": "Specify Exception Types",
            "rationale": "Bare 'except:' catches SystemExit and KeyboardInterrupt, causing unexpected behavior.",
            "snippet": """# Before: Catches everything including Ctrl+C
try:
    risky_operation()
except:
    pass

# After: Specific exception handling
try:
    risky_operation()
except ValueError as e:
    logger.error("Invalid value: %s", e)
except IOError as e:
    logger.error("IO error: %s", e)
except Exception as e:
    logger.exception("Unexpected error")
    raise""",
            "priority": "High",
            "est_hours": 1
        },
        "Swallowed Exception": {
            "title": "Handle Exceptions Properly",
            "rationale": "Silent 'pass' in except block hides errors and makes debugging impossible.",
            "snippet": """# Before: Silent failure
try:
    save_data(data)
except Exception:
    pass

# After: Proper handling
try:
    save_data(data)
except IOError as e:
    logger.error("Failed to save: %s", e)
    return None  # Or raise a custom exception
except Exception as e:
    logger.exception("Unexpected error saving data")
    raise DataSaveError("Save failed") from e""",
            "priority": "High",
            "est_hours": 1
        },
        "Star Import": {
            "title": "Use Explicit Imports",
            "rationale": "Star imports pollute namespace and make it hard to track where names come from.",
            "snippet": """# Before: Namespace pollution
from utils import *

# After: Explicit imports
from utils import validate_email, format_date, parse_json

# Or import the module
import utils
utils.validate_email(email)""",
            "priority": "Medium",
            "est_hours": 1
        },
        "Data Clump": {
            "title": "Use Data Classes",
            "rationale": "Too many related attributes suggest a missing abstraction.",
            "snippet": """# Before: Many related attributes
class Order:
    def __init__(self):
        self.shipping_street = None
        self.shipping_city = None
        self.shipping_zip = None
        self.billing_street = None
        # ... many more

# After: Extract to data class
@dataclass
class Address:
    street: str
    city: str
    zip_code: str

class Order:
    shipping_address: Address
    billing_address: Address""",
            "priority": "Medium",
            "est_hours": 2
        },
        "Magic Number": {
            "title": "Extract Named Constants",
            "rationale": "Magic numbers lack context and are error-prone during maintenance.",
            "snippet": """# Before: What does 86400 mean?
if elapsed > 86400:
    refresh_cache()

# After: Self-documenting
SECONDS_PER_DAY = 86400
CACHE_TTL_SECONDS = SECONDS_PER_DAY

if elapsed > CACHE_TTL_SECONDS:
    refresh_cache()""",
            "priority": "Medium",
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
