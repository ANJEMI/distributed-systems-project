#!/bin/bash

# Define the paths
CLIENT_1_DOWNLOADS="./src/client/downloads/client_1/*"
CLIENT_2_DOWNLOADS="./src/client/downloads/client_2/*"
CLIENT_1_UPLOADS="./src/client/uploads/client_1/*"
CLIENT_2_UPLOADS="./src/client/uploads/client_2/*"
TRACKER_DATA="./src/tracker/database/tracker_data.json"

# Delete the contents of the client_1 and client_2 folders
echo "Deleting contents of client_1 and client_2 in downloads..."
rm -rf $CLIENT_1_DOWNLOADS
rm -rf $CLIENT_2_DOWNLOADS
rm -rf $CLIENT_1_UPLOADS
rm -rf $CLIENT_2_UPLOADS

# Delete the tracker_data.json file
if [ -f "$TRACKER_DATA" ]; then
    echo '{
    "torrents": []
}' > "$TRACKER_DATA"
else
    echo "tracker_data.json not found."
fi

echo "Cleanup completed."
