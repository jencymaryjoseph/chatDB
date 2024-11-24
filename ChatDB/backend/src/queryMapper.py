import re
import string
import nltk

# Dataset schema remains the same
dataset_schema = {
    "year": ["year", "model year", "manufacturing year", "production year","release year", "launch year", "publication year", "production year"],
    "make": ["company", "brand", "manufacturer", "automaker"],
    "model": ["model", "car model", "vehicle model", "make", "cars","model of car","car sold"],
    "body": ["body", "car body", "vehicle type", "chassis"],
    "transmission": ["transmission", "gearbox", "drive system", "transmission type"],
    "odometer": ["odometer", "mileage", "distance traveled", "miles"],
    "color": ["color", "paint", "shade", "hue"],
    "interior": ["interior", "inside", "cabin", "seating"],
    "sellingprice": ["selling price of car", "price", "cost", "value","price sold"],
    "name": ["title", "game name", "video game title", "game"],
    "platform": ["console", "gaming platform", "system", "device"],
    "genre": ["category", "game type", "game category", "style", "genre of games"],
    "publisher": ["developer", "game publisher", "studio", "producer"],
    "NA_Sales": ["North America sales", "NA revenue", "USA sales", "American sales"],
    "EU_Sales": ["Europe sales", "EU revenue", "European sales", "EMEA sales"],
    "JP_Sales": ["Japan sales", "JP revenue", "Japanese sales", "Asia sales"],
    "other_sales": ["miscellaneous sales", "other region sales", "additional sales", "ROW sales"],
    "global_sales": ["worldwide sales", "total sales", "global revenue", "all-region sales"],
    "order_id": ["transaction ID", "order number", "receipt number", "purchase ID"],
    "item_name": ["product name", "food item", "menu item", "dish"],
    "item_type": ["category", "food type", "cuisine type", "menu category"],
#"item_price": ["price per item", "unit price", "cost of item", "rate"],
    "quantity": ["amount", "number of items", "count", "item quantity"],
    "transaction_amount": ["total amount", "order value", "bill amount", "payment total"],
    "transaction_type": ["payment method", "transaction mode", "billing type", "payment type"]

}

# Operators mapping remains the same
operators = {
    '=': '=',
    '==': '=',
    '>': '>',
    '<': '<',
    '>=': '>=',
    '<=': '<=',
    '!=': '!=',
    'equal to': '=',
    'equals': '=',
    'greater than or equal to': '>=',
    'less than or equal to': '<=',
    'not equal to': '!=',
    'not equals': '!=',
    'greater than': '>',
    'less than': '<',
    'fewer than': '<',
    'more than': '>',
    'greater': '>',
    'exceeds': '>',
    'less': '<',
    'above': '>',
    'below': '<',
    'is': '='
}


# Patterns updated with new pattern for HAVING
patterns = {
    "aggregate <A> by <B>": """SELECT {B}, {aggregate_function}({A}) AS {alias}
FROM {table}
GROUP BY {B}{order_clause}{limit_clause};""",

    "aggregate <A> by <B> having <condition>": """SELECT {B}, {aggregate_function}({A}) AS {alias}
FROM {table}
GROUP BY {B}
HAVING {aggregate_function}({A}) {op} {value}{order_clause}{limit_clause};""",

    "retrieve <A> where <B>": """SELECT {A}
FROM {table}
WHERE {B} {op} {value}{order_clause}{limit_clause};""",

    "retrieve <A>": """SELECT {A}
FROM {table}{order_clause}{limit_clause};""",
}



aggregate_synonyms = ["total", "sum", "calculate", "compute", "aggregate", "add up", "summarize"]
retrieve_synonyms = ["list", "show", "display", "retrieve", "get", "fetch"]
order_synonyms = ["order by", "ordered by", "sort by", "sorted by", "arranged by", "based on", "highest", 'lowest']
order_directions = ["ascending", "asc", "descending", "desc", "highest number", "ascending order", "descending order"]
limit_synonyms = ["top", "first", "highest", "most", "bottom", "last", "lowest", "least"]
# Aggregate functions
aggregate_functions = ["sum", "average", "count", "min", "max"]

# Aggregate function mapping to SQL equivalents
aggregate_function_mapping = {
    "SUM": "SUM",
    "AVERAGE": "AVG",
    "COUNT": "COUNT",
    "MIN": "MIN",
    "MAX": "MAX"
}
aggregate_synonym_mapping = {
    'average': 'avg',
    'sum': 'sum',
    'total': 'sum',
    'count': 'count',
    'minimum': 'min',
    'maximum': 'max',
    'min': 'min',
    'max': 'max'
}
# List of stop words to exclude
stop_words = ["of", "and", "in", "on", "at", "by", "for"]

table_name = "CARSALES"

def match_column(input_term, schema):
    input_term = input_term.lower()
    for column, terms in schema.items():
        if input_term == column.lower() or input_term in [term.lower() for term in terms]:
            if column == 'sales':
                return 'transaction_qty * unit_price'
            else:
                return column
    # Singularize if necessary
    if input_term.endswith('es'):
        input_term_singular = input_term[:-2]
    elif input_term.endswith('s'):
        input_term_singular = input_term[:-1]
    else:
        input_term_singular = input_term
    if input_term_singular != input_term:
        for column, terms in schema.items():
            if input_term_singular == column.lower() or input_term_singular in [term.lower() for term in terms]:
                if column == 'sales':
                    return 'transaction_qty * unit_price'
                else:
                    return column
    return None

def match_operator(input_terms):
    for op_len in range(5, 0, -1):
        for i in range(len(input_terms) - op_len + 1):
            op_candidate = ' '.join(input_terms[i:i + op_len])
            op_symbol = operators.get(op_candidate)
            if op_symbol:
                return op_symbol, op_len
    return None, 0


def parse_input(text):
    # Ensure NLTK stopwords are downloaded
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords

    # Define stop words, excluding essential keywords
    stop_words = set(stopwords.words('english'))
    essential_keywords = {'retrieve', 'aggregate', 'where', 'having', 'by', 'order', 'group', 'select', 'top', 'bottom', 'on', 'a', 'than', 'and', 'to', 'not', 'or', 'of', 'is'}
    stop_words = stop_words - essential_keywords

    # Remove unnecessary punctuation (keep operator symbols, slashes, quotes, and commas)
    operator_symbols = set(['=', '>', '<', '!', '%'])
    punctuation_to_remove = ''.join(c for c in string.punctuation if c not in operator_symbols and c not in ['/', "'", ','])
    text = text.translate(str.maketrans("", "", punctuation_to_remove))
    text = text.rstrip('.')  # Remove period at the end if present

    # Preserve the original text for accurate extraction
    original_text = text

    # Convert text to lowercase for uniformity
    text = text.lower()

    # Remove stop words from the text
    text_tokens = text.split()
    text_tokens = [word for word in text_tokens if word not in stop_words]
    text = ' '.join(text_tokens)

    # Combine aggregate synonyms and functions
    aggregate_words = aggregate_synonyms + aggregate_functions

    # Ordering synonyms and direction

    # Limit synonyms
    limit_synonyms = ["top", "first", "highest", "most", "bottom", "last", "lowest", "least"]

    # Initialize order and limit placeholders
    order_column_raw = None
    order_direction = ''
    order_column = None
    limit_value = None

    # Check for limit phrases in text
    limit_match = None
    for synonym in limit_synonyms:
        pattern = r'\b' + re.escape(synonym) + r'\s+(\d+)\b'
        match = re.search(pattern, text)
        if match:
            limit_match = match.group()
            limit_value = match.group(1)
            text = text.replace(limit_match, '').strip()
            # Determine order direction based on synonym
            if synonym in ['top', 'first', 'highest', 'most']:
                order_direction = 'desc'
            elif synonym in ['bottom', 'last', 'lowest', 'least']:
                order_direction = 'asc'
            break

    # Check for ordering phrases in text
    ordering_match = None
    for phrase in order_synonyms:
        if phrase in text:
            ordering_match = phrase
            break

    if ordering_match:
        ordering_index = text.find(ordering_match)
        # Extract ordering column and direction
        ordering_part = text[ordering_index + len(ordering_match):].strip()
        # Remove ordering part from text
        text = text[:ordering_index].strip()
        # Check if direction is specified
        for direction in order_directions:
            if ordering_part.endswith(' ' + direction):
                order_direction = direction
                ordering_part = ordering_part[: -len(direction)].strip()
                break
        else:
            if not order_direction:
                order_direction = 'asc'  # Default to ascending if not set by limit synonym
        order_column_raw = ordering_part.strip()

    # Now, we need to split the text into words after processing limit and ordering
    words = text.lower().split()

    # Check for aggregate synonyms or functions
    aggregate_word = next((word for word in words if word in aggregate_words), None)
    retrieve_word = next((word for word in words if word in retrieve_synonyms), None)

    # Initialize limit clause
    if limit_value:
        limit_clause = f"\nLIMIT {limit_value}"
    else:
        limit_clause = ''

    # Proceed with parsing logic, adding limit clause where appropriate
    # For 'aggregate' patterns
    if aggregate_word and "by" in words:
        aggregate_index = words.index(aggregate_word)
        by_index = words.index("by")

        # Check if 'having' is present
        if "having" in words:
            having_index = words.index("having")
            if aggregate_index + 1 >= by_index or by_index + 1 >= having_index:
                print(f"Error: Missing or invalid columns between 'aggregate', 'by', and 'having'.")
                return None, {}
            # Extract A, B, and condition
            a_raw_tokens = words[aggregate_index + 1:by_index]
            b_raw_tokens = words[by_index + 1:having_index]
            condition_tokens = words[having_index + 1:]

            # Remove stop words from tokens
            a_raw_tokens = [token for token in a_raw_tokens if token not in stop_words]
            b_raw_tokens = [token for token in b_raw_tokens if token not in stop_words]
            condition_tokens = [token for token in condition_tokens if token not in stop_words]

            a_raw = ' '.join(a_raw_tokens)
            b_raw = ' '.join(b_raw_tokens)
            print(f"Raw inputs: A tokens='{a_raw_tokens}', B tokens='{b_raw_tokens}', condition='{condition_tokens}'")

            # Determine the aggregate function
            if aggregate_word in aggregate_functions:
                aggregate_function = aggregate_function_mapping.get(aggregate_word.upper(), aggregate_word.upper())
            else:
                aggregate_function = "SUM"  # Default aggregate function

            # Check if an aggregate function is specified in a_raw_tokens
            for func in aggregate_functions:
                if func in a_raw_tokens:
                    aggregate_function = aggregate_function_mapping.get(func.upper(), func.upper())
                    func_index = a_raw_tokens.index(func)
                    # Assume the rest after the function is the column
                    a_raw_tokens = a_raw_tokens[func_index + 1:]
                    a_raw = ' '.join(a_raw_tokens)
                    break

            print(f"Aggregate function: {aggregate_function}")
            print(f"Column A after extracting aggregate function and removing stop words: '{a_raw}'")

            # Match terms to dataset schema
            a = match_column(a_raw.strip(), dataset_schema)
            b = match_column(b_raw.strip(), dataset_schema)
            print(f"Matched columns: A='{a}', B='{b}'")
            if not a or not b:
                print(f"Error: Unable to match columns for 'aggregate <A> by <B>'. A={a}, B={b}")
                return None, {}  # Invalid columns

            # Parse condition
            condition_str = ' '.join(condition_tokens)
            print(f"Condition string: '{condition_str}'")

            # Initialize variables
            operator = None
            value = None
            condition_lhs = None

            # Try to find the operator within the condition string
            for op_phrase in sorted(operators.keys(), key=lambda x: -len(x.split())):
                if f' {op_phrase} ' in f' {condition_str} ':
                    op_symbol = operators[op_phrase]
                    operator = op_symbol
                    # Split the condition string using the operator
                    parts = condition_str.split(op_phrase)
                    if len(parts) == 2:
                        condition_lhs = parts[0].strip()
                        value = parts[1].strip()
                    break

            if not operator or not value:
                print("Error: Invalid condition in HAVING clause.")
                return None, {}

            print(f"Parsed condition: lhs='{condition_lhs}', operator='{operator}', value='{value}'")

            # Handle value quoting
            try:
                float(value)
                # It's a number, no need to modify
            except ValueError:
                # Not a number, ensure it's properly quoted
                value = value.strip("'\"")  # Remove existing quotes
                value = f"'{value}'"

            # Prepare alias for the aggregated column
            alias = a_raw.strip().replace(' ', '_')

            # Handle ordering for aggregate queries
            if order_column_raw:
                order_column = match_column(order_column_raw.strip(), dataset_schema)
                if not order_column:
                    # Maybe the ordering is on the alias
                    order_column_normalized = order_column_raw.lower().replace(' ', '_')
                    possible_alias = f"{aggregate_function.lower()}_{alias}"
                    if order_column_normalized == possible_alias.lower():
                        order_column = possible_alias
                    else:
                        print(f"Error: Unable to match ordering column '{order_column_raw}'.")
                        return None, {}
                # Determine order direction
                if order_direction.lower() in ['descending', 'desc', 'highest', 'descending order']:
                    order_dir_sql = 'DESC'
                else:
                    order_dir_sql = 'ASC'
                order_clause = f"\nORDER BY {order_column} {order_dir_sql}"
            else:
                order_clause = ''

            # Define placeholders before adding limit_clause
            placeholders = {
                "A": a,
                "B": b,
                "aggregate_function": aggregate_function,
                "aggregate_function_lower": aggregate_function.lower(),
                "table": table_name,
                "alias": f"{aggregate_function.lower()}_{alias}",
                "op": operator,
                "value": value,
                "order_column": order_clause,
                "limit_clause": limit_clause  # Include limit_clause here
            }

            return "aggregate <A> by <B> having <condition>", placeholders

        else:
            # Existing 'aggregate <A> by <B>' pattern
            if aggregate_index + 1 >= by_index:
                print(f"Error: Missing or invalid column between '{aggregate_word}' and 'by'.")
                return None, {}
            # Extract all words between aggregate word and 'by' for A
            a_raw_tokens = words[aggregate_index + 1:by_index]
            # Extract all words after 'by' for B
            b_raw_tokens = words[by_index + 1:]

            # Remove stop words from tokens
            a_raw_tokens = [token for token in a_raw_tokens if token not in stop_words]
            b_raw_tokens = [token for token in b_raw_tokens if token not in stop_words]

            a_raw = ' '.join(a_raw_tokens)
            b_raw = ' '.join(b_raw_tokens)
            print(f"Raw inputs: A tokens='{a_raw_tokens}', B tokens='{b_raw_tokens}'")

            # Determine the aggregate function
            if aggregate_word in aggregate_functions:
                aggregate_function = aggregate_function_mapping.get(aggregate_word.upper(), aggregate_word.upper())
            else:
                aggregate_function = "SUM"  # Default aggregate function

            # Check if an aggregate function is specified in a_raw_tokens
            for func in aggregate_functions:
                if func in a_raw_tokens:
                    aggregate_function = aggregate_function_mapping.get(func.upper(), func.upper())
                    func_index = a_raw_tokens.index(func)
                    # Assume the rest after the function is the column
                    a_raw_tokens = a_raw_tokens[func_index + 1:]
                    a_raw = ' '.join(a_raw_tokens)
                    break

            print(f"Aggregate function: {aggregate_function}")
            print(f"Column A after extracting aggregate function and removing stop words: '{a_raw}'")

            # Match terms to dataset schema
            a = match_column(a_raw.strip(), dataset_schema)
            b = match_column(b_raw.strip(), dataset_schema)
            print(f"Matched columns: A='{a}', B='{b}'")
            if not a or not b:
                print(f"Error: Unable to match columns for 'aggregate <A> by <B>'. A={a}, B={b}")
                return None, {}  # Invalid columns

            # Prepare alias for the aggregated column
            alias = a_raw.strip().replace(' ', '_')

            # Handle ordering for aggregate queries
            if order_column_raw:
                order_column = match_column(order_column_raw.strip(), dataset_schema)
                if not order_column:
                    # Maybe the ordering is on the alias
                    order_column_normalized = order_column_raw.lower().replace(' ', '_')
                    possible_alias = f"{aggregate_function.lower()}_{alias}"
                    if order_column_normalized == possible_alias.lower():
                        order_column = possible_alias
                    else:
                        print(f"Error: Unable to match ordering column '{order_column_raw}'.")
                        return None, {}
                # Determine order direction
                if order_direction.lower() in ['descending', 'desc', 'highest']:
                    order_dir_sql = 'DESC'
                else:
                    order_dir_sql = 'ASC'
                order_clause = f"\nORDER BY {order_column} {order_dir_sql}"
            else:
                # No ordering specified
                order_clause = ''

            placeholders = {
                "A": a,
                "B": b,
                "aggregate_function": aggregate_function,
                "aggregate_function_lower": aggregate_function.lower(),
                "table": table_name,
                "alias": f"{aggregate_function.lower()}_{alias}",
                "order_clause": order_clause,
                "limit_clause": limit_clause  # Include limit_clause here
            }
            return "aggregate <A> by <B>", placeholders

    elif retrieve_word:
        retrieve_indices = [i for i, word in enumerate(words) if word == retrieve_word]
        where_indices = [i for i, word in enumerate(words) if word == "where"]

        # Determine if 'where' is present
        if where_indices:
            # Handle 'retrieve <A> where <B>' pattern
            retrieve_index = retrieve_indices[0]
            where_index = where_indices[0]

            # Extract all words between 'retrieve' and 'where' for A
            a_raw_tokens = words[retrieve_index + 1:where_index]
            # Do not remove stop words here to preserve 'and'

            if not a_raw_tokens:
                # No columns specified, default to '*'
                a = '*'
            else:
                # Combine tokens
                a_raw = ' '.join(a_raw_tokens)
                # Insert spaces around commas
                a_raw = re.sub(r',', ' , ', a_raw)
                # Split columns on commas and 'and'
                columns = re.split(r'\s*(?:,|and)\s*', a_raw)
                column_names = []
                for col in columns:
                    col = col.strip()
                    if not col:
                        continue
                    # Optionally remove stop words from individual column names
                    col_tokens = [token for token in col.split() if token not in stop_words]
                    col = ' '.join(col_tokens)
                    column = match_column(col, dataset_schema)
                    if column:
                        column_names.append(column)
                    else:
                        print(f"Error: Unable to match column '{col}'.")
                        return None, {}
                a = ', '.join(column_names)

            # Extract condition after 'where'
            condition_tokens = words[where_index + 1:]
            if not condition_tokens:
                print("Error: Incomplete condition after 'where'.")
                return None, {}
            condition_str = ' '.join(condition_tokens)

            # Try to find the operator within the condition string
            operator = None
            value = None
            condition_column_raw = None
            for op_phrase in sorted(operators.keys(), key=lambda x: -len(x.split())):
                if f' {op_phrase} ' in f' {condition_str} ':
                    op_symbol = operators[op_phrase]
                    operator = op_symbol
                    parts = condition_str.split(op_phrase)
                    if len(parts) == 2:
                        condition_column_raw = parts[0].strip()
                        value = parts[1].strip()
                    break

            if not operator or not value:
                print("Error: Invalid condition in WHERE clause.")
                return None, {}

            # Match condition column
            condition_column = match_column(condition_column_raw, dataset_schema)
            if not condition_column:
                print(f"Error: Unable to match condition column '{condition_column_raw}'.")
                return None, {}

            # Handle cases where 'top' or 'highest' is used without an explicit ordering column
            if limit_value and not ordering_match and any(agg_word in condition_column_raw for agg_word in ['total', 'sum', 'average', 'count', 'max', 'min']):
                # Treat as an aggregate query with a HAVING clause
                aggregate_function = 'SUM'  # Default to SUM; can enhance based on condition_column_raw
                # Use aggregate_word if present
                if aggregate_word:
                    aggregate_function = aggregate_synonym_mapping.get(aggregate_word.lower(), 'SUM').upper()
                # Extract B (grouping column) from A
                b_raw = a if a != '*' else 'store'  # Default grouping column if not specified
                b = match_column(b_raw.strip(), dataset_schema)
                if not b:
                    print(f"Error: Unable to match grouping column '{b_raw}'.")
                    return None, {}
                a_column = condition_column  # The column to aggregate (e.g., 'sales')
                alias = f"{aggregate_function.lower()}_{a_column.replace('.', '_')}"
                # Handle ordering
                order_column = f"{aggregate_function}({a_column})"
                if order_direction.lower() in ['descending', 'desc']:
                    order_dir_sql = 'DESC'
                else:
                    order_dir_sql = 'ASC'
                order_clause = f"\nORDER BY {order_column} {order_dir_sql}"
                # Handle value quoting
                try:
                    float(value)
                except ValueError:
                    value = value.strip("'\"")
                    value = f"'{value}'"
                placeholders = {
                    "A": a_column,
                    "B": b,
                    "aggregate_function": aggregate_function,
                    "alias": alias,
                    "table": table_name,
                    "op": operator,
                    "value": value,
                    "order_clause": order_clause,
                    "limit_clause": limit_clause
                }
                return "aggregate <A> by <B> having <condition>", placeholders
            else:
            # Proceed as normal retrieve query
            # Handle ordering for retrieve queries
                if order_column_raw:
                    order_column = match_column(order_column_raw.strip(), dataset_schema)
                    if not order_column:
                        print(f"Error: Unable to match ordering column '{order_column_raw}'.")
                        return None, {}
                else:
                    # Default to ordering by the condition column if limit is specified
                    if limit_value:
                        order_column = condition_column
                    else:
                        order_column = None

                if order_column:
                    # Determine order direction
                    if order_direction.lower() in ['descending', 'desc', 'highest']:
                        order_dir_sql = 'DESC'
                    else:
                        order_dir_sql = 'ASC'
                    order_clause = f"\nORDER BY {order_column} {order_dir_sql}"
                else:
                    order_clause = ''

                # Handle value quoting
                try:
                    float(value)
                except ValueError:
                    value = value.strip("'\"")
                    value = f"'{value}'"
                placeholders = {
                    "A": a,
                    "B": condition_column,
                    "op": operator,
                    "value": value,
                    "table": table_name,
                    "order_clause": order_clause,
                    "limit_clause": limit_clause
                }
                return "retrieve <A> where <B>", placeholders
        else:
            # Handle 'retrieve <A>' pattern without 'where'
            retrieve_index = retrieve_indices[0]
            # Extract all words after 'retrieve' for A
            a_raw_tokens = words[retrieve_index + 1:]
            # Do not remove stop words here to preserve 'and'

            if not a_raw_tokens:
                # No columns specified, default to '*'
                a = '*'
            else:
                # Combine tokens
                a_raw = ' '.join(a_raw_tokens)
                # Insert spaces around commas
                a_raw = re.sub(r',', ' , ', a_raw)
                # Split columns on commas and 'and'
                columns = re.split(r'\s*(?:,|and)\s*', a_raw)
                column_names = []
                for col in columns:
                    col = col.strip()
                    if not col:
                        continue
                    # Optionally remove stop words from individual column names
                    col_tokens = [token for token in col.split() if token not in stop_words]
                    col = ' '.join(col_tokens)
                    column = match_column(col, dataset_schema)
                    if column:
                        column_names.append(column)
                    else:
                        print(f"Error: Unable to match column '{col}'.")
                        return None, {}
                a = ', '.join(column_names)

            # Handle ordering for retrieve queries
            if order_column_raw:
                order_column = match_column(order_column_raw.strip(), dataset_schema)
                if not order_column:
                    print(f"Error: Unable to match ordering column '{order_column_raw}'.")
                    return None, {}
                # Determine order direction
                if order_direction.lower() in ['descending', 'desc', 'highest']:
                    order_dir_sql = 'DESC'
                else:
                    order_dir_sql = 'ASC'
                order_clause = f"\nORDER BY {order_column} {order_dir_sql}"
            else:
                order_clause = ''

            placeholders = {
                "A": a,
                "table": table_name,
                "order_clause": order_clause,
                "limit_clause": limit_clause
            }
            return "retrieve <A>", placeholders

    else:
        print("Pattern not recognized in input text.")
        return None, {}

def generate_query(pattern_key, placeholders):
    """
    Generate the SQL query based on the pattern and placeholders.
    """
    if pattern_key in patterns:
        query_template = patterns[pattern_key]

        # Generate the query
        query = query_template.format(**placeholders)
        return query
    print("Pattern not recognized.")
    return "Pattern not recognized."