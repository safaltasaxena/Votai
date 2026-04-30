# 🏗 AI Election Navigator — System Architecture & Engineering Standards

## 🎯 Project Archetype

> AI-powered **Guided Civic Assistant** that transforms a complex election process into a structured, step-by-step, user-centric journey.

---

# 🧠 1. System Philosophy

* Build a **guidance system**, not a generic chatbot

* Prioritize:

  * clarity over cleverness
  * reliability over complexity
  * structure over randomness

* Every feature must answer:
  → “What should the user do next?”

---

# 📂 2. Context Awareness Rule

Before implementing any feature:

* Understand:

  * user journey (eligibility → voting)
  * current step in flow
  * required output format

* Always align logic with:

  * step-based navigation
  * neutrality constraints
  * structured outputs

---

# 🏗 3. Architecture Overview

### System Flow:

Frontend (React / UI)
→ Backend API (Python preferred)
→ Firestore (state + data)
→ AI Layer (LLM for explanation)

---

## Separation of Concerns (STRICT)

* **UI Layer**

  * rendering
  * user interaction

* **Flow Engine**

  * step logic
  * navigation

* **AI Layer**

  * explanation
  * summarization

* **Data Layer**

  * election data
  * user state

---

# 🗄 4. Firestore Data Design

### Collections:

#### users

* id
* age
* location
* first_time_voter

---

#### progress

* user_id
* current_step
* completed_steps

---

#### elections

* region
* deadlines
* steps

---

#### parties

* name
* focus
* policies
* past_work

---

# ⚙️ 5. Engineering Standards (CRITICAL)

## 🧩 Code Quality Rules

* ❌ No “God functions”
  → Keep functions **< 40–50 lines**

* ✅ Use modular design
  → One function = one responsibility

* ✅ Use clear naming
  → `get_user_progress()` > `func1()`

* ✅ Use type hints (Python)

```python
def get_user_progress(user_id: str) -> dict:
```

---

## 🧠 Readability First

* Code must be:

  * easy to read
  * easy to debug
  * easy to extend

* Prefer:

  * simple logic
  * explicit steps

---

## 💬 Comments & Documentation

* Add comments for:

  * complex logic
  * flow decisions

Example:

```python
# Determine next step based on completed steps
```

* Avoid:

  * obvious comments
  * redundant explanations

---

## 🧪 Testing

* Test:

  * flow logic
  * step transitions
  * edge cases

* Use:

  * pytest (if Python)

---

# 🧠 6. AI Integration Standards

## AI Responsibilities

* Explanation
* Simplification
* Summarization
* Comparison

---

## AI Restrictions

* ❌ No political bias
* ❌ No recommendations
* ❌ No hallucinated facts

---

## Prompt Discipline

* Keep prompts:

  * structured
  * reusable
  * context-aware

---

# 🛡 7. Safety & Neutrality Enforcement

* Always:

  * include disclaimers for party info
  * avoid persuasive language

---

# 🧪 8. Edge Case Handling

Must explicitly handle:

* user moved location
* missed registration
* name missing in list

---

## Rule:

Always provide:

* next step
* fallback solution

---

# 📊 9. UX Engineering Rules

* Always show:

  * current step
  * next step
  * progress

---

## UI must be:

* minimal
* intuitive
* fast

---

# 🔔 10. Engagement & Feedback

* Include:

  * progress indicators
  * completion states
  * feedback prompts

---

# 🌍 11. Localization Strategy

* Phase 1:

  * country-level

* Phase 2:

  * region-level

---

# 🧠 12. Data Integrity Rules

* Prefer:

  * official sources

* Avoid:

  * assumptions
  * unverified claims

---

# ⚡ 13. Development Workflow

## Step 1: MVP

* guided flow
* explanation engine
* timeline

---

## Step 2: Enhancement

* personalization
* comparison feature
* edge cases

---

## Step 3: Polish

* UI improvements
* engagement features
* trust layer

---

# 🏆 Final Engineering Principle

> Build a system that is:

* predictable
* understandable
* trustworthy

NOT:

* flashy but unreliable

---

# 🧠 Final Mental Model

User State + Flow Logic + AI Explanation
→ Clear Guidance → Confident Action
