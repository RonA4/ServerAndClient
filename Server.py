import socket

PORT = 12348 # The port number on which the server will listen for incoming connections
SERVER_ADDRESS = ('', PORT) # The server's address, set to listen on all available network interfaces
MAX_CLIENTS = 1 # The maximum number of simultaneous clients the server will accept
FILE_NAME = "input.txt"  # The name of the file that will be used or accessed by the server


def handle_max_size_from_input():
    """
        Prompts the user to input the maximum allowed message size in bytes.
        The function waits for the user to input a value, converts the input to an integer,
        and returns it as the maximum message size.
        """
    max_size = int(input("Enter the maximum message size (in bytes): "))
    return max_size


def handle_max_size_from_file():
    """
       Reads the maximum allowed message size from a file.
       The function opens the specified file (defined by the global `FILE_NAME`),
       reads its lines, and searches for the line containing the "maximum_msg_size:" keyword.
       It then extracts and returns the value following the colon as the maximum message size.
       """
    with open(FILE_NAME, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if "maximum_msg_size:" in line:
                return line.split(":")[1].strip()

def get_and_handle_first_max_size_message(client_message):
    """
       Handles the request for the maximum message size based on the client's message.
       The function checks the provided `client_message` and calls either
       `handle_max_size_from_input` or `handle_max_size_from_file` accordingly.
       - If the message is "Please provide data from Input", it prompts the user for input.
       - If the message is "Please provide data from File", it reads the size from a file.
       """
    if client_message == "Please provide data from Input":
        return handle_max_size_from_input()
    elif client_message == "Please provide data from File":
        return handle_max_size_from_file()
def extract(decoded_msg):
    """
     Extracts the packet number and message content from a decoded message.
     The function splits the input message into two parts:
     1. The packet identifier which is used to determine the packet number.
     2. The message content following the  (":").
     """
    packet_identifier, message_content = decoded_msg.split(":", 1)
    packet_number = int(packet_identifier[1:])
    return packet_number, message_content

def handle_client(client_socket):
    """
    Handles the communication with a connected client.
        The function receives a message from the client to determine the maximum allowed
        message size. It then continuously receives packets from the client, processes
        them in order, and sends back acknowledgment (ACK) messages. If packets arrive
        out of order, the server waits for the expected packet.
        Steps:
            1. Receive and process client message to get the maximum message size.
            2. Continuously receive packets from the client.
            3. Extract packet number and message content.
            4. Store and reassemble packets in order.
            5. Send acknowledgment (ACK) messages back to the client
        """
    try:
        client_message = client_socket.recv(1024).decode('utf-8').strip()
        max_size = get_and_handle_first_max_size_message(client_message)
        max_size_number = int(max_size)
        client_socket.sendall(f"{max_size}".encode('utf-8'))
        print(f"Sending back maximum message size: {max_size}")
        packets_received = []
        packet_expected_from_client = 0
        while True:
            msg_from_client = client_socket.recv(max_size_number)
            decoded_msg = msg_from_client.decode()
            if not decoded_msg.strip():
                print("Client is finished , Closing socket")
                break
            print(f"Server recived message - {decoded_msg}")
            packet_number, message_content = extract(decoded_msg)

            if packet_number >= len(packets_received):
                packets_received.extend([None] * (packet_number - len(packets_received) + 1))

            if packets_received[packet_number] is None:
                packets_received[packet_number] = message_content

            if packet_number == packet_expected_from_client:
                print(f"Received expected packet {packet_number}")
                packet_expected_from_client += 1
                while packet_expected_from_client < len(packets_received) and packets_received[
                    packet_expected_from_client] is not None:
                    packet_expected_from_client += 1
            else:
                print(
                    f"Out-of-order packet {packet_number} received, still waiting for packet {packet_expected_from_client}")

            ack_message = f"ACK{packet_expected_from_client - 1}"
            ack_message = ack_message.ljust(max_size_number, '#')
            print(f"Sending ack message {ack_message}")
            client_socket.send(ack_message.encode())
    except Exception as e:
        print(f"Error handling client: {e}")


def start_server():
    """
       Starts the server, listens for incoming client connections, and processes client requests.
       The function creates a server socket, binds it to the specified address, and listens for incoming
       connections. When a client connects, it handles the client's request by calling the `handle_client` function.
       The server continuously waits for new connections and processes them until an error occurs or the server is shut down.
       Steps:
           1. Create and bind the server socket to the specified address.
           2. Wait for a client connection.
           3. Accept the client connection and handle it.
           4. Close the client socket and wait for the next client.
       """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(SERVER_ADDRESS)
        print(f"Server started and listening on ${SERVER_ADDRESS}")
        server_socket.listen(MAX_CLIENTS)

        while True:
            print("Waiting for a client to connect...")
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            handle_client(client_socket)
            client_socket.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()
        print("Server shut down.")


if __name__ == "__main__":
    start_server()
