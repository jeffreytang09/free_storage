## free_storage 

[https://www.google.com/drive/](GoogleDrive) provides up to 15GB of free storage (as of the date of writing). The offical Python API ([`pydrive`](https://pythonhosted.org/PyDrive/index.html)) is a bit tricky to use when you have a nested directory structure. The goal here is to be able to manipulate . If you are using GoogleCloud, S3 or other paid storage services, [cloud-storage-client](https://pypi.org/project/cloud-storage-client/) might be a better for you. As the name suggests, this is really useful at all if you want to stick to something free :) 

To use the library for the first time, you need to follow this [tutorial](https://pythonhosted.org/PyDrive/quickstart.html) to generate `gdrive_credentials.json`. Also you need to define an extra `gdrive_settings.yaml` file.

```bash
# gdrive_credentials.json
{"access_token": XXXX, "client_id": XXXX, "client_secret": XXXX, ...}
```

```bash
# gdrive_settings.yaml
client_config_backend: settings
client_config:
  client_id: XXXX
  client_secret: XXXX

save_credentials: True
save_credentials_backend: file
save_credentials_file: gdrive_credentials.json

get_refresh_token: True

oauth_scope:
  - https://www.googleapis.com/auth/drive
  - https://www.googleapis.com/auth/drive.metadata
```

Below is an example of how the interface is used
```python
from free_storage import GoogleDriveStorage

drive = GoogleDriveStorage(
    setting_file_name="path/to/gdrive_settings.yaml",
    credential_file_name="path/to/gdrive_credentials.json"
)

# Create a folder under root
drive.create_file("directory_name")

# Upload an existing file locally to a remote path
drive.create_file(
    remote_path="directory_name/test.zip",
    local_path="test.zip",
)

# Upload content in memory to a file in remote path
drive.create_file(
    remote_path="directory_name/test.txt",
    content="some string",
)

# Download file
drive.download_file(
    remote_path="directory_name/test.txt",
    local_path="test.txt"
)

# Delete file
drive.delete_file("directory_name/test.txt")
```

TODO:
- For `create_file` method under `GoogleDriveStorage`, allow creating nested levels of directories, instead of just one level down 
- Stream reading large files without downloading the whole file to local