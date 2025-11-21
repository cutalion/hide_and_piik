import json
import sys


def _get_placeholder(label, original_value, cache, counters):
    """Return a deterministic placeholder for a unique (label, value) pair."""
    label_cache = cache.setdefault(label, {})
    if isinstance(original_value, (dict, list)):
        normalized_value = json.dumps(original_value, sort_keys=True, ensure_ascii=False)
    else:
        normalized_value = original_value

    if normalized_value in label_cache:
        return label_cache[normalized_value]

    counters[label] = counters.get(label, 0) + 1
    placeholder = f"<{label}:{counters[label]}>"
    label_cache[normalized_value] = placeholder
    return placeholder


def traverse_and_redact(data, config, path="", cache=None, counters=None):
    if cache is None:
        cache = {}
    if counters is None:
        counters = {}

    if isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{path}.{k}" if path else k
            
            # Check if this path is in config
            if new_path in config:
                if v is None:
                    continue
                label = config[new_path]
                data[k] = _get_placeholder(label, v, cache, counters)
            else:
                traverse_and_redact(v, config, new_path, cache, counters)
                
    elif isinstance(data, list):
        new_path = f"{path}[]"
        # Check if the list itself is marked (unlikely but possible)
        if new_path in config:
             # This would replace the whole list, which might be what's wanted if the list contains PII
             # But usually we want to redact items inside.
             # For now, let's just traverse items.
             pass
             
        for i, item in enumerate(data):
            # We don't replace the item in the list directly here easily if it's a primitive
            # because we are iterating.
            # But if it's a dict/list, we recurse.
            # If it's a primitive, we need to check if the list path is in config?
            # Actually, our paths for list items are like "items[]".
            # So if "items[]" is in config, it means "redact every item in this list".
            
            if new_path in config:
                if item is None:
                    continue
                label = config[new_path]
                data[i] = _get_placeholder(label, item, cache, counters)
            else:
                if isinstance(item, (dict, list)):
                    traverse_and_redact(item, config, new_path, cache, counters)
                # If it's a primitive and not in config, we leave it.
                # Note: The analyzer produces paths like "a.b[]" for primitives in a list.
                # If the config says "a.b[]": "PHONE", we should redact it.
                
                # Wait, my analyzer produces "a.b[]" for the *value* inside the list if it's a primitive?
                # Let's check analyzer logic:
                # if isinstance(data, list): new_path = f"{path}[]"; for item in data: traverse(item, new_path)
                # if item is primitive, it goes to 'else' block and records path "a.b[]".
                # So yes, if we have ["123", "456"], path is "list[]".
                
    return data

def main():
    if len(sys.argv) < 3:
        print("Usage: python redact.py <input_file.json> <config_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    config_file = sys.argv[2]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading files: {e}")
        sys.exit(1)

    redacted_data = traverse_and_redact(data, config)
    
    print(json.dumps(redacted_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
