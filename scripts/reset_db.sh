#!/bin/bash
# This script will reset the database of the Vivacampo application.
# Warning: This will permanently delete all data in the database.

echo "Stopping services..."
docker-compose down

echo "Removing database volume..."
docker volume rm vivacampo_dbdata

echo "Starting services..."
docker-compose up -d --build

echo "Database has been reset. It might take a few minutes for the services to be fully available."
