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
            "### 🔍 DSA: Binary Search\n\n"
            "#### **Algorithm**:\n"
            "1. Initialize `low = 0` and `high = len(arr) - 1`.\n"
            "2. While `low <= high`:\n"
            "   a. Compute the middle index: `mid = low + (high - low) // 2`.\n"
            "   b. If `arr[mid] == target`, target is found. Return `mid`.\n"
            "   c. If `arr[mid] > target`, search the left half by setting `high = mid - 1`.\n"
            "   d. If `arr[mid] < target`, search the right half by setting `low = mid + 1`.\n"
            "3. If loop ends without finding target, return `-1`.\n\n"
            
            "#### **Dry Run**:\n"
            "Input Array: `arr = [1, 3, 5, 7, 9]`, Target = `7`\n"
            "- **Iteration 1**: `low = 0`, `high = 4`\n"
            "  - `mid = 0 + (4 - 0) // 2 = 2`\n"
            "  - Value at `mid` is `arr[2] = 5`\n"
            "  - Since `5 < 7`, set `low = mid + 1 = 3`\n"
            "- **Iteration 2**: `low = 3`, `high = 4`\n"
            "  - `mid = 3 + (4 - 3) // 2 = 3`\n"
            "  - Value at `mid` is `arr[3] = 7`\n"
            "  - Since `7 == 7`, target is found. Return `3`.\n\n"
            
            "#### **Complexity Analysis**:\n"
            "- **Time Complexity**:\n"
            "  - *Worst Case*: $O(\\log N)$ — array divided in half at each step.\n"
            "  - *Average Case*: $O(\\log N)$\n"
            "  - *Best Case*: $O(1)$ — target found at middle element on the first try.\n"
            "- **Space Complexity**: $O(1)$ — iterative implementation requires constant extra memory.\n\n"
            
            "#### **Code Implementation**:\n"
            "```python\n"
            "def binary_search(arr, target):\n"
            "    low = 0\n"
            "    high = len(arr) - 1\n"
            "    while low <= high:\n"
            "        mid = low + (high - low) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] > target:\n"
            "            high = mid - 1\n"
            "        else:\n"
            "            low = mid + 1\n"
            "    return -1\n"
            "```"
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
            system_instruction=(
                "You are DevDash AI, an expert programming mentor and computer science exam prep assistant. "
                "Your goal is to provide concise, structured, and exam-friendly responses by default. "
                "Never include verbose introductory or concluding filler text.\n\n"
                
                "Strictly follow these response guidelines based on the query type:\n\n"
                
                "1. **ACADEMIC PROGRAMMING QUESTIONS**:\n"
                "   - Detect if the query is a simple academic programming task (e.g., contains 'WAP', 'write a program', "
                "     'C++ program', 'Python program', etc.).\n"
                "   - Return exactly these sections in order:\n"
                "     * **Program**: The complete program code block. Do NOT include excessive comments inside simple programs.\n"
                "     * **Sample Input/Output**: Show clear example input(s) and the expected output(s).\n"
                "     * **Short Explanation**: A very brief and concise explanation of the program logic.\n"
                "     * **Time Complexity**: Clear and explicit big-O time complexity.\n"
                "     * **Space Complexity**: Clear and explicit big-O space complexity.\n\n"
                
                "2. **DSA (DATA STRUCTURES & ALGORITHMS) QUESTIONS**:\n"
                "   - Detect if the query asks for a DSA concept, algorithm, or search/sort method (e.g., 'Binary Search', 'Merge Sort', 'BFS', 'DFS').\n"
                "   - Return exactly these sections in order:\n"
                "     * **Algorithm**: Clear, step-by-step description of the algorithm.\n"
                "     * **Dry Run**: A concise, step-by-step trace showing index/variable transitions for a small sample input.\n"
                "     * **Complexity Analysis**: Time Complexity (explicitly stating Best, Average, Worst cases) and Space Complexity with brief explanations.\n"
                "     * **Code Implementation**: The complete, clean code block with minimal, essential comments.\n\n"
                
                "3. **INTERVIEW & CONCEPTUAL DEVELOPER QUESTIONS**:\n"
                "   - Detect if the query is an interview or general conceptual developer question (e.g., 'Difference between BFS and DFS', 'Flask Authentication Example').\n"
                "   - Provide detailed, thorough explanations using bullet points, comparison tables (for differences), blockquotes, and step-by-step structural workflows.\n\n"
                
                "4. **DEFAULT CONCISE FORMAT**:\n"
                "   - For all other queries, create concise, structured, direct, and exam-friendly responses.\n"
                "   - Always use proper fenced code blocks with language specifiers (e.g., ```cpp, ```python, ```sql).\n"
                "   - Use GitHub-Flavored Markdown components (bolding, headers, tables, callout blockquotes) beautifully."
            )
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
