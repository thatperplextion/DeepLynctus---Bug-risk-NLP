from typing import Dict, Any, List

# Simple in-memory DB adapter for prototyping
class InMemoryDB:
    projects: Dict[str, Dict[str, Any]] = {}
    file_metrics: Dict[str, List[Dict[str, Any]]] = {}
    risks: Dict[str, List[Dict[str, Any]]] = {}
    smells: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def upsert_project(cls, project: Dict[str, Any]):
        cls.projects[project["_id"]] = project

    @classmethod
    def get_project(cls, project_id: str) -> Dict[str, Any] | None:
        return cls.projects.get(project_id)

    @classmethod
    def set_metrics(cls, project_id: str, metrics: List[Dict[str, Any]]):
        cls.file_metrics[project_id] = metrics

    @classmethod
    def get_metrics(cls, project_id: str) -> List[Dict[str, Any]]:
        return cls.file_metrics.get(project_id, [])

    @classmethod
    def set_risks(cls, project_id: str, risks: List[Dict[str, Any]]):
        cls.risks[project_id] = risks

    @classmethod
    def get_risks(cls, project_id: str) -> List[Dict[str, Any]]:
        return cls.risks.get(project_id, [])
