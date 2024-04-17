# Developer Notes

These are notes to help me remember how to do things when I come back to this project in the future.

## Install

  ```bash
  pip install -r requirements.txt
  pip install -r requirements_dev.txt
  pip install -e .
  ```

## Run Tests

  ```bash
  pytest
  ```

## Build

  ```bash
  python -m build
  ```

## Publish

  ```bash
  twine upload dist/*.tar.gz dist/*.whl
  ```
