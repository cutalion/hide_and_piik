import json
import sys
import re

def mask_value(value):
    if not isinstance(value, (str, int, float)):
        return str(type(value))
    
    s_val = str(value)
    # Replace letters with L
    s_val = re.sub(r'[a-zA-Zа-яА-Я]', 'L', s_val)
    # Replace digits with D
    s_val = re.sub(r'\d', 'D', s_val)
    return s_val

def traverse(data, path="", paths_stats=None):
    if paths_stats is None:
        paths_stats = {}

    if isinstance(data, dict):
        for k, v in data.items():
            # Check if key itself looks like PII (optional, but good to note)
            # For now, we just append the key to path
            new_path = f"{path}.{k}" if path else k
            traverse(v, new_path, paths_stats)
    elif isinstance(data, list):
        # For lists, we use [] to indicate array items
        new_path = f"{path}[]"
        for item in data:
            traverse(item, new_path, paths_stats)
    else:
        # Leaf node
        if path not in paths_stats:
            paths_stats[path] = set()
        
        # Add masked sample
        masked = mask_value(data)
        paths_stats[path].add(masked)

    return paths_stats

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <input_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def analyze_data(data):
    stats = traverse(data)
    
    # Convert sets to lists for JSON serialization and limit samples
    output = []
    for path, samples in stats.items():
        # Sort to make deterministic, take top 5 unique samples
        sorted_samples = sorted(list(samples))[:5]
        output.append({
            "path": path,
            "samples": sorted_samples
        })
    return output

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <input_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    output = analyze_data(data)
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
