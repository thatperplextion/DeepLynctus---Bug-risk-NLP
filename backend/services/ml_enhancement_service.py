"""
ML Model Enhancement Service
Model explainability, custom thresholds, and anomaly detection
"""

from typing import Dict, List, Optional
import numpy as np


class MLEnhancementService:
    """Enhanced ML capabilities for bug risk prediction"""
    
    def __init__(self, db):
        self.db = db
        self.custom_thresholds = {}
        self.anomaly_baseline = {}
    
    async def explain_risk_score(self, file_path: str, risk_score: float) -> Dict:
        """
        Explain why a file has a specific risk score
        
        Shows feature contributions to the prediction
        """
        # Simulated feature contributions
        features = {
            "complexity": 0.25,
            "code_smells": 0.20,
            "dependencies": 0.15,
            "test_coverage": -0.10,  # Negative means it reduces risk
            "code_duplication": 0.18,
            "lines_of_code": 0.12,
            "recent_changes": 0.10
        }
        
        # Normalize to match risk score
        total_contribution = sum(abs(v) for v in features.values())
        normalized_features = {
            k: (v / total_contribution) * risk_score
            for k, v in features.items()
        }
        
        # Sort by impact
        sorted_features = sorted(
            normalized_features.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return {
            "file": file_path,
            "risk_score": risk_score,
            "feature_contributions": dict(sorted_features),
            "top_risk_factors": [
                {"feature": f[0], "impact": f[1]}
                for f in sorted_features[:3]
            ],
            "explanation": self._generate_explanation(sorted_features)
        }
    
    def _generate_explanation(self, sorted_features: List) -> str:
        """Generate human-readable explanation"""
        top_feature = sorted_features[0]
        
        explanations = {
            "complexity": "High cyclomatic complexity is the main risk factor",
            "code_smells": "Multiple code smells detected",
            "dependencies": "Complex dependency structure increases risk",
            "code_duplication": "Significant code duplication found",
            "lines_of_code": "File is very large",
            "recent_changes": "Frequent recent modifications"
        }
        
        return explanations.get(
            top_feature[0],
            f"{top_feature[0]} is the primary risk factor"
        )
    
    async def set_custom_threshold(self, project_id: str, risk_level: str,
                                  threshold: float) -> Dict:
        """Set custom risk thresholds per project"""
        if project_id not in self.custom_thresholds:
            self.custom_thresholds[project_id] = {}
        
        self.custom_thresholds[project_id][risk_level] = threshold
        
        return {
            "project_id": project_id,
            "risk_level": risk_level,
            "threshold": threshold,
            "status": "threshold_updated"
        }
    
    async def detect_anomalies(self, project_id: str) -> Dict:
        """Detect unusual code patterns"""
        files = await self.db.get_files_by_project(project_id)
        
        # Calculate baseline statistics
        risk_scores = [f.get('risk_score', 0) for f in files]
        complexities = [f.get('complexity', 0) for f in files]
        
        if not risk_scores:
            return {"anomalies": []}
        
        mean_risk = np.mean(risk_scores)
        std_risk = np.std(risk_scores)
        mean_complexity = np.mean(complexities)
        std_complexity = np.std(complexities)
        
        anomalies = []
        
        for file in files:
            file_risk = file.get('risk_score', 0)
            file_complexity = file.get('complexity', 0)
            
            # Check if file is anomalous (3 standard deviations)
            if abs(file_risk - mean_risk) > 3 * std_risk:
                anomalies.append({
                    "file": file.get('path'),
                    "type": "risk_anomaly",
                    "risk_score": file_risk,
                    "deviation": abs(file_risk - mean_risk) / std_risk if std_risk > 0 else 0,
                    "message": f"Risk score ({file_risk:.2f}) is unusually {'high' if file_risk > mean_risk else 'low'}"
                })
            
            if abs(file_complexity - mean_complexity) > 3 * std_complexity:
                anomalies.append({
                    "file": file.get('path'),
                    "type": "complexity_anomaly",
                    "complexity": file_complexity,
                    "deviation": abs(file_complexity - mean_complexity) / std_complexity if std_complexity > 0 else 0,
                    "message": f"Complexity ({file_complexity}) is unusually high"
                })
        
        return {
            "project_id": project_id,
            "anomalies_found": len(anomalies),
            "anomalies": anomalies,
            "baseline": {
                "mean_risk": mean_risk,
                "std_risk": std_risk,
                "mean_complexity": mean_complexity
            }
        }
    
    async def learn_from_history(self, project_id: str) -> Dict:
        """Learn patterns from past bugs"""
        scans = await self.db.get_scan_history(project_id, limit=50)
        
        if len(scans) < 5:
            return {"status": "insufficient_data"}
        
        # Analyze patterns in files that had issues
        patterns = {
            "high_risk_patterns": [],
            "common_smells": {},
            "risky_file_types": {}
        }
        
        for scan in scans:
            for file in scan.get('files', []):
                if file.get('risk_score', 0) >= 0.7:
                    # Track file types
                    file_type = file.get('type', 'unknown')
                    patterns["risky_file_types"][file_type] = \
                        patterns["risky_file_types"].get(file_type, 0) + 1
                    
                    # Track common smells
                    for smell in file.get('code_smells', []):
                        smell_type = smell.get('type', 'unknown')
                        patterns["common_smells"][smell_type] = \
                            patterns["common_smells"].get(smell_type, 0) + 1
        
        return {
            "project_id": project_id,
            "scans_analyzed": len(scans),
            "patterns": patterns,
            "status": "learning_complete"
        }
