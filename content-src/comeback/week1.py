from _helpers import code

ITEMS = [
    {
        "id": "cb-w1-fstring", "type": "code", "stage": "week1", "week": 1, "difficulty": 1,
        "tags": ["strings", "f-strings"], "pattern": "f-strings",
        "title": "Greeting with an f-string",
        "prompt": "Write `greet(name, n)` that returns `'Hi Ada, you have 3 new messages'`.",
        "starter": code('''
            def greet(name, n):
                pass
        '''),
        "tests": code('''
            def test_basic():
                assert greet("Ada", 3) == "Hi Ada, you have 3 new messages"
            def test_zero():
                assert greet("Bo", 0) == "Hi Bo, you have 0 new messages"
        '''),
        "hints": ["Python's template strings start with f before the quote.",
                  "Inside an f-string, put expressions in {curly braces}.",
                  "return f\"Hi {name}, you have ... new messages\""],
        "solution": code('''
            def greet(name, n):
                return f"Hi {name}, you have {n} new messages"
        '''),
        "ts": "`Hi ${name}, you have ${n} new messages`",
        "lesson": "f-strings are Python's template literals: f\"{expr}\". Format specs go after a colon: f\"{price:.2f}\".",
    },
    {
        "id": "cb-w1-slice-rev", "type": "predict", "kind": "output", "stage": "week1", "week": 1,
        "difficulty": 1, "tags": ["slicing"], "pattern": "slicing",
        "code": code('''
            s = "python"
            print(s[::-1][:3])
        '''),
        "question": "What does this print?",
        "choices": ["noh", "pyt", "nohtyp", "hon"],
        "answer": 0,
        "explanation": "s[::-1] reverses to 'nohtyp'; [:3] takes the first three characters.",
    },
]
