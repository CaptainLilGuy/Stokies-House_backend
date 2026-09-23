from rapidfuzz import fuzz

MATCH_THRESHOLD = 70 # 0-100 scale — tune this based on testing results

def find_best_match(ocr_name: str, existing_items: list) -> dict | None:
    """
    existing_items: list of dicts like {'id': int, 'name': str}
    Returns the best-matching existing item (with a 'score' key added)
    if its similarity score meets the threshold, else None.
    """
    best_match = None
    best_score = 0

    for item in existing_items:
        score = fuzz.token_set_ratio(ocr_name.lower(), item['name'].lower())
        if score > best_score:
            best_score = score
            best_match = item

    if best_match and best_score >= MATCH_THRESHOLD:
        return {**best_match, 'score': best_score}
    else:
        return None