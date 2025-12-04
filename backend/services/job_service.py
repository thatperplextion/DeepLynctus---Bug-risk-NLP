from datetime import datetime

class JobService:
    @staticmethod
    async def start_scan(project_id: str, options: dict) -> str:
        # TODO: enqueue background job
        return datetime.utcnow().isoformat()
