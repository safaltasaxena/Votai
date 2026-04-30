# 🏗 AI Election Navigator — Engineering Guidelines

## 🎯 System Type

AI-powered **Guided Civic Assistant**

NOT a chatbot
→ A structured decision-support system

---

# 🧠 1. CORE PRINCIPLE

Always answer:

→ “What should the user do next?”

---

# 🏗 2. SYSTEM ARCHITECTURE

Frontend (React)
→ Backend (FastAPI)
→ Firestore (data)
→ AI Layer (Gemini)

---

## Separation (STRICT)

| Layer       | Responsibility |
| ----------- | -------------- |
| UI          | rendering      |
| Flow Engine | step logic     |
| AI          | explanation    |
| Data        | storage        |

---

# 🗄 3. DATA CONTRACT (IMPORTANT)

AI must ONLY use:

* Firestore data
* API responses

❌ No external assumptions
❌ No hallucinated data

---

# ⚙️ 4. ENGINEERING RULES

* Functions < 50 lines
* Single responsibility
* Clear naming
* Type hints required

---

# 🧠 5. AI INTEGRATION RULES

AI must:

* explain
* simplify
* compare

AI must NOT:

* recommend
* rank
* persuade

---

# 🧠 PROMPT DESIGN

Prompts must include:

* step context
* region_id
* party data
* user intent

---

# 🛡 6. SAFETY

Always include disclaimer for:

* parties
* candidates

---

# 🧪 7. EDGE CASES

Handle:

* moved location
* missed deadline
* missing voter name

Return:

* solution
* next step

---

# 📊 8. UX RULES

Always show:

* current step
* progress
* next action

---

# ⚡ 9. FAILURE HANDLING

If AI fails:

* fallback to structured data
* NEVER return empty response

---

# 🧠 10. DATA INTEGRITY

* Prefer official data
* Avoid assumptions

---

# 🏆 FINAL PRINCIPLE

System must be:

* predictable
* reliable
* understandable

NOT:

* flashy but unstable

---

# 🧠 FINAL MODEL

User State + Flow + Data + AI
→ Clear Guidance → Confident User
