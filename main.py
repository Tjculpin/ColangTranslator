import re
import ast
import os
import glob
import sys

def get_exe_directory():
    """
    Returns the directory containing the executable (or script when not frozen).
    Handles PyInstaller --onefile mode by using sys.executable for the .exe path.
    """
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller .exe
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Running as a Python script
        return os.path.dirname(os.path.abspath(__file__))

def get_available_languages():
    """
    Scans the executable's directory for files matching '*_translations.txt'
    and returns a list of language names (the part before '_translations.txt').
    Only includes files that are valid and readable.
    """
    script_dir = get_exe_directory()
    print(f"Scanning directory: {script_dir}")
    # Find all files matching the pattern '*_translations.txt' (case-insensitive)
    translation_files = glob.glob(os.path.join(script_dir, '*_translations.txt'))
    languages = []
    
    for file_path in translation_files:
        language = os.path.basename(file_path).rsplit('_translations.txt', 1)[0]
        # Quick validation to ensure file is readable and has correct format
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content.startswith('translation_dict ='):
                    content = content[len('translation_dict ='):].strip()
                    ast.literal_eval(content)  # Test parsing
                    languages.append(language)
                else:
                    print(f"Warning: {file_path} does not start with 'translation_dict ='. Skipping.")
        except (FileNotFoundError, PermissionError) as e:
            print(f"Warning: Cannot access {file_path}: {str(e)}. Skipping.")
        except (SyntaxError, ValueError) as e:
            print(f"Warning: Invalid dictionary format in {file_path}: {str(e)}. Skipping.")
    
    print(f"Found languages: {languages}")
    return languages

def load_translation_dict(language):
    """
    Loads translation dictionary from a text file for the specified language.
    File should be named '<language>_translations.txt' and contain a Python dictionary.
    """
    script_dir = get_exe_directory()
    file_path = os.path.join(script_dir, f"{language}_translations.txt")
    
    translation_dict = {}
    try:
        print(f"Loading translation file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Extract the dictionary part after "translation_dict ="
            if content.startswith('translation_dict ='):
                content = content[len('translation_dict ='):].strip()
            # Safely evaluate the string as a Python dictionary
            translation_dict = ast.literal_eval(content)
            # Ensure all keys are lowercase
            translation_dict = {k.lower(): v for k, v in translation_dict.items()}
        return translation_dict
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return {}
    except (SyntaxError, ValueError) as e:
        print(f"Error: Invalid dictionary format in {file_path}: {str(e)}")
        return {}
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return {}

def translate_to_conlang(text, translation_dict):
    """
    Translates English text to the constructed language, handling punctuation and case-insensitive matching.
    Preserves original case, punctuation, and untranslated words.
    """
    # Split text into words and punctuation using regex
    # \w+ matches words, [^\w\s] matches punctuation, \s+ matches whitespace
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text, re.UNICODE)
    translated_tokens = []
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Check if token is a word
        if re.match(r'\w+', token):
            # Handle multi-word phrases (e.g., "you all", "good-bye")
            translated = None
            if i + 2 < len(tokens) and tokens[i+1].lower() == "all":
                phrase = f"{token.lower()} all"
                if phrase in translation_dict:
                    translated = translation_dict[phrase]
                    i += 2  # Skip the next token ("all")
                else:
                    translated = token  # Keep untranslated word
                    i += 1
            elif i + 2 < len(tokens) and tokens[i+1] == "-" and tokens[i+2].lower() == "bye":
                phrase = "good-bye"
                if phrase in translation_dict:
                    translated = translation_dict[phrase]
                    i += 3  # Skip "good", "-", and "bye"
                else:
                    translated = token  # Keep untranslated word
                    i += 1
            else:
                # Single word translation
                word_lower = token.lower()
                if word_lower in translation_dict:
                    translated = translation_dict[word_lower]
                else:
                    translated = token  # Keep untranslated word as is
                i += 1
            
            # Preserve original case
            if token.isupper():
                translated = translated.upper()
            elif token[0].isupper() and len(token) > 1:
                translated = translated[0].upper() + translated[1:].lower()
            elif token[0].isupper():
                translated = translated[0].upper()
        else:
            # Preserve punctuation and whitespace
            translated = token
            i += 1
        
        translated_tokens.append(translated)
    
    return "".join(translated_tokens)

# Interactive translation loop
if __name__ == "__main__":
    # Get available languages
    languages = get_available_languages()
    
    if not languages:
        print("Error: No valid translation files found (looking for '*_translations.txt'). Exiting.")
        sys.exit(1)
    
    # Prompt user to select a language
    print("\nAvailable languages:")
    for i, lang in enumerate(languages, 1):
        print(f"{i}. {lang}")
    while True:
        try:
            choice = input("Select a language (enter the number): ")
            choice = int(choice) - 1
            if 0 <= choice < len(languages):
                selected_language = languages[choice]
                break
            else:
                print(f"Please enter a number between 1 and {len(languages)}.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Load the translation dictionary for the selected language
    translation_dict = load_translation_dict(selected_language)
    
    if not translation_dict:
        print(f"No translations loaded for {selected_language}. Exiting.")
        sys.exit(1)
    
    print(f"\nWelcome to the {selected_language} Translator!")
    print("Enter text to translate (or type 'exit' to quit):")
    
    while True:
        user_input = input("> ")
        if user_input.lower() == "exit":
            print(f"Goodbye! (Vekhterüszt in {selected_language}!)")
            break
        if user_input.strip() == "":
            print("Please enter some text to translate.")
            continue
        translated_text = translate_to_conlang(user_input, translation_dict)
        print(f"Translated: {translated_text}\n")