from pathlib import Path
import mimetypes
from concurrent.futures import ThreadPoolExecutor
import structlog

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.uploader.dataclasses.upload_path import UploadPath

logger = structlog.get_logger()

class StorageClient:
    def __init__(self, client: DatacosmosClient):
        self.datacosmos_client = client
        self.base_url = client.config.datacosmos_cloud_storage.as_domain_url()

    def upload_file(self, src: str, dst: str):
        """Uploads a single file to the specified destination path."""
        url = self.base_url.with_suffix(str(dst))
        logger.info(f"Uploading file {src} to {dst}")
        with open(src, "rb") as f:
            response = self.datacosmos_client.put(url, data=f)
        response.raise_for_status()
        logger.info(f"Upload complete for {src}")

    def get_mime_type(self, file_path: str) -> str:
        """Returns the MIME type of a given file based on its extension."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def upload_from_folder(self, src: str, dst: UploadPath, workers: int = 4):
        """Uploads all files from a folder to the destination path in parallel."""
        if Path(dst.path).is_file():
            raise ValueError(f"Destination path should not be a file path {dst}")

        if Path(src).is_file():
            raise ValueError(f"Source path should not be a file path {src}")

        logger.info(f"Uploading folder {src} to {dst} with {workers} workers")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for file in Path(src).rglob("*"):
                if file.is_file():
                    dst = UploadPath(
                        mission=dst.mission,
                        level=dst.level,
                        day=dst.day,
                        month=dst.month,
                        year=dst.year,
                        id=dst.id,
                        path=str(file.relative_to(src)),
                    )
                    futures.append(executor.submit(self.upload_file, str(file), dst))
            for future in futures:
                future.result()

