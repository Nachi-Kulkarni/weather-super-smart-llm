"""
Soil Crop Advisor — 10-Session Benchmark Suite
Runs 10 multi-turn conversations through the /chat endpoint,
then uses an LLM judge to score each session on a detailed rubric.
"""

import json
import time
import sys
import urllib.request
import urllib.error

API_BASE = "http://127.0.0.1:8000"

# ---------------------------------------------------------------------------
# 10 test scenarios — each has 5 user turns
# ---------------------------------------------------------------------------

SESSIONS = [
    {
        "name": "Cold start — vague question, no data",
        "turns": [
            "I have a farm. What should I grow?",
            "It's in Karnataka, near Tumkur",
            "I got my soil tested — N is 180, P is 22, K is 180",
            "It's for kharif season",
            "What about groundnut — is that a safe bet for my soil?",
        ],
    },
    {
        "name": "Partial data — has location, missing soil",
        "turns": [
            "Can you recommend crops for Madhya Pradesh rabi season?",
            "I don't have a full soil test, but my neighbour said the soil is low in nitrogen",
            "OK let me check — N is around 90, P is 12, K is 150. That's all I have right now",
            "Do I really need pH and EC values too?",
            "Fair enough. Can you run what you have and flag what's uncertain?",
        ],
    },
    {
        "name": "Full data upfront — should use tool immediately",
        "turns": [
            "Rank kharif crops for me. Karnataka, Tumkur district. Soil N 180 P 22 K 180 pH 6.7.",
            "Why is wheat not in the results?",
            "What would change if I target 60 q/ha yield instead of defaults?",
            "How much urea and DAP do I actually need to buy for groundnut?",
            "Is this recommendation something I can take to my agri officer?",
        ],
    },
    {
        "name": "Wrong season — asking for kharif wheat",
        "turns": [
            "I want to grow wheat this kharif in Karnataka. What fertilizer do I need?",
            "But I've seen people grow wheat in monsoon. Are you sure it's not suitable?",
            "OK what about rabi then — can you rank rabi crops for the same soil?",
            "Between wheat and ragi for rabi, which needs less fertilizer?",
            "What's the risk if I push wheat yield target to 55 q/ha?",
        ],
    },
    {
        "name": "Drill-down after recommendation",
        "turns": [
            "I'm in Raichur, Karnataka. Soil N 220 P 15 K 250. What kharif crops work?",
            "Why did ragi score higher than maize?",
            "Can you break down the scoring components for ragi?",
            "What happens if my P goes from 15 to 30 after adding SSP?",
            "Give me the scoring policy — how do confidence bands work?",
        ],
    },
    {
        "name": "Extreme soil values — stress test",
        "turns": [
            "My soil test came back weird. N is 450, P is 3, K is 500. Karnataka kharif.",
            "That N and K seem too high — should I be concerned?",
            "Is there any crop that would actually work with these numbers?",
            "What if I add 100 kg P through DAP first, then retest?",
            "Can you just run the recommendation as-is so I can see what the system says?",
        ],
    },
    {
        "name": "Multi-crop comparison",
        "turns": [
            "I'm deciding between rice and maize for my kharif plot. Karnataka, Tumkur.",
            "My soil is N 150 P 30 K 200. Which is better suited?",
            "What about input cost — which one costs more to fertilize?",
            "If water is limited, does that change your recommendation?",
            "OK run both and let me see the side-by-side numbers",
        ],
    },
    {
        "name": "Advisory without recommendation — general knowledge",
        "turns": [
            "What does N-P-K actually mean on a soil test report?",
            "My report says P2O5 — is that the same as P?",
            "How do I convert fertilizer recommendation in P2O5 to actual DAP?",
            "What's the difference between confidence band A and C?",
            "Can you explain the scoring system you use?",
        ],
    },
    {
        "name": "User corrects their own info",
        "turns": [
            "I want crop recommendations. Tamil Nadu, kharif, soil N 200 P 18 K 190",
            "Wait, I messed up. The N is actually 120, not 200. And it's rabi not kharif",
            "Also the state is Karnataka not Tamil Nadu. Sorry. Let me start over — Karnataka, rabi, N 120 P 18 K 190",
            "Can you compare this to what the wrong numbers would have given?",
            "How sensitive is the ranking to a 80-point change in nitrogen?",
        ],
    },
    {
        "name": "New farmer onboarding — hesitant and uncertain",
        "turns": [
            "Hi, I'm new to farming. I just got a soil test but I don't understand it",
            "The report has lots of numbers — nitrogen 140, phosphorus 25, potassium 170, pH 6.3",
            "I'm in Dharwad, Karnataka. I want to grow something in the coming season",
            "I don't know which season — when should I plant?",
            "Let's go with kharif then. What do you recommend for a first-time farmer?",
        ],
    },
]

# ---------------------------------------------------------------------------
# Judge rubric
# ---------------------------------------------------------------------------

JUDGE_PROMPT = """\
You are an impartial agronomy advisor evaluating a chat assistant called "Soil Crop Advisor".

## Your task
Rate the assistant's performance in this conversation on a scale of 0-10.
Be strict. Average performance should score 5/10. Only genuinely excellent work gets 8+.

## Rubric (each scored 0-2, sum = /10)

### 1. Asks before assuming (0-2)
- 2: Always asks clarifying questions when info is missing. Never assumes location/soil/season.
- 1: Sometimes asks but occasionally guesses or gives generic answers instead of asking.
- 0: Dumps generic lists without asking questions. Assumes values not provided.

### 2. Tool usage correctness (0-2)
- 2: Uses run_recommendation only when sufficient data is available. JSON is valid. Never calls without location/soil/season.
- 1: Calls tool sometimes when data is incomplete, or has minor formatting issues.
- 0: Calls tool with made-up values, wrong JSON keys, or calls when it shouldn't.

### 3. Answer quality and accuracy (0-2)
- 2: Answers are factually correct, practical, and specific to the user's situation. Cites confidence bands and caveats.
- 1: Mostly correct but some vagueness or minor inaccuracies.
- 0: Incorrect advice, hallucinated data, or dangerous agronomy recommendations.

### 4. Conversation flow and conciseness (0-2)
- 2: Natural back-and-forth. Asks 1-3 focused questions per reply. No walls of text.
- 1: Decent flow but sometimes too verbose or too terse.
- 0: Encyclopedia dumps. Ignores user's actual question. Unreadably long.

### 5. Handling edge cases and corrections (0-2)
- 2: Gracefully handles wrong info, extreme values, corrections. Adapts to new information. Explains seasonal constraints.
- 1: Handles some edge cases but misses others. Doesn't fully adapt when corrected.
- 0: Ignores corrections. Gives same answer regardless. Doesn't flag out-of-season crops.

## Conversation to evaluate:

{conversation}

## Output format (STRICT — respond with exactly this JSON):
```json
{{
  "asks_before_assuming": {{"score": 0, "reason": "..."}},
  "tool_usage": {{"score": 0, "reason": "..."}},
  "answer_quality": {{"score": 0, "reason": "..."}},
  "conversation_flow": {{"score": 0, "reason": "..."}},
  "edge_case_handling": {{"score": 0, "reason": "..."}},
  "total": 0,
  "summary": "2-3 sentence overall assessment"
}}
```
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def call_chat(messages: list[dict]) -> dict:
    """Call the /chat endpoint with accumulated messages."""
    payload = json.dumps({"messages": messages}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"text": f"[HTTP {e.code}] {body}", "toolEvents": []}
    except Exception as e:
        return {"text": f"[ERROR] {e}", "toolEvents": []}


def call_judge(conversation_text: str) -> dict:
    """Use the same /chat endpoint with a judge system prompt baked into user message."""
    prompt = JUDGE_PROMPT.format(conversation=conversation_text)
    payload = json.dumps({"messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"text": f"[JUDGE ERROR] {e}"}


def format_conversation(turns: list[dict]) -> str:
    """Format the full conversation for the judge."""
    lines = []
    for turn in turns:
        role = turn["role"].upper()
        text = turn.get("text", turn.get("content", ""))
        tools = turn.get("toolEvents", [])
        lines.append(f"### {role}")
        lines.append(text)
        if tools:
            lines.append(f"[Tool events: {len(tools)} — " + ", ".join(f'{t["tool"]}({t["phase"]})' for t in tools) + "]")
        lines.append("")
    return "\n".join(lines)


def parse_judge_score(text: str) -> dict | None:
    """Extract JSON score from judge response."""
    # Try to find JSON block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end]
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end]

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_session(session: dict) -> dict:
    """Run a single multi-turn session and return transcript + scores."""
    print(f"\n{'='*70}")
    print(f"SESSION: {session['name']}")
    print(f"{'='*70}")

    messages: list[dict] = []
    transcript: list[dict] = []

    for i, user_text in enumerate(session["turns"], 1):
        print(f"\n--- Turn {i} ---")
        print(f"USER: {user_text}")

        messages.append({"role": "user", "content": user_text})
        result = call_chat(messages)

        agent_text = result.get("text", "[no response]")
        tool_events = result.get("toolEvents", [])

        print(f"AGENT: {agent_text[:300]}{'...' if len(agent_text) > 300 else ''}")
        if tool_events:
            for t in tool_events:
                print(f"  TOOL: {t['tool']} → {t['phase']}" + (f" ({t.get('detail','')[:80]})" if t.get('detail') else ""))

        messages.append({"role": "assistant", "content": agent_text})

        transcript.append({"role": "user", "content": user_text})
        transcript.append({
            "role": "assistant",
            "text": agent_text,
            "toolEvents": tool_events,
        })

        time.sleep(1)  # rate limiting courtesy

    return {
        "name": session["name"],
        "transcript": transcript,
    }


def judge_session(transcript: list[dict], session_name: str) -> dict | None:
    """Send transcript to judge and parse score."""
    conversation_text = format_conversation(transcript)
    print(f"\n  Judging: {session_name}...")
    result = call_judge(conversation_text)
    judge_text = result.get("text", "")
    score = parse_judge_score(judge_text)

    if score is None:
        print(f"  JUDGE RAW (could not parse JSON):\n{judge_text[:500]}")
        return None

    print(f"  Score: {score.get('total', '?')}/10 — {score.get('summary', '')[:120]}")
    return score


def main():
    print("SOIL CROP ADVISOR — 10-SESSION BENCHMARK")
    print("=" * 70)

    results = []

    for i, session in enumerate(SESSIONS, 1):
        print(f"\n[{i}/10] Running: {session['name']}")
        session_result = run_session(session)

        score = judge_session(session_result["transcript"], session["name"])

        results.append({
            "session_num": i,
            "name": session["name"],
            "score": score,
        })

    # ---------------------------------------------------------------
    # Final report
    # ---------------------------------------------------------------
    print("\n\n")
    print("=" * 70)
    print("BENCHMARK FINAL REPORT")
    print("=" * 70)

    valid_results = [r for r in results if r["score"] is not None]
    total_score = 0

    for r in valid_results:
        s = r["score"]
        subtotal = s.get("total", 0)
        total_score += subtotal
        print(f"\n[{r['session_num']}] {r['name']}")
        print(f"  Total: {subtotal}/10")
        for dim in ["asks_before_assuming", "tool_usage", "answer_quality", "conversation_flow", "edge_case_handling"]:
            d = s.get(dim, {})
            print(f"  - {dim}: {d.get('score', '?')}/2 — {d.get('reason', '')[:80]}")
        print(f"  Summary: {s.get('summary', '')}")

    final = total_score
    max_possible = len(valid_results) * 10
    pct = (final / max_possible * 100) if max_possible else 0

    print(f"\n{'='*70}")
    print(f"FINAL SCORE: {final}/{max_possible} ({pct:.1f}%)")
    print(f"{'='*70}")

    # Save full results to file
    with open("/tmp/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nFull results saved to /tmp/benchmark_results.json")


if __name__ == "__main__":
    main()
