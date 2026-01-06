try:
    from rapidfuzz import process, fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    import difflib
    HAS_RAPIDFUZZ = False

class FuzzyMatchService:
    def __init__(self):
        pass

    def get_similar_branches(self, new_branch_name, existing_branch_names, threshold=85):
        """
        Returns a list of tuples (match, score) for branches that are similar to new_branch_name.
        Restricted to >= threshold.
        """
        if not existing_branch_names:
            return []

        if HAS_RAPIDFUZZ:
            # rapidfuzz implementation
            matches = process.extract(
                new_branch_name, 
                existing_branch_names, 
                scorer=fuzz.ratio, 
                limit=5
            )
            # matches is a list of (match, score, index)
            results = [(m[0], m[1]) for m in matches if m[1] >= threshold]
            return results
        else:
            # difflib fallback
            results = []
            for branch in existing_branch_names:
                # difflib ratio is 0.0-1.0, we scale to 0-100
                score = difflib.SequenceMatcher(None, new_branch_name.lower(), branch.lower()).ratio() * 100
                if score >= threshold:
                    results.append((branch, score))
            # Sort by score desc
            results.sort(key=lambda x: x[1], reverse=True)
            return results
