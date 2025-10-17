#!/bin/sh

# Set default user ID and group ID
USER_ID=${PUID:-1000}
GROUP_ID=${PGID:-1000}

echo "Starting with UID: $USER_ID, GID: $GROUP_ID"

# Change the appuser's group and user ID to match the host
groupmod -g $GROUP_ID appuser
usermod -u $USER_ID -g $GROUP_ID appuser

# Change ownership of relevant directories
chown -R appuser:appuser /app

# Drop root privileges and execute the main command as appuser
exec su-exec appuser "$@"