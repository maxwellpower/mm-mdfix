# Mattermost Message Formatter

This project provides a Dockerized Python script to format code blocks in Mattermost messages stored in a PostgreSQL database, ensuring code blocks are properly formatted with newlines, making them more readable.

## Prerequisites

- Docker
- Access to your Mattermost PostgreSQL database

## Usage

### 1. Configuration

Copy the `default.env` file in the root directory of this project to `.env` and set your variables:

```
DB_HOST=your_host
DB_PORT=your_port
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_dbname
CHANNEL_ID=optional_channel_id
COMMIT_MODE=false
```

Replace the placeholders (`your_host`, `your_port`, etc.) with your actual database connection details. The `CHANNEL_ID` is optional; if provided, only messages from that channel will be processed. By default, the script runs in test mode (`COMMIT_MODE=false`). If you want to commit changes to the database, set `COMMIT_MODE=true`.

There are additional debug messages available by adding `DEBUG=true` to your environment.

### 2. Run the Docker Container

```bash
docker run --env-file .env ghcr.io/maxwellpower/mm-mdfix
```

#### Using Command Line

If you prefer to provide the environment variables directly:

```bash
docker run -e DB_HOST=your_host -e DB_PORT=your_port -e DB_USER=your_user -e DB_PASSWORD=your_password -e DB_NAME=your_dbname -e CHANNEL_ID=optional_channel_id -e COMMIT_MODE=false ghcr.io/maxwellpower/mm-mdfix
```

Replace the placeholders with your actual database connection details.

## Notes

- The script processes messages containing code blocks (enclosed in triple backticks ```).
- Messages with a language specifier immediately after the opening ticks (e.g., ```php) remain unchanged.
- Only messages from posts that haven't been marked as deleted (where `deleteat` is `0`) are processed.
- By default, the script runs in test mode, allowing you to review potential changes without modifying the database. To apply changes, set `COMMIT_MODE=true`.
