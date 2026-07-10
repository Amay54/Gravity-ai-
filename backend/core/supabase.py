from loguru import logger
from supabase import Client, create_client

from backend.core.config import settings


class SupabaseWrapper:
    """
    Gateway client wrapping the Supabase Cloud SDK, providing database and storage operations.
    """

    def __init__(self) -> None:
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_ANON_KEY
        self.client: Client | None = None
        self._is_mock = False

        self.initialize()

    def initialize(self) -> None:
        """
        Connects to Supabase Cloud or initializes mock drivers in local dev.
        """
        # If url is default mock or missing, activate sandbox mock driver mode
        if self.url == "https://mock.supabase.co" or not self.key or self.key == "mock-anon-key":
            logger.warning(
                "[SupabaseWrapper] Running under local developer sandbox mock mode. Actions will use in-memory fallbacks."
            )
            self._is_mock = True
            self.client = None
            return

        try:
            self.client = create_client(self.url, self.key)
            self._is_mock = False
            logger.info(f"[SupabaseWrapper] Successfully connected to Supabase Cloud: {self.url}")
        except Exception as e:
            logger.error(
                f"[SupabaseWrapper] Connection failed: {e}. Falling back to mock driver mode."
            )
            self._is_mock = True
            self.client = None

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    def get_client(self) -> Client:
        if self._is_mock or self.client is None:
            raise RuntimeError(
                "Supabase client is running in mock mode and cannot handle real Cloud transactions."
            )
        return self.client

    # Storage bucket helper methods
    def upload_file(
        self, bucket: str, path: str, file_data: bytes, content_type: str = "application/pdf"
    ) -> str:
        """
        Uploads report binaries to Supabase Storage bucket and returns signed url or public path.
        """
        if self._is_mock:
            mock_url = f"https://mock.supabase.co/storage/v1/object/public/{bucket}/{path}"
            logger.info(
                f"[MOCK STORAGE] Uploaded file of type {content_type} to '{bucket}/{path}' -> URL: {mock_url}"
            )
            return mock_url

        try:
            client = self.get_client()
            # Upload file
            client.storage.from_(bucket).upload(
                path=path,
                file=file_data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            # Fetch signed download url (valid for 1 hour)
            signed_url_res = client.storage.from_(bucket).create_signed_url(path, 3600)
            return (
                signed_url_res.get("signedURL")
                or signed_url_res.get("signedUrl")
                or f"{self.url}/storage/v1/object/public/{bucket}/{path}"
            )
        except Exception as e:
            logger.error(f"[SupabaseWrapper] Storage upload failed: {e}")
            return f"/storage/fallback/{path}"

    def get_signed_url(self, bucket: str, path: str) -> str:
        """
        Returns a signed URL for download authorization.
        """
        if self._is_mock:
            return f"https://mock.supabase.co/storage/v1/object/public/{bucket}/{path}?token=mock-token"

        try:
            client = self.get_client()
            signed_url_res = client.get_client().storage.from_(bucket).create_signed_url(path, 3600)
            return signed_url_res.get("signedURL") or signed_url_res.get("signedUrl") or ""
        except Exception as e:
            logger.error(f"[SupabaseWrapper] Failed to generate signed URL: {e}")
            return ""


# Global Supabase client wrapper singleton instance
supabase_wrapper = SupabaseWrapper()
