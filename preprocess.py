"""
============================================
 MEAL MAPPER — preprocess.py
 Converts raw_recipes.csv → recipes.json
 Run: python preprocess.py
============================================
"""

import pandas as pd
import json
import re
import os

# ── CONFIG ───────────────────────────────
INPUT_FILE  = "raw_recipes.csv"   # your CSV file
OUTPUT_FILE = "recipes.json"      # output for Flask
MAX_RECIPES = 300                 # how many to keep
# ─────────────────────────────────────────


def clean_text(text):
    """Remove extra spaces and weird characters."""
    if pd.isna(text):
        return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def parse_ingredients(raw):
    """Convert pipe-separated or comma-separated ingredients into a list."""
    if pd.isna(raw):
        return []
    raw = str(raw).strip()

    # Try pipe separator first (our CSV uses this)
    if "|" in raw:
        items = raw.split("|")
    elif "," in raw:
        items = raw.split(",")
    elif "\n" in raw:
        items = raw.split("\n")
    else:
        items = [raw]

    # Clean each ingredient
    cleaned = []
    for item in items:
        item = item.strip().lower()
        # Remove quantities like "2 cups", "1 tbsp"
        item = re.sub(r'^\d+[\d/\s]*\s*(cup|tbsp|tsp|oz|lb|g|kg|ml|l|pinch|piece|clove|slice)s?\s*(of\s*)?', '', item)
        item = item.strip()
        if item and len(item) > 1:
            cleaned.append(item)

    return cleaned


def parse_steps(raw):
    """Convert step string into a list of steps."""
    if pd.isna(raw):
        return []
    raw = str(raw).strip()

    # Split by period followed by capital letter
    steps = re.split(r'(?<=[.!?])\s+(?=[A-Z])', raw)
    steps = [s.strip() for s in steps if len(s.strip()) > 5]

    if not steps:
        return [raw]
    return steps


def remove_duplicates(recipes):
    """Remove recipes with duplicate names."""
    seen = set()
    unique = []
    for r in recipes:
        key = r['name'].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def standardise_ingredients(ingredients):
    """Standardise common ingredient names."""
    replacements = {
        "eggs":              "egg",
        "tomatoes":          "tomato",
        "potatoes":          "potato",
        "onions":            "onion",
        "olive oil":         "oil",
        "vegetable oil":     "oil",
        "kosher salt":       "salt",
        "sea salt":          "salt",
        "black pepper":      "pepper",
        "all purpose flour": "flour",
        "all-purpose flour": "flour",
        "green onion":       "spring onion",
        "scallion":          "spring onion",
    }
    result = []
    for ing in ingredients:
        ing = replacements.get(ing, ing)
        if ing not in result:
            result.append(ing)
    return result


# ── MAIN ─────────────────────────────────

print("=" * 45)
print("  MEAL MAPPER — Preprocessor")
print("=" * 45)

# 1. Check file exists
if not os.path.exists(INPUT_FILE):
    print(f"ERROR: File not found: {INPUT_FILE}")
    print("Make sure raw_recipes.csv is in this folder.")
    exit(1)

# 2. Load CSV
print(f"\nLoading: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)
print(f"Loaded {len(df)} rows")
print(f"Columns: {list(df.columns)}")

# 3. Process each row
print(f"\nProcessing...")
recipes = []

for _, row in df.iterrows():
    name        = clean_text(row.get("recipe_name", row.get("name", "")))
    ingredients = parse_ingredients(row.get("ingredients", ""))
    steps       = parse_steps(row.get("steps", row.get("instructions", "")))

    # Skip if no name or less than 2 ingredients
    if not name or len(ingredients) < 2:
        continue

    ingredients = standardise_ingredients(ingredients)

    recipes.append({
        "name":        name,
        "ingredients": ingredients,
        "steps":       steps
    })

print(f"Valid recipes: {len(recipes)}")

# 4. Remove duplicates
before = len(recipes)
recipes = remove_duplicates(recipes)
print(f"Removed {before - len(recipes)} duplicates")

# 5. Limit to MAX_RECIPES
if len(recipes) > MAX_RECIPES:
    recipes = recipes[:MAX_RECIPES]
    print(f"Trimmed to {MAX_RECIPES} recipes")

# 6. Save to JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(recipes, f, indent=2, ensure_ascii=False)

print(f"\nSaved to: {OUTPUT_FILE}")

# 7. Show sample
print(f"\nSample (first 3 recipes):")
print("-" * 40)
for r in recipes[:3]:
    print(f"Name        : {r['name']}")
    print(f"Ingredients : {r['ingredients']}")
    print(f"Steps       : {len(r['steps'])} steps")
    print()

print("=" * 45)
print("Done! recipes.json is ready for Flask.")
print("=" * 45)
