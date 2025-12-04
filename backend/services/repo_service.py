import uuid
from typing import Any
from fastapi import UploadFile

class RepoService:
    @staticmethod
    async def queue_project(req: Any) -> str:
        # TODO: persist to DB; for now return id
        return str(uuid.uuid4())

    @staticmethod
    async def queue_zip(file: UploadFile) -> str:
        # TODO: save file securely and return project id
        _ = file.filename
        return str(uuid.uuid4())
