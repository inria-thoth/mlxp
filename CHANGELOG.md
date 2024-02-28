# Changes

## 1.0.0 (2024-02-28)

### Features

- Add new methods such as `filter`, `apply`, `map`, `transform` and `select` in a new `DataFrame` object to replicate some functionalities of `pandas` acting on frames containing lazily loaded data.
- Add references to saved artifacts in `DataFrame` using dedicated columns.
- Automatically load referenced artifacts in `DataFrame` using dedicated loaders from artifacts.

### API Change

- Revamp `Artifact` to allow users to log custom objects by specifying new types using `register_artifact_type`.


## 0.2.1 (2024-02-27)

### Bug fixes

- Fix broken `mlxpsub` command due to incorrect import in `setup.py`

## 0.2.0 (2024-02-14)

### Features

- Adding `mlxpsub` command for easy submission to a job scheduler.
- Simplifying the interactive mode. 
