import spacy
from spacy.matcher import Matcher
from typing import Dict

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

# Define SQL patterns
patterns = {
    "SELECT": [
        {"LOWER": {"IN": ["select", "get", "find", "fetch"]}}, 
        {"POS": "NOUN", "OP": "+"}
    ],
    "SELECT_MULTIPLE": [
        {"POS": "NOUN", "OP": "+"},
        {"LOWER": {"IN": [",", "and"]}, "OP": "?"},
        {"POS": "NOUN", "OP": "+"}
    ],
    "WHERE": [
        {"LOWER": {"IN": ["where", "made"]}}, 
        {"POS": "NOUN", "OP": "+"}, 
        {"LOWER": {"IN": ["by", "is", "="]}}, 
        {"POS": {"IN": ["PROPN", "NOUN", "NUM"]}}
    ],
    "WHERE_YEAR": [
        {"LOWER": {"IN": ["manufactured", "in", "made", "where"]}}, 
        {"LOWER": {"IN": ["year"]}, "OP": "?"}, 
        {"POS": "NUM"}
    ],
    "AGGREGATE": [
        {"LOWER": {"IN": ["total", "sum", "average", "avg", "count", "minimum", "min", "maximum", "max"]}}, 
        {"POS": "NOUN", "OP": "+"}
    ],
    "COUNT": [
        {"LOWER": {"IN": ["count", "number"]}}, 
        {"LOWER": {"IN": ["of"]}, "OP": "?"}, 
        {"POS": "NOUN", "OP": "+"}
    ],
    "ORDER_BY": [
        {"LOWER": {"IN": ["order"]}},
        {"LOWER": "by"},
        {"POS": "NOUN"},
        {"LOWER": {"IN": ["ascending", "descending", "asc", "desc"]}, "OP": "?"}
    ],
    "SORT": [
        {"LOWER": "sort"},
        {"POS": "NOUN", "OP": "+"},
        {"LOWER": "by"},
        {"POS": "NOUN"},
        {"LOWER": {"IN": ["ascending", "descending", "asc", "desc"]}, "OP": "?"}
    ],
     "GROUP_BY": [
        {"LOWER": {"IN": ["group"]}},
        {"LOWER": "by"},
        {"POS": "NOUN", "OP": "+"},
        {"LOWER": "and", "OP": "?"},
        {"POS": "NOUN", "OP": "*"}
    ],
    "HAVING": [
        {"LOWER": "having"},
        {"POS": "NOUN", "OP": "+"},  # Column name or aggregate function
        {"LOWER": {"IN": [">", "<", "=", ">=", "<="]}},  # Comparison operator
        {"POS": {"IN": ["NUM", "NOUN"]}}  # Value
    ]
}

# Add patterns to the matcher
for intent, pattern in patterns.items():
    matcher.add(intent, [pattern])

# Define column mappings
column_mappings = {
    "make": "make",
    "model": "model",
    "year": "year",
    "condition": "condition",
    "mileage": "mileage",
    "price": "price",  # Added price column
    "vehicles": None,
    "cars": None,
    "details": None,  # Generic terms to be ignored
}

# Helper function to map column names, excluding action words
def map_to_column(text: str) -> str:
    if text.lower() in ["select", "get", "find", "fetch", "count", "number", "of", "and", ",", "order", "sort", "by", "ascending", "descending", "asc", "desc"]:
        return None
    return column_mappings.get(text.lower(), text)

# Parse and generate SQL query
def parse_and_generate_sql(user_query: str) -> str:
    doc = nlp(user_query)
    matches = matcher(doc)

    # Initialize query parts
    query_parts = {
        "SELECT": [],
        "WHERE": [],
        "ORDER_BY": ""
    }

    # Track aggregation function and count-specific logic
    aggregation = None
    is_count_query = False

    # Process matches
    for match_id, start, end in matches:
        intent = nlp.vocab.strings[match_id]
        span = doc[start:end]

        if intent == "SELECT" or intent == "SELECT_MULTIPLE":
            for token in span:
                column = map_to_column(token.text)
                if column and column not in query_parts["SELECT"]:
                    query_parts["SELECT"].append(column)

        elif intent == "WHERE":
            tokens = [token.text.lower() for token in span]
            if len(tokens) >= 4:
                column = map_to_column(tokens[1])
                operator = "=" if tokens[2] in ["by", "is", "="] else tokens[2]
                value = tokens[3].capitalize() if tokens[3].isalpha() else tokens[3]
                if column:
                    condition = f"{column} {operator} '{value}'" if operator == "=" else f"{column} {operator} {value}"
                    query_parts["WHERE"].append(condition)

        elif intent == "WHERE_YEAR":
            tokens = [token.text.lower() for token in span]
            if len(tokens) >= 2:
                column = "year"
                operator = "="
                value = tokens[-1]
                condition = f"{column} {operator} {value}"
                query_parts["WHERE"].append(condition)

        elif intent == "AGGREGATE":
            tokens = [token.text.lower() for token in span]
            if len(tokens) >= 2:
                agg_func = tokens[0].upper()
                column = map_to_column(tokens[1])
                if column:
                    aggregation = f"{agg_func}({column})"

        elif intent == "COUNT":
            is_count_query = True
            aggregation = "COUNT(*)"

        elif intent == "ORDER_BY" or intent == "SORT":
            tokens = [token.text.lower() for token in span]
            if len(tokens) >= 3:
                column = map_to_column(tokens[-2] if len(tokens) > 3 else tokens[-1])
                if column:
                    direction = "ASC" if tokens[-1] in ["ascending", "asc"] else "DESC"
                    query_parts["ORDER_BY"] = f"{column} {direction}"

    if "car" in user_query.lower() or "cars" in user_query.lower() or "vehicle" in user_query.lower() or "vehicles" in user_query.lower():
        for token in doc:
            if token.text.lower() == "made" and token.nbor(1).text.lower() == "by":
                make_value = token.nbor(2).text.capitalize()
                query_parts["WHERE"].append(f"make = '{make_value}'")

    if aggregation:
        select_clause = aggregation
    elif query_parts["SELECT"]:
        select_clause = ", ".join(query_parts["SELECT"])
    else:
        select_clause = "*"

    where_clause = " AND ".join(query_parts["WHERE"])

    sql = f"SELECT {select_clause} FROM vehicles"
    if where_clause:
        sql += f" WHERE {where_clause}"
    if query_parts["ORDER_BY"]:
        sql += f" ORDER BY {query_parts['ORDER_BY']}"

    return sql

# Test the function with various inputs
# test_queries = [
#     "get price from vehicles which is order by price",
#     "find all details of cars made by toyota where year is 2020 order by price descending",
#     "sort car by price ascending",
#     "get cars made by Honda order by model descending",
#     "sort vehicles by price ascending",
#     "fetch model of car made by toyota",
#     "fetch mileage of vehicle where year is 2022",
#      "count the number of cars made by Toyota",
#     "find year, condition, mileage and model of cars made by toyota where year is 2020",
#     "find the condition of vehicles where year is 2022",
#     "get condition of cars made by Toyota where year = 2019",
#     "find the total mileage of cars made by toyota",
#     "get the average condition of vehicles made by honda where year is 2020",
#     "count the number of vehicles when year is 2021",
#      "find year, condition, mileage and model of cars made by toyota where year is 2020",
#     "find condition of vehicles where year is 2022",
#     "get condition of cars made by Toyota where year = 2019",
#     "find the total mileage of cars made by toyota",
#     "get the average condition of vehicles made by honda where year is 2020",
#     "count the number of cars made by Toyota",
#     "find the maximum price of vehicles made by Toyota",
#     "get the average price of cars where year is 2021",
#     "find the total price of vehicles where year is 2020",
#     "find the price, model of cars made by Ford",
#     "find the maximum year of vehicles manufactured in 2021",
#      "find  year, mileage of cars made by toyota where year is 2020",
#     "Fetch model of vehicles made by toyota.",
#     "Fetch details of vehicles manufactured in 2020.",
#     "fetch  mileage of vehicle where year is 2022",
#     "get all cars made by Toyota where year = 2019",
#     "find manufacturer,model of vehicles manufactured in 2021",
#     "fetch model of car made by toyota",
#     "find the year, mileage of cars made by toyota where year = 2020",
#     "get model of cars made by Toyota where in year 2019",
#     "get maximum price of car made by Kia where model is Sorento"
# ]

# for query in test_queries:
#     sql_query = parse_and_generate_sql(query)
#     print(f"User Query: {query}")
#     print(f"SQL Query: {sql_query}\n")
