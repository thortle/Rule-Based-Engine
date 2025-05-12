import json
import re
import os

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# If the script is in the parent directory, adjust the path
if os.path.basename(script_dir) != 'french-chunker':
    script_dir = os.path.join(script_dir, 'french-chunker')

def load_json(filepath):
    """
    Load a JSON file from the given filepath.

    Args:
        filepath (str): Path to the JSON file

    Returns:
        dict or list: The loaded JSON data
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_text(filepath):
    """
    Load raw text from the given filepath.

    Args:
        filepath (str): Path to the text file

    Returns:
        str: The loaded text
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def tokenize(text):
    """
    Tokenize the input text into a list of tokens.

    Args:
        text (str): The input text to tokenize

    Returns:
        list: A list of tokens
    """
    # Use regex to split words (handling apostrophes like l' and hyphens like week-end)
    # and punctuation separately
    tokens = re.findall(r"\w+(?:[-']\w+)*|[^\w\s]", text)
    return tokens



def chunk_text(tokens, rules, lexicon):
    """
    Chunk the input tokens based on the provided rules and lexicon.

    Args:
        tokens (list): The input tokens (plain strings)
        rules (list): The chunking rules
        lexicon (dict): The lexicon for token categorization

    Returns:
        list: A list of chunk dictionaries
    """
    chunks = []
    i = 0

    def matches_element(token, element):
        if element["type"] == "lexicon_category":
            # Check if token is in the lexicon category
            lexicon_key = element["key"]
            if lexicon_key in lexicon:
                return token.lower() in [word.lower() for word in lexicon[lexicon_key]]
            return False

        elif element["type"] == "lookup":
            # Check if token exactly matches the lookup value
            return token.lower() == element["value"].lower()

        elif element["type"] == "category":
            # Simple category matching - only basic validation
            punctuation = ['.', ',', ';', ':', '!', '?', '(', ')', '[', ']', '"', "'"]
            function_word_categories = ['P', 'CC', 'Det', 'CS', 'PPS', 'Mod', 'DET', 'ADP', 'AUX', 'CCONJ', 'SCONJ', 'PRON', 'PART']

            # Check if token is not punctuation
            if token in punctuation:
                return False

            # Check if token is not in any function word category
            for category in function_word_categories:
                if category in lexicon and token.lower() in [word.lower() for word in lexicon[category]]:
                    return False

            # Default case - accept the token if it's not punctuation or a function word
            return True

        elif element["type"] == "suffix":
            # Check if token ends with the suffix
            suffix = element["value"]
            return token.lower().endswith(suffix.lower())

        elif element["type"] == "regex":
            # Check if token matches the regex pattern
            return bool(re.match(element["value"], token))

        # Default case
        return False

    while i < len(tokens):
        # First, try to match sequence rules (prioritize over single-token rules)
        matched_sequence_rule = False

        for rule in rules:
            if rule["pattern"]["type"] == "sequence":
                # Get the sequence elements
                elements = rule["pattern"]["elements"]

                # Check if enough tokens remain
                if i + len(elements) <= len(tokens):
                    # Check if all elements match
                    all_match = True
                    for j, element in enumerate(elements):
                        if not matches_element(tokens[i + j], element):
                            all_match = False
                            break

                    if all_match:
                        # Create a chunk for the matched sequence
                        chunk_text = " ".join([tokens[i + j] for j in range(len(elements))])
                        chunks.append({
                            "text": chunk_text,
                            "category": rule["category"],
                            "rule": rule["pattern_description"]
                        })
                        i += len(elements)
                        matched_sequence_rule = True
                        break

        # If no sequence rule matched, try single-token rules
        if not matched_sequence_rule:
            matched_single_rule = False

            for rule in rules:
                if rule["pattern"]["type"] != "sequence":
                    if matches_element(tokens[i], rule["pattern"]):
                        chunks.append({
                            "text": tokens[i],
                            "category": rule["category"],
                            "rule": rule["pattern_description"]
                        })
                        matched_single_rule = True
                        break

            # If no rule matched, mark as UNKNOWN
            if not matched_single_rule:
                chunks.append({
                    "text": tokens[i],
                    "category": "UNKNOWN",
                    "rule": "No matching rule"
                })

            i += 1

    return chunks

def calculate_statistics(chunks):
    """
    Calculate statistics about the chunking results.

    Args:
        chunks (list): The list of chunks

    Returns:
        tuple: (categories_count, total_chunks, unknown_count, categorization_rate)
    """
    total_chunks = len(chunks)
    categories_count = {}
    unknown_count = 0

    for chunk in chunks:
        category = chunk["category"]
        if category == "UNKNOWN":
            unknown_count += 1
        else:
            categories_count[category] = categories_count.get(category, 0) + 1

    # Sort categories by count (descending)
    categories_count = dict(sorted(categories_count.items(), key=lambda x: x[1], reverse=True))

    # Calculate categorization rate
    categorization_rate = ((total_chunks - unknown_count) / total_chunks) * 100 if total_chunks > 0 else 0

    return categories_count, total_chunks, unknown_count, categorization_rate

def generate_text_output(chunks, categories_count, total_chunks, unknown_count, categorization_rate):
    """
    Generate a text representation of the chunked text.

    Args:
        chunks (list): List of chunk dictionaries
        categories_count (dict): Dictionary mapping categories to their counts
        total_chunks (int): Total number of chunks
        unknown_count (int): Number of UNKNOWN chunks
        categorization_rate (float): Categorization rate percentage

    Returns:
        str: Text representation
    """
    output = "===== CHUNKING STATISTICS =====\n\n"
    output += f"Total chunks: {total_chunks}\n"
    output += f"Unknown chunks: {unknown_count}\n"
    output += f"Categorization rate: {categorization_rate:.1f}%\n\n"

    output += "===== CATEGORY DISTRIBUTION =====\n\n"
    for category, count in categories_count.items():
        percentage = (count / total_chunks) * 100
        output += f"{category}: {count} ({percentage:.1f}%)\n"

    output += "\n===== CHUNKED TEXT =====\n\n"
    for chunk in chunks:
        category = chunk["category"]
        text = chunk["text"]
        output += f"[{category}] {text} "

    return output

# No HTML output generation as per requirements

if __name__ == "__main__":
    # Language selection
    print("\nSelect the language of the input text:")
    print("fr - French")
    print("en - English")
    lang_choice = input("Enter language (fr/en): ").lower()

    # Set paths based on language choice
    if lang_choice == "en":
        rules_path = os.path.join(script_dir, 'lang_en', 'rules.json')
        lexicon_path = os.path.join(script_dir, 'lang_en', 'lexicon.json')
        print("\n===== USING ENGLISH RULES AND LEXICON =====\n")
    else:
        # Default to French if invalid choice
        if lang_choice != "fr":
            print(f"\nInvalid language choice: '{lang_choice}'. Defaulting to French.")
        rules_path = os.path.join(script_dir, 'lang_fr', 'rules.json')
        lexicon_path = os.path.join(script_dir, 'lang_fr', 'lexicon.json')
        print("\n===== USING FRENCH RULES AND LEXICON =====\n")

    # Ask user which text to process
    print("\nWhich text would you like to process?")

    if lang_choice == "en":
        available_texts = {
            "1": os.path.join(script_dir, 'data', 'english_sports.txt')
        }
    else:
        available_texts = {
            "1": os.path.join(script_dir, 'data', 'gorafi_medical.txt'),
            "2": os.path.join(script_dir, 'data', 'gorafi_sports.txt'),
            "3": os.path.join(script_dir, 'data', 'figaro_text.txt')
        }

    # Display available texts
    for key, path in available_texts.items():
        print(f"{key}. {os.path.basename(path)}")

    # Get user choice
    choice_keys = ", ".join(available_texts.keys())
    choice = input(f"Enter your choice ({choice_keys}): ")

    # Get text path based on choice
    text_path = available_texts.get(choice)
    if not text_path:
        print(f"Invalid choice: '{choice}'. Exiting.")
        exit(1)

    # Determine output path based on text_path
    base_filename = os.path.basename(text_path).replace('.txt', '')
    output_path = os.path.join(script_dir, 'data', 'output', f"{base_filename}_chunked_auto.txt")

    print(f"\n===== PROCESSING {base_filename.upper()} =====\n")

    # Load rules and lexicon
    print(f"Loading rules from {rules_path} and lexicon from {lexicon_path}...")
    rules = load_json(rules_path)
    lexicon = load_json(lexicon_path)

    # Load text
    print(f"Loading text from {text_path}...")
    text = load_text(text_path)
    print(f"Text starts with: {text[:100]}...")

    # Tokenize text
    print("Tokenizing text...")
    tokens = tokenize(text)
    print(f"Tokenized {len(tokens)} tokens")

    # Print a sample of tokens
    if tokens:
        print("\nSample of tokens:")
        for i, token in enumerate(tokens[:5]):
            print(f"  {i+1}. Token: '{token}'")
        print("  ...")

    # Chunk the text
    print("\nChunking text...")
    chunks = chunk_text(tokens, rules, lexicon)

    # Calculate statistics
    print("Calculating statistics...")
    categories_count, total_chunks, unknown_count, categorization_rate = calculate_statistics(chunks)

    # Generate text output
    print("Generating text output...")
    output_text = generate_text_output(chunks, categories_count, total_chunks, unknown_count, categorization_rate)

    # Write output to file
    print(f"Saving output to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(output_text)

    # No HTML output generation as per requirements

    # Print statistics
    print("\n===== CHUNKING STATISTICS =====\n")
    print(f"Total chunks: {total_chunks}")
    print(f"Unknown chunks: {unknown_count}")
    print(f"Categorization rate: {categorization_rate:.1f}%\n")

    print("===== CATEGORY DISTRIBUTION =====\n")
    for category, count in categories_count.items():
        percentage = (count / total_chunks) * 100
        print(f"{category}: {count} ({percentage:.1f}%)")

    # Print all chunks without limiting the output
    print("\n===== ALL CHUNKS =====\n")
    for i, chunk in enumerate(chunks):
        print(f"[{chunk['category']}] {chunk['text']}")
        if i % 10 == 9:
            print()

    print(f"\nOutput saved to: {output_path}")
