import logging
from flask import Blueprint, request, jsonify, session
from config import Config

# Configure logger
logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

# Initialize Gemini Client if API key is present
gemini_initialized = False
try:
    if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY.strip():
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        gemini_initialized = True
        logger.info("Google Gemini API successfully configured.")
    else:
        logger.warning("GEMINI_API_KEY is missing. AI Chat Assistant will run in Fallback/Simulation mode.")
except Exception as e:
    logger.error(f"Error configuring Google Gemini API: {e}")

SYSTEM_INSTRUCTION = (
    "You are DevDash AI, an expert programming mentor and DSA coach. "
    "Respond directly, with zero filler introduction or conclusion, using this structure:\n\n"
    
    "1. **Coding Questions**:\n"
    "   - Provide clean, concise, production-style code block with minimal comments.\n"
    "   - After code, provide exactly: Approach (2-3 lines), Time Complexity, Space Complexity.\n\n"
    
    "2. **DSA Questions**:\n"
    "   - Provide concise, interviewer-friendly competitive programming solutions.\n"
    "   - After code, provide exactly: Approach (2-3 lines), Time Complexity, Space Complexity.\n\n"
    
    "3. **Conceptual Questions**:\n"
    "   - Provide focused, direct explanations with comparison tables, workflows, or bullet points."
)

# High-fidelity simulated offline assistant response helper
def get_offline_fallback_response(message):
    """Provides structured, high-quality offline developer responses when the Gemini API key is missing or calls fail.
    This ensures the user experience remains premium and fully interactive during local development.
    """
    msg_lower = message.lower()
    
    offline_notice = (
        "> [!NOTE]\n"
        "> **Offline Simulator Active**: This is an intelligent simulated response because your `GEMINI_API_KEY` is not set in `.env`. "
        "Please add a valid key from Google AI Studio to unlock full, live AI mentoring!\n\n"
    )
    
    if "binary search" in msg_lower:
        return offline_notice + (
            "### Code\n"
            "```python\n"
            "def binary_search(arr, target):\n"
            "    low, high = 0, len(arr) - 1\n"
            "    while low <= high:\n"
            "        mid = low + (high - low) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1\n"
            "```\n\n"
            "### Approach\n"
            "Implements the Binary Search algorithm using a two-pointer interval reduction strategy, continuously halving the "
            "search space by comparing the middle element with the target and narrowing the range to the left or right subarray.\n\n"
            "### Time Complexity\n"
            "- **Worst/Average Case**: $O(\\log N)$ — the search space is divided by two at each iteration.\n"
            "- **Best Case**: $O(1)$ — target found at the middle index on the first step.\n\n"
            "### Space Complexity\n"
            "- $O(1)$ — operates iteratively using constant auxiliary space."
        )
    
    elif "flask" in msg_lower or "route" in msg_lower or "routing" in msg_lower:
        return offline_notice + (
            "### 🌶️ Flask Routing & Framework Basics\n\n"
            "In Flask, **routing** binds a URL to a specific Python function. When a user visits the URL, that function is executed to return the response.\n\n"
            "#### Modern Flask Routing Example:\n"
            "```python\n"
            "from flask import Flask, jsonify, request\n"
            "app = Flask(__name__)\n\n"
            "# 1. Basic Route\n"
            "@app.route('/')\n"
            "def home():\n"
            "    return \"Hello DevDash!\"\n\n"
            "# 2. REST API Route with variables and methods\n"
            "@app.route('/api/goals/<int:goal_id>', methods=['PUT'])\n"
            "def update_goal(goal_id):\n"
            "    data = request.get_json()\n"
            "    return jsonify({\"status\": \"updated\", \"id\": goal_id, \"data\": data})\n"
            "```\n\n"
            "#### 🛠️ Key Tips:\n"
            "- Always use specific HTTP methods (`methods=['POST', 'GET']`) for security and clarity.\n"
            "- Use type converters like `<int:id>` or `<string:name>` directly in URLs to sanitize parameters.\n"
            "- Return dynamic JSON using `jsonify()` when building RESTful APIs."
        )
        
    elif "sql" in msg_lower or "join" in msg_lower:
        return offline_notice + (
            "### 🗄️ SQL Joins Cheat-Sheet\n\n"
            "SQL **JOIN** clauses are used to combine rows from two or more tables, based on a related column between them.\n\n"
            "#### Types of Joins:\n"
            "1. **INNER JOIN**: Returns records that have matching values in both tables.\n"
            "2. **LEFT (OUTER) JOIN**: Returns all records from the left table, and matching records from the right. If no match, right columns return `NULL`.\n"
            "3. **RIGHT (OUTER) JOIN**: Returns all records from the right table, and matching records from the left.\n"
            "4. **FULL (OUTER) JOIN**: Returns all records when there is a match in either left or right table.\n\n"
            "#### Visual & Query Representation:\n"
            "```sql\n"
            "-- Query to connect Users and their Daily Goals\n"
            "SELECT users.username, goals.title, goals.priority\n"
            "FROM users\n"
            "INNER JOIN goals ON users.id = goals.user_id;\n"
            "```"
        )
        
    elif "debug" in msg_lower or "error" in msg_lower:
        return offline_notice + (
            "### 🐞 Smart Debugging Methodology\n\n"
            "When debugging code, follow this standard production-style approach:\n\n"
            "1. **Isolate the Error**: Read the traceback from bottom to top. Identify the file, line number, and error type (e.g. `KeyError`, `TypeError`).\n"
            "2. **Check Current State**: Print or log variables leading up to the error. Make sure variables are initialized and match expected shapes/types.\n"
            "3. **Write a Minimal Test**: Reproduce the error in a separate scratch script using the simplest inputs possible.\n"
            "4. **Verify Database Bounds**: If SQL is failing, check if the columns exist, datatypes match, and connection strings are correctly loaded."
        )

    # General fallback reply
    return offline_notice + (
        f"### 👋 Welcome to DevDash AI Assistant!\n\n"
        f"You asked: *\"{message}\"*\n\n"
        f"I am fully ready to answer all your developer questions, explain technical concepts, write code, "
        f"and help you design systems. \n\n"
        f"**Suggested topics to ask me:**\n"
        f"- *\"Explain Binary Search\"*\n"
        f"- *\"Explain Flask Routing basics\"*\n"
        f"- *\"Show me a cheat sheet for SQL Joins\"*\n"
        f"- *\"Tell me how to debug a TypeError in Python\"*\n\n"
        f"🔧 **API Setup Tip**: To get real-time, custom AI answers, simply sign up for a free Gemini API key "
        f"at [Google AI Studio](https://aistudio.google.com/) and paste it as `GEMINI_API_KEY=your_key` inside your `.env` file, then restart the Flask server!"
    )


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint that forwards user requests to Google Gemini AI API with graceful local fallback capabilities."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized. Please log in first."}), 401
        
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"success": False, "message": "Message is required."}), 400
        
    # If Gemini is not configured, fall back immediately to offline simulated helper
    if not gemini_initialized:
        logger.info("Serving offline fallback response for chat query.")
        reply = get_offline_fallback_response(user_message)
        return jsonify({"reply": reply}), 200
        
    try:
        import google.generativeai as genai
        
        # We will use gemini-2.5-flash which is extremely fast and perfect for assistant chats
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Request generation
        response = model.generate_content(user_message)
        
        if response and response.text:
            return jsonify({"reply": response.text.strip()}), 200
        else:
            raise Exception("Empty response received from Gemini.")
            
    except Exception as e:
        logger.error(f"Gemini API execution error: {e}. Falling back to simulated response.")
        # Graceful fallback: do not crash. Return a simulated response instead!
        reply = get_offline_fallback_response(user_message)
        return jsonify({"reply": reply}), 200
