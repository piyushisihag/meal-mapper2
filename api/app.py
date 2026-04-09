from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────
# Load recipes
# ─────────────────────────────────────────
def load_recipes():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "pro_dataset.json")
    with open(path, "r") as f:
        return json.load(f)

# ─────────────────────────────────────────
# Pairings
# ─────────────────────────────────────────
DEFAULT_PAIRS = ["Masala Chai", "Lemonade"]

# ─────────────────────────────────────────
# Find recipes (SMART ENGINE)
# ─────────────────────────────────────────
def find_recipes(user_ingredients):
    recipes = load_recipes()
    user_ingredients = [i.strip().lower() for i in user_ingredients]

    matched = []

    for recipe in recipes:
        name = recipe.get("recipe_name") or recipe.get("name", "Unknown")

        core = [i.lower() for i in recipe.get("core_ingredients", [])]
        optional = [i.lower() for i in recipe.get("optional_ingredients", [])]

        if not core:
            continue

        core_have = [i for i in core if i in user_ingredients]
        core_missing = [i for i in core if i not in user_ingredients]
        optional_missing = [i for i in optional if i not in user_ingredients]

        # 🎯 Match %
        match_percent = int((len(core_have) / len(core)) * 100)

        # 🚫 Filter weak
        if match_percent < 20:
            continue

        # ⚡ Smart tag
        one_away = len(core_missing) == 1

        matched.append({
            "name": name,
            "match_percent": match_percent,
            "core_have": core_have,
            "core_missing": core_missing,
            "optional_missing": optional_missing,
            "one_away": one_away,

            "cuisine": recipe.get("cuisine") or "Indian",
            "preparation_time": recipe.get("preparation_time") or "10-20 minutes",
            "difficulty_level": recipe.get("difficulty_level") or "Easy",
            "suggestions": recipe.get("suggestions") or [
                "Adjust spices to your taste",
                "Serve fresh for best flavor"
            ],

            "pair_with": recipe.get("pairs_with") or DEFAULT_PAIRS
        })

    # 🧠 Smart sorting
    matched.sort(key=lambda x: (
        x["match_percent"],
        -len(x["core_missing"])  # fewer missing = better
    ), reverse=True)

    return matched

# ─────────────────────────────────────────
# Botpress API (PREMIUM OUTPUT)
# ─────────────────────────────────────────
@app.route("/botpress", methods=["POST"])
def botpress():
    data = request.get_json()
    ingredients = data.get("ingredients", [])

    results = find_recipes(ingredients)

    if not results:
        return jsonify({
            "reply": "😕 No strong matches found. Try adding 1–2 more ingredients!"
        })

    top3 = results[:3]

    text = "🍽️ *Top Recipes Just For You*\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, r in enumerate(top3):
        # ⭐ Highlight best
        if i == 0:
            text += "🔥 *BEST MATCH*\n"

        text += f"{medals[i]} *{r['name']}* — {r['match_percent']}%\n"
        text += f"🌍 {r['cuisine']} | ⏱️ {r['preparation_time']} | 🎯 {r['difficulty_level']}\n\n"

        # ⚡ Smart message
        if r["one_away"]:
            text += "⚡ You are just *1 ingredient away!*\n\n"

        text += f"✅ Core: {', '.join(r['core_have']) or '—'}\n"

        if r["core_missing"]:
            text += f"❌ Missing: {', '.join(r['core_missing'])}\n"
        else:
            text += "🎉 Ready to cook!\n"

        if r["optional_missing"]:
            text += f"✨ Upgrade with: {', '.join(r['optional_missing'])}\n"

        text += "\n💡 Pro Tips:\n"
        for tip in r["suggestions"][:2]:
            text += f"  • {tip}\n"

        text += f"\n🍵 Best with: {', '.join(r['pair_with'])}\n"
        text += "\n──────────────────────────────\n\n"

    return jsonify({"reply": text})

# ─────────────────────────────────────────
# Run
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
