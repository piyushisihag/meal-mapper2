from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
import re

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)
CORS(app)

# ─────────────────────────────────────────
# Load recipes
# ─────────────────────────────────────────
def load_recipes():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "recipes.json")
    with open(path, "r") as f:
        return json.load(f)


# ─────────────────────────────────────────
# Pairings
# ─────────────────────────────────────────
PAIRINGS = {
    "maggi masala": ["Masala Chai", "Cold Coffee", "Lemonade"],
}
DEFAULT_PAIRS = ["Masala Chai", "Lemonade"]


# ─────────────────────────────────────────
# Substitutes
# ─────────────────────────────────────────
SUBSTITUTES = {
    "paneer": "tofu",
    "milk": "coconut milk",
    "butter": "oil"
}


# ─────────────────────────────────────────
# Find recipes
# ─────────────────────────────────────────
def find_recipes(user_ingredients):
    recipes = load_recipes()
    user_ingredients = [i.strip().lower() for i in user_ingredients]

    matched = []
    for recipe in recipes:
        name = recipe.get("recipe_name") or recipe.get("name", "Unknown")
        core = [i.lower() for i in recipe.get("core_ingredients", [])]

        have = [i for i in core if i in user_ingredients]
        missing = [i for i in core if i not in user_ingredients]

        if not core:
            continue

        match_percent = int((len(have) / len(core)) * 100)
        if match_percent < 20:
            continue

        matched.append({
            "name": name,
            "match_percent": match_percent,
            "have": have,
            "missing": missing,
            "pair_with": recipe.get("pairs_with", DEFAULT_PAIRS),
            "steps": recipe.get("steps", [])
        })

    matched.sort(key=lambda x: x["match_percent"], reverse=True)
    return matched


# ─────────────────────────────────────────
# Chat helper
# ─────────────────────────────────────────
def get_chat_reply(message):
    msg = message.lower()
    if "hi" in msg or "hello" in msg:
        return "👋 Hello! Tell me your ingredients 🍽️"
    if "thanks" in msg:
        return "😊 Happy cooking!"
    return "🍳 Ask me about cooking or ingredients!"


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/chat-page")
def chat_page():
    return render_template("chatbot.html")


# ─────────────────────────────────────────
# Suggest
# ─────────────────────────────────────────
@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.get_json()
    ingredients = data.get("ingredients", [])

    results = find_recipes(ingredients)

    return jsonify({
        "recipes": results[:10]
    })


# ─────────────────────────────────────────
# Botpress (MAIN FIXED)
# ─────────────────────────────────────────
@app.route("/botpress", methods=["POST"])
def botpress():
    data = request.get_json()

    message = data.get("message", "")
    ingredients = data.get("ingredients", [])

    if not ingredients and message:
        ingredients = [i.strip().lower() for i in message.split(",") if i.strip()]

    if ingredients:
        results = find_recipes(ingredients)

        if not results:
            return jsonify({"reply": "😕 No recipes found"})

        top3 = results[:3]

        # 🔥 FULL RECIPE FETCH
        all_recipes = load_recipes()

        def get_full_recipe(name):
            for r in all_recipes:
                if r.get("recipe_name", "").lower() == name.lower():
                    return r
            return {}

        top3_full = [get_full_recipe(r["name"]) for r in top3]

        # TEXT
        text = "🍽️ Top Recipes:\n\n"
        for i, r in enumerate(top3, 1):
            text += f"{i}. {r['name']} ({r['match_percent']}%)\n"

        return jsonify({
            "reply": text,

            # 🔥 FULL DATA
            "top_recipes": top3_full,

            # 🔥 NAMES
            "top_recipe_names": [r["name"] for r in top3]
        })

    if message:
        return jsonify({"reply": get_chat_reply(message)})

    return jsonify({"reply": "Send ingredients"})


# ─────────────────────────────────────────
# Steps (FIXED)
# ─────────────────────────────────────────
@app.route("/steps", methods=["POST"])
def steps():
    data = request.get_json()
    recipe_name = data.get("recipe_name", "").lower()

    recipes = load_recipes()

    for recipe in recipes:
        if recipe["recipe_name"].lower() == recipe_name:
            return jsonify({
                "name": recipe["recipe_name"],
                "steps": recipe.get("steps", [])
            })

    return jsonify({"error": "Not found"})


# ─────────────────────────────────────────
# Substitutes
# ─────────────────────────────────────────
@app.route("/substitutes", methods=["POST"])
def substitutes():
    data = request.get_json()
    missing = data.get("missing", [])

    result = []
    for ing in missing:
        sub = SUBSTITUTES.get(ing.lower(), "use similar ingredient")
        result.append(f"{ing} → {sub}")

    return jsonify({"substitutes": result})


# ─────────────────────────────────────────
# Chat
# ─────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "")

    return jsonify({"reply": get_chat_reply(msg)})


# ─────────────────────────────────────────
# Run
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
