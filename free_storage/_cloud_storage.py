from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TextIO, Type


class CloudStorage(ABC):
    def __init__(self, retry_limit: int, api_error: Type[IOError]) -> None:
        self._drive = None
        self._api_error = api_error
        self.retry_limit = retry_limit

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def reconnect(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def list_files(self, remote_path: str) -> List[str]:
        pass

    @abstractmethod
    def path_exists(self, remote_path: str) -> Optional[str]:
        """
        Checks if path exists and if so return path identifier,
        otherwise return empty str
        """
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def read_file(self, remote_path: str) -> TextIO:
        pass

    @abstractmethod
    def create_file(
        self,
        remote_path: str,
        content: Optional[str] = None,
        local_path: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    def delete_file(self, remote_path: str):
        pass

    def _run_command(
        self, command: Callable, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        result = None
        success = False
        for i in range(self.retry_limit):
            try:
                result = command() if params is None else command(**params)
                success = True
            except self._api_error:
                continue
            break
        if success:
            return result
        else:
            raise self._api_error
