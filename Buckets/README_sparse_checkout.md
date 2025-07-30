# Sparse Checkout Feature

The `setup_and_run.py` script now supports cloning only specific folders from a repository using Git's sparse-checkout feature. This is useful when you only need a subfolder from a large repository.

## Usage

### Clone entire repository (default behavior):

```bash
python3 setup_and_run.py --repo https://github.com/owner/repo --app-module main:app
```

### Clone only a specific folder:

```bash
python3 setup_and_run.py --repo https://github.com/owner/repo --repo-folder SubFolder --app-module main:app
```

## Examples

### Example 1: Clone only the "Buckets" folder from UWS-tools

```bash
python3 setup_and_run.py \
  --repo https://github.com/Unicorn-Web-Services/UWS-tools \
  --repo-folder Buckets \
  --app-module buckets:app \
  --container-name my-buckets-app
```

### Example 2: Clone only the "api" folder from a hypothetical repo

```bash
python3 setup_and_run.py \
  --repo https://github.com/example/microservices \
  --repo-folder api \
  --app-module main:app \
  --container-name api-service
```

### Example 3: Clone a nested folder

```bash
python3 setup_and_run.py \
  --repo https://github.com/example/monorepo \
  --repo-folder services/user-service \
  --app-module app:application \
  --container-name user-service
```

## How it works

1. **Sparse Clone**: Uses `git clone --no-checkout` to clone the repository metadata
2. **Configure Sparse-Checkout**: Enables sparse-checkout and specifies which folder to include
3. **Selective Checkout**: Checks out only the specified folder
4. **Move to Target**: Moves the specified folder to the project directory
5. **Cleanup**: Removes temporary files

## Benefits

- **Faster cloning**: Only downloads the files you need
- **Less disk space**: Doesn't store unnecessary files
- **Clean setup**: Gets only the relevant code for your FastAPI project
- **Flexible**: Works with any folder structure in the repository

## Parameters

- `--repo`: The Git repository URL to clone from
- `--repo-folder`: The specific folder within the repository to clone (optional)
- `--project-dir`: Where to place the cloned folder (optional)
- `--app-module`: The FastAPI app module path (e.g., "main:app")
- `--container-name`: Docker container name
- `--port`: Starting port to search for available ports

If `--repo-folder` is not specified, the entire repository will be cloned (default behavior).
