# file: promptrecon/sociotech/git_analyzer.py
import os
from git import Repo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_author_risk(repo_path: str, filepath: str) -> dict:
    """
    Look up the git history of a specific file to determine who introduced a potential leak.
    Also calculates a "risk score" based on commit timing and frequency.
    """
    try:
        repo = Repo(repo_path)
    except Exception as e:
        logger.warning(f"Not a valid git repository: {e}")
        return {"author": "Unknown", "sociotech_risk": 0.0}

    # Make path relative to repo root
    try:
        rel_path = os.path.relpath(filepath, repo.working_dir)
        
        # Blame the file to see who last touched the lines (for simplicity, we grab the latest commit)
        # In a real tool, we'd map the exact line of the leak to the blame list.
        commits = list(repo.iter_commits(paths=rel_path, max_count=5))
        
        if not commits:
            return {"author": "Unknown", "sociotech_risk": 0.0}
            
        latest_commit = commits[0]
        author_email = latest_commit.author.email
        
        # Sociotechnical Risk Heuristic Demo:
        # e.g., Commits made on weekends or very late at night get higher risk scores
        commit_time = latest_commit.authored_datetime
        risk_score = 0.0
        
        if commit_time.weekday() >= 5: # Weekend
            risk_score += 2.0
        
        if commit_time.hour < 6 or commit_time.hour > 22: # Late night
            risk_score += 2.5
            
        return {
            "author": author_email,
            "commit_hash": latest_commit.hexsha,
            "time": str(commit_time),
            "sociotech_risk_modifier": min(risk_score, 5.0)
        }
    except Exception as e:
        logger.error(f"Failed to analyze git history for {filepath}: {e}")
        return {"author": "Error", "sociotech_risk": 0.0}
