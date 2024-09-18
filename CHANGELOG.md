# Changes

## 1.0.1 (2024-07-10)


### Bug fixes

- Fix broken import of logs in the reader due to incorrect path.
- Atomic logging of artifacts to avoid corrupted object when code is interupted unexpectedly.
- Warning when using the version manager: relative paths in the config are wrt to the backup directory. To avoid this behavior use an absolute path.
- Removing scheduler from default mlxp config.


