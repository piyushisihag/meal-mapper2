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
#  Load recipes from JSON file
# ─────────────────────────────────────────
def load_recipes():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "pro_dataset.json")
    with open(path, "r") as f:
        return json.load(f)


# ─────────────────────────────────────────
#  Pairings map
# ─────────────────────────────────────────
PAIRINGS = {
    "maggi masala":       ["Masala Chai", "Cold Coffee", "Lemonade"],
    "masala chai":        ["Butter Toast", "Bread Pakora", "Biscuits"],
    "omelette":           ["Butter Toast", "Masala Chai", "Orange Juice"],
    "dal tadka":          ["Jeera Rice", "Naan", "Raita"],
    "pasta arrabbiata":   ["Garlic Bread", "Lemonade", "Tomato Soup"],
    "aloo paratha":       ["Raita", "Masala Chai", "Green Chutney"],
    "poha":               ["Masala Chai", "Banana Milkshake"],
    "upma":               ["Masala Chai", "Coconut Chutney"],
    "bread pakora":       ["Green Chutney", "Masala Chai"],
    "vada pav":           ["Masala Chai", "Tamarind Chutney"],
    "egg fried rice":     ["Manchurian", "Spring Roll", "Cold Coffee"],
    "chow mein":          ["Manchurian", "Lemonade"],
    "veg burger":         ["French Fries", "Cold Coffee", "Lemonade"],
    "pizza":              ["Garlic Bread", "Cold Coffee", "Tomato Soup"],
    "samosa":             ["Green Chutney", "Masala Chai", "Tamarind Chutney"],
    "pav bhaji":          ["Masala Chai", "Lemonade"],
    "chole bhature":      ["Masala Chai", "Lassi"],
    "rajma chawal":       ["Raita", "Papad", "Masala Chai"],
    "garlic bread":       ["Tomato Soup", "Cold Coffee"],
    "french fries":       ["Ketchup", "Cold Coffee", "Lemonade"],
    "cheese sandwich":    ["Masala Chai", "Cold Coffee"],
    "idli sambar":        ["Coconut Chutney", "Masala Chai"],
    "masala dosa":        ["Sambar", "Coconut Chutney", "Masala Chai"],
    "tomato soup":        ["Garlic Bread", "Butter Toast"],
    "aloo chaat":         ["Masala Chai", "Lemonade"],
    "bhel puri":          ["Masala Chai", "Lemonade"],
    "butter chicken":     ["Naan", "Jeera Rice", "Lassi"],
    "chicken biryani":    ["Raita", "Masala Chai", "Lemonade"],
}

DEFAULT_PAIRS = ["Masala Chai", "Lemonade"]


# ─────────────────────────────────────────
#  Substitutes map (no API needed)
# ─────────────────────────────────────────
SUBSTITUTES = {
    "paneer":         "tofu or crumbled cottage cheese",
    "cream":          "full-fat milk or coconut milk",
    "butter":         "ghee or any cooking oil",
    "ghee":           "butter or coconut oil",
    "yogurt":         "hung curd or thick buttermilk",
    "egg":            "1 tbsp flaxseed in 3 tbsp water (flax egg)",
    "milk":           "coconut milk or oat milk",
    "olive oil":      "any vegetable or sunflower oil",
    "parmesan":       "any hard cheese or skip",
    "basil":          "fresh coriander or dried Italian herbs",
    "parsley":        "coriander leaves",
    "oregano":        "mixed Italian herbs or dried basil",
    "saffron":        "a pinch of turmeric for colour",
    "coconut milk":   "full-fat milk with a pinch of coconut powder",
    "tamarind":       "lemon juice with a pinch of sugar",
    "green chilli":   "red chilli powder or black pepper",
    "ginger":         "ginger powder (half the amount)",
    "garlic":         "garlic powder or asafoetida (hing)",
    "cashew":         "almonds or skip",
    "khoya":          "condensed milk or dried milk powder",
    "jaggery":        "brown sugar or regular sugar",
    "besan":          "rice flour or all-purpose flour",
    "semolina":       "fine rice flour or vermicelli",
    "urad dal":       "moong dal",
    "kidney beans":   "black chana or rajma from can",
    "chickpeas":      "white beans or black chana",
    "bread":          "roti or any flatbread",
    "pasta":          "any noodles or spaghetti",
    "noodles":        "thin spaghetti or vermicelli",
    "cheese":         "paneer or skip",
    "spring onion":   "regular onion greens",
    "capsicum":       "zucchini or carrot strips",
    "potato":         "sweet potato or raw banana",
    "tomato":         "tomato puree (half amount) or tamarind",
}


# ─────────────────────────────────────────
#  Helper: find matching recipes
#  Matching rules:
#    - match_percent based ONLY on core_ingredients
#    - basic_ingredients and optional_ingredients shown as have/missing
#    - Recipes with 0 core matches but some optional/basic match → 5% priority
#    - Sort: match_percent desc, then optional matches desc
# ─────────────────────────────────────────
def find_recipes(user_ingredients):
    recipes = load_recipes()
    user_ingredients = [i.strip().lower() for i in user_ingredients]

    matched = []
    for recipe in recipes:
        # ── Support both pro_dataset (recipe_name) and legacy (name) format ──
        name = recipe.get("recipe_name") or recipe.get("name", "Unknown")

        core = [i.lower() for i in recipe.get("core_ingredients", [])]
        basic = [i.lower() for i in recipe.get("basic_ingredients", [])]
        optional = [i.lower() for i in recipe.get("optional_ingredients", [])]

        # Fallback for old flat format
        if not core and not basic and not optional:
            core = [i.lower() for i in recipe.get("ingredients", [])]

        # ── Core matching (drives match_percent) ──
        core_have = [i for i in core if i in user_ingredients]
        core_missing = [i for i in core if i not in user_ingredients]

        # ── Basic and optional matching (display only) ──
        basic_have = [i for i in basic if i in user_ingredients]
        basic_missing = [i for i in basic if i not in user_ingredients]
        optional_have = [i for i in optional if i in user_ingredients]
        optional_missing = [i for i in optional if i not in user_ingredients]

        # ── Calculate match_percent from core only ──
        if core:
            match_percent = int((len(core_have) / len(core)) * 100)
        else:
            match_percent = 0

        # ── Skip recipes with nothing in common at all ──
        total_have = core_have + basic_have + optional_have
        if not total_have:
            continue

        # ── Recipes with no core match but some optional/basic match → low priority ──
        if match_percent == 0:
            if optional_have or basic_have:
                match_percent = 5
            else:
                continue

        # ── Build combined have/missing lists for output ──
        have = core_have + basic_have + optional_have
        missing = core_missing + basic_missing + optional_missing

        # ── pairs_with: use dataset value, fallback to PAIRINGS map, then DEFAULT_PAIRS ──
        dataset_pairs = recipe.get("pairs_with", [])
        pair_with = dataset_pairs if dataset_pairs else PAIRINGS.get(name.lower(), DEFAULT_PAIRS)

        matched.append({
            "name": name,
            "match_percent": match_percent,
            "have": have,
            "missing": missing,
            "suggestions": recipe.get("suggestions", []),
            "cuisine": recipe.get("cuisine", ""),
            "type": recipe.get("type", []),
            "preparation_time": recipe.get("preparation_time", ""),
            "difficulty_level": recipe.get("difficulty_level", ""),
            "tags": recipe.get("tags", []),
            "pair_with": pair_with,
            "_optional_have_count": len(optional_have)  # used for secondary sort
        })

    # ── Sort: match_percent desc, then optional matches desc ──
    matched.sort(key=lambda x: (x["match_percent"], x["_optional_have_count"]), reverse=True)

    # ── Clean up internal sort key before returning ──
    for r in matched:
        r.pop("_optional_have_count", None)

    return matched


# ─────────────────────────────────────────
#  Helper: get substitutes without API
# ─────────────────────────────────────────
def get_substitutes_local(missing_ingredients, recipe_name):
    lines = []
    for ing in missing_ingredients:
        ing_lower = ing.strip().lower()
        sub = SUBSTITUTES.get(ing_lower)
        if sub:
            lines.append(f"🔄 {ing} → {sub}")
        else:
            lines.append(f"🔄 {ing} → try skipping it or use whatever is closest")
    if lines:
        tip = "💡 Tip: Indian kitchens are creative — adjust spices to taste!"
        return "\n".join(lines) + "\n\n" + tip
    return "✅ No substitutes needed — you have everything!"


# ─────────────────────────────────────────
#  Helper: simple chat answers (no API)
# ─────────────────────────────────────────
CHAT_ANSWERS = {
    r"how long.*(cook|boil|fry|bake|steam)":
        "⏱️ Most stovetop dishes take 10–30 minutes. Baking usually needs 15–45 minutes. When in doubt, cook on medium flame and keep checking!",
    r"substitute|replace|don.t have|dont have|no (.+)":
        "🔄 Use the /substitutes endpoint with your missing ingredients for exact suggestions!",
    r"how (much|many) (salt|sugar|spice|oil|water)":
        "🧂 Start small — add salt and spices in small amounts, taste and adjust. You can always add more but can't take it out!",
    r"(burn|burnt|overcooked)":
        "🔥 If something burns, lower the heat immediately. Add a splash of water and stir. Prevention: always cook on medium flame and stir regularly.",
    r"(raw|undercooked|not cooked)":
        "♨️ Cover the pan and cook on low flame for a few more minutes. Add a tiny splash of water to create steam and help it cook through.",
    r"(too spicy|very spicy|reduce spice)":
        "🌶️ Add a dollop of yogurt, a squeeze of lemon, or a bit of sugar to balance the spice. Dairy always helps cool down heat!",
    r"(too salty|very salty|reduce salt)":
        "🧂 Add a raw potato to absorb salt, or dilute with more water/ingredient. A squeeze of lemon can also help balance saltiness.",
    r"(store|storage|how long.*fridge|refrigerate)":
        "🧊 Most cooked Indian dishes last 2–3 days in the fridge. Always store in airtight containers. Reheat properly before eating.",
    r"(vegan|no dairy|no milk|no egg|plant.based)":
        "🌱 Replace dairy with coconut milk, oat milk or soy milk. Replace egg with flaxseed egg (1 tbsp flax + 3 tbsp water). Most Indian sabzis are naturally vegan!",
    r"(hello|hi|hey|helo|hii)":
        "👋 Hello! I'm your Meal Mapper kitchen assistant. Tell me what ingredients you have and I'll find recipes for you! 🍽️",
    r"(thank|thanks|thank you|thx)":
        "😊 You're welcome! Happy cooking! 🍳",
    r"(help|what can you do|features)":
        "🗺️ I can: 1) Find recipes from your ingredients 2) Give step-by-step instructions 3) Suggest what goes well with your dish 4) Find substitutes for missing items. Just tell me what's in your kitchen!",
}


def get_chat_reply(message):
    msg = message.lower().strip()
    for pattern, reply in CHAT_ANSWERS.items():
        if re.search(pattern, msg):
            return reply
    return "🍳 Great question! For the best results, try listing your ingredients and I'll find matching recipes. Or ask about a specific cooking problem like 'too spicy' or 'how long to cook'!"


# ─────────────────────────────────────────
#  Route 1 - health check
# ─────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "🗺️ Meal Mapper API is running!", "status": "ok"})


# ─────────────────────────────────────────
#  Route 2 - get recipe suggestions
# ─────────────────────────────────────────
@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.get_json()
    if not data or "ingredients" not in data:
        return jsonify({"error": "Please send ingredients in the request body."}), 400

    ingredients = data["ingredients"]
    if not isinstance(ingredients, list) or len(ingredients) == 0:
        return jsonify({"error": "ingredients must be a non-empty list."}), 400

    results = find_recipes(ingredients)
    if not results:
        return jsonify({
            "message": "Sorry, no recipes found with those ingredients. Try adding more common ingredients like onion, tomato, or salt.",
            "recipes": []
        })

    return jsonify({
        "message": f"Found {len(results)} recipe(s) for you!",
        "recipes": results[:10]  # return top 10
    })


# ─────────────────────────────────────────
#  Route 3 - Botpress webhook (main entry)
#  Botpress sends: { "message": "...", "ingredients": [...] }
# ─────────────────────────────────────────
@app.route("/botpress", methods=["POST"])
def botpress():
    data = request.get_json()
    if not data:
        return jsonify({"reply": "Sorry, I didn't understand that. Please try again!"}), 400

    message = data.get("message", "").strip()
    ingredients = data.get("ingredients", [])

    # If ingredients provided, find recipes
    if ingredients and isinstance(ingredients, list) and len(ingredients) > 0:
        results = find_recipes(ingredients)
        if not results:
            return jsonify({
                "reply": "😕 I couldn't find any recipes with those ingredients. Try adding more common items like onion, tomato, or rice!",
                "recipes": []
            })

        # Top 3 above 20% match
        top3 = results[:3]
        recipe_text = f"🍽️ Top {len(top3)} recipe(s) for you!\n"
        recipe_text += "─" * 30 + "\n\n"

        for idx, recipe in enumerate(top3, 1):
            recipe_text += f"#{idx} *{recipe['name']}* — {recipe['match_percent']}% match\n"
            if recipe.get("cuisine"):
                recipe_text += f"🌍 Cuisine: {recipe['cuisine']} | ⏱️ {recipe.get('preparation_time', '')} | 🎯 {recipe.get('difficulty_level', '')}\n"
            recipe_text += f"✅ Have: {', '.join(recipe['have'])}\n"
            if recipe["missing"]:
                recipe_text += f"❌ Missing: {', '.join(recipe['missing'])}\n"
            if recipe.get("suggestions"):
                recipe_text += "💡 Tips:\n"
                for tip in recipe["suggestions"]:
                    recipe_text += f"  • {tip}\n"
            recipe_text += f"🍵 Pairs with: {', '.join(recipe['pair_with'])}\n"
            recipe_text += "\n"

        return jsonify({
            "reply": recipe_text,
            "top_recipes": [r["name"] for r in top3],
            "all_recipes": [r["name"] for r in results[:10]],
            "pair_with": top3[0]["pair_with"]
        })

    # If just a chat message
    if message:
        reply = get_chat_reply(message)
        return jsonify({"reply": reply})

    return jsonify({"reply": "👋 Hi! Tell me what ingredients you have and I'll find recipes for you!"}), 200


# ─────────────────────────────────────────
#  Route 4 - get recipe details by name
# ─────────────────────────────────────────
@app.route("/steps", methods=["POST"])
def steps():
    data = request.get_json()
    if not data or "recipe_name" not in data:
        return jsonify({"error": "Please send recipe_name in the request body."}), 400

    recipe_name = data["recipe_name"].strip().lower()
    recipes = load_recipes()

    for recipe in recipes:
        name = recipe.get("recipe_name") or recipe.get("name", "")
        if name.lower() == recipe_name:
            dataset_pairs = recipe.get("pairs_with", [])
            pair_with = dataset_pairs if dataset_pairs else PAIRINGS.get(recipe_name, DEFAULT_PAIRS)
            return jsonify({
                "name": name,
                "cuisine": recipe.get("cuisine", ""),
                "type": recipe.get("type", []),
                "preparation_time": recipe.get("preparation_time", ""),
                "difficulty_level": recipe.get("difficulty_level", ""),
                "tags": recipe.get("tags", []),
                "suggestions": recipe.get("suggestions", []),
                "pair_with": pair_with
            })

    return jsonify({"error": f"Recipe '{data['recipe_name']}' not found."}), 404


# ─────────────────────────────────────────
#  Route 5 - get substitutes (no API!)
# ─────────────────────────────────────────
@app.route("/substitutes", methods=["POST"])
def substitutes():
    data = request.get_json()
    missing_ingredients = data.get("missing", [])
    recipe_name = data.get("recipe_name", "this recipe")

    if not missing_ingredients:
        return jsonify({"substitutes": "✅ You have all ingredients needed!"})

    result = get_substitutes_local(missing_ingredients, recipe_name)
    return jsonify({"substitutes": result})


# ─────────────────────────────────────────
#  Route 6 - simple chat (no API!)
# ─────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"reply": "Please ask a cooking question! 🍳"})

    reply = get_chat_reply(user_message)
    return jsonify({"reply": reply})


# ─────────────────────────────────────────
#  Route 7 - add new recipe
# ─────────────────────────────────────────
@app.route("/add_recipe", methods=["POST"])
def add_recipe():
    data = request.get_json()
    required = ["name", "core_ingredients"]
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Please send at least: name and core_ingredients."}), 400

    new_recipe = {
        "recipe_name": data["name"].strip(),
        "type": data.get("type", ["Meal"]),
        "cuisine": data.get("cuisine", ""),
        "core_ingredients": [i.strip().lower() for i in data["core_ingredients"]],
        "basic_ingredients": [i.strip().lower() for i in data.get("basic_ingredients", [])],
        "optional_ingredients": [i.strip().lower() for i in data.get("optional_ingredients", [])],
        "preparation_time": data.get("preparation_time", ""),
        "difficulty_level": data.get("difficulty_level", ""),
        "source": "User Added",
        "pairs_with": data.get("pairs_with", []),
        "tags": data.get("tags", ["general"]),
        "suggestions": data.get("suggestions", []),
        "suggestion_type": "Max"
    }

    recipes = load_recipes()
    for r in recipes:
        existing_name = r.get("recipe_name") or r.get("name", "")
        if existing_name.lower() == new_recipe["recipe_name"].lower():
            return jsonify({"error": "Recipe already exists!"}), 409

    recipes.append(new_recipe)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, "pro_dataset.json"), "w") as f:
        json.dump(recipes, f, indent=2)

    return jsonify({"message": f"Recipe '{new_recipe['recipe_name']}' added successfully!"}), 201


# ─────────────────────────────────────────
#  Run the app
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
