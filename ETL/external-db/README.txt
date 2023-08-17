This creates a volatile database (changes will not be persistent).

To start: 

# Build image
docker build -t storage_database .
# Run container
docker run -d -p 5432:5432 --name storage_database storage_database
