class RiskModel:
    VERSION = "rf-0.0"

    @staticmethod
    def predict_proba(features: dict) -> float:
        # Dummy probability based on simple heuristic
        score = 0.0
        score += min(features.get("cyclomatic_max", 0)/20, 1)
        score += min(features.get("dup_ratio", 0)*2, 1)
        score += min(features.get("loc", 0)/1000, 1)
        
        # Security vulnerabilities significantly increase risk
        security_issues = features.get("security_issues", 0)
        if security_issues > 0:
            # Each security issue adds substantial risk
            score += min(security_issues * 0.3, 0.8)
        
        # Critical smells (severity 5) should push risk higher
        critical_smells = features.get("critical_smells", 0)
        if critical_smells > 0:
            score += min(critical_smells * 0.25, 0.7)
        
        return min(score/3 if security_issues == 0 else score/2, 1.0)

    @staticmethod
    def to_risk(proba: float) -> int:
        return round(100 * proba)

    @staticmethod
    def to_tier(risk: int) -> str:
        if risk <= 30:
            return "Low"
        if risk <= 60:
            return "Medium"
        if risk <= 80:
            return "High"
        return "Critical"
