import os

def get_stats(root_dir):
    loc = 0
    total_size = 0
    relevant_dirs = ['core', 'infra', 'local_api', 'scripts', 'tests']
    
    for root, dirs, files in os.walk(root_dir):
        # Exclude hidden and venv dirs
        if '.venv' in root or '.git' in root or '.idea' in root:
            continue
            
        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                total_size += size
                
                if file.endswith('.py'):
                    # Only count LOC if it's in a relevant dir or root
                    is_relevant = any(rd in path for rd in relevant_dirs) or root == root_dir
                    if is_relevant:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            loc += sum(1 for _ in f)
            except:
                pass
                
    return loc, total_size / (1024 * 1024)

loc, size_mb = get_stats('.')
print(f"LOC: {loc}")
print(f"Size (MB): {size_mb:.2f}")
