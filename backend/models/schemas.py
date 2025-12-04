from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class Project(BaseModel):
    id: str = Field(alias="_id")
    name: str
    source_type: str
    source_ref: str
    languages: List[str] = []
    status: str = "queued"

class FileMetric(BaseModel):
    id: str = Field(alias="_id")
    project_id: str
    path: str
    language: str
    loc: int
    avg_fn_len: float
    cyclomatic_avg: float
    cyclomatic_max: int
    nesting_max: int
    dup_ratio: float
    comment_ratio: float
    fn_count: int

class CodeSmell(BaseModel):
    id: str = Field(alias="_id")
    project_id: str
    path: str
    smell_type: str
    severity: int
    message: str
    start_line: int
    end_line: int

class RiskScore(BaseModel):
    id: str = Field(alias="_id")
    project_id: str
    path: str
    model_version: str
    proba: float
    risk_score: int
    tier: str
    top_features: List[Dict]
