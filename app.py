import asyncio
import websockets

# Define the WebSocket server endpoint
async def handle_client(websocket):
    try:
        while True:
            # Wait for a message from the client
            client_message = await websocket.recv()
            print(f"Received message from client: {client_message}")

            # Send a response back to the client
            server_message = f"Server says: Hello, you sent '{client_message}'"
            await websocket.send(server_message)
            print(f"Sent message to client: {server_message}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")


# Main function to start the WebSocket server
async def main():
    # Set up the WebSocket server
    await websockets.serve(handle_client, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765/say_hello")

    # Keep the server running
    await asyncio.Future()  # Run forever


# Run the WebSocket server
if __name__ == "__main__":
    asyncio.run(main())
