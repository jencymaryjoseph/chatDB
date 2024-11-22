import spacy
from spacy.matcher import Matcher
from typing import Dict

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize matcher for intent detection
matcher = Matcher(nlp.vocab)

# Add patterns for intent detection
matcher.add("FIND_TOTAL_SALES", [[{"LOWER": "find"}, {"LOWER": "total"}, {"LOWER": "sales"}]])
matcher.add("SHOW_AVERAGE_PRICE", [[{"LOWER": "show"}, {"LOWER": "average"}, {"LOWER": "price"}]])

# Database schema mapping
database_mapping = {
    "product category": "product_sales.category",
    "sales": "SUM(product_sales.sales)",
}

# Query template
query_templates = {
    "SELECT": "SELECT {columns} FROM {table} WHERE {conditions}",
    "GROUP_BY": "SELECT {columns}, {group_by} FROM {table} WHERE {conditions} GROUP BY {group_by}",
}

# Parse Query Function
def parse_query(user_query: str) -> Dict:
    # Process the query using SpaCy
    doc = nlp(user_query)
    
    # Dependency parsing
    subject = [token.text for token in doc if token.dep_ == "nsubj"]
    action = [token.text for token in doc if token.dep_ == "ROOT"]
    attributes = [token.text for token in doc if token.dep_ in ("pobj", "attr", "dobj")]
    
    # Intent detection
    matches = matcher(doc)
    detected_intent = None
    for match_id, start, end in matches:
        detected_intent = nlp.vocab.strings[match_id]
        break  # Assume one match is enough
    
    # Map attributes to schema
    mapped_columns = [database_mapping.get(attr, attr) for attr in attributes]
    mapped_subject = database_mapping.get(subject[0], subject[0]) if subject else "*"
    
    return {
        "intent": detected_intent,
        "action": action[0] if action else None,
        "columns": ", ".join(mapped_columns) if mapped_columns else mapped_subject,
        "table": "product_sales",  # Example table
        "conditions": "1=1",  # Default condition
        "group_by": attributes[0] if attributes else None
    }

# Generate Query Function
def generate_query(parsed_data: Dict) -> str:
    if parsed_data["intent"] == "FIND_TOTAL_SALES":
        # Example of GROUP BY query
        return query_templates["GROUP_BY"].format(
            columns=parsed_data["columns"],
            table=parsed_data["table"],
            conditions=parsed_data["conditions"],
            group_by=parsed_data["group_by"]
        )
    elif parsed_data["intent"] == "SHOW_AVERAGE_PRICE":
        # Example of SELECT query
        return query_templates["SELECT"].format(
            columns="AVG(price)",
            table="product_sales",
            conditions="1=1"
        )
    else:
        return "Unsupported query type."

# Main Function
if __name__ == "__main__":
    # Example user queries
    queries = [
        "Find total sales by product category",
        "Show average price of products"
    ]
    
    for user_query in queries:
        print(f"User Query: {user_query}")
        parsed_data = parse_query(user_query)
        print("Parsed Data:", parsed_data)
        sql_query = generate_query(parsed_data)
        print("Generated Query:", sql_query)
        print("-" * 50)
