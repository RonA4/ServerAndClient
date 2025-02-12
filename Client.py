import socket
import time

SERVER_IP = 'localhost' # The IP address of the server (localhost for local testing).
PORT = 12348  # The port number on which the server listens for connections.
BUFFER_SIZE = 1024  # The size of the buffer for sending/receiving data (in bytes).
FILE_NAME = "input.txt"  # The name of the file containing input data for the program.

def split_into_windows(packets, window_size):
    """
    Splits a list of packets into windows of a specified size.
    Arguments:
        packets (list): A list of packets to be split.
        window_size (int): The number of packets in each window.
    Returns:
        list: A list of windows, where each window is a sublist containing a subset of the packets.
    """
    windows = []
    total_packets = len(packets)
    for i in range(0, total_packets, window_size):
        window = packets[i:i + window_size]
        windows.append(window)
    return windows
def send_packets_in_window(client_socket, packets, recieved_ack_packets, current_start_windows_index, window_size):
    """
    Sends packets in a specific window and checks whether any of the packets have already been acknowledged.
    Arguments:
        client_socket (socket): The socket to send the packets over.
        packets (list): A list of packets to send.
        recieved_ack_packets (list): A list tracking whether each packet has been acknowledged.
        current_start_windows_index (int): The index from where to start sending packets.
        window_size (int): The number of packets to send in one window.
    """
    for i in range(current_start_windows_index, min(current_start_windows_index + int(window_size), len(packets))):
        if not recieved_ack_packets[i]:  # Only send unacknowledged packets
            print(f"Sending packet {i}: {packets[i]}")
            client_socket.send(packets[i].encode())  # Send the packet

def start_receiving_acks_with_timeout(client_socket, time_out, received_ack_packets, max_size, window_size):
    """
    Waits for acknowledgment messages from the server within a specified timeout period.
    Arguments:
        client_socket (socket): The socket to receive ACKs from.
        time_out (float): The timeout period in seconds.
        received_ack_packets (list): A list that tracks which packets have been acknowledged.
        max_size (int): The maximum size for an ACK message.
        window_size (int): The number of ACKs to wait for in one window.
    Returns:
        None: This function updates the acknowledgment status and handles timeouts.
    """
    start_time = time.time()
    remaining_time_out = time_out
    number_of_received_packs = 0
    while remaining_time_out > 0 and number_of_received_packs < window_size:
        try:
            elapsed_time = time.time() - start_time
            remaining_time_out = time_out - elapsed_time
            if remaining_time_out <= 0:
                print("General timeout reached.")
                break

            client_socket.settimeout(remaining_time_out)
            ack_from_server = client_socket.recv(max_size).decode()
            stripped_data = ack_from_server.rstrip('#')
            ack_number = int(stripped_data[3:])
            for j in range(ack_number + 1):
                if not received_ack_packets[j]:
                    number_of_received_packs += 1
                    print(f"Received ACK{ack_number}")
                received_ack_packets[j] = True
        except socket.timeout:
            print("Timeout reached while waiting for messages.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    if remaining_time_out <= 0:
        print(f"timeout is occurred")

def send_in_sliding_window_method(client_socket, packets, window_size, time_out, max_size):
    """
    Implements the sliding window protocol to send packets and wait for their acknowledgments.
    Arguments:
        client_socket (socket): The socket to send and receive data over.
        packets (list): A list of packets to be sent.
        window_size (int): The number of packets to send in one window.
        time_out (float): The timeout period in seconds.
        max_size (int): The maximum size for an ACK message.
    Returns:
        None: This function handles the transmission and acknowledgment of packets.
    """
    packets_size = len(packets)
    received_ack_packets = [False] * packets_size
    current_start_windows_index = 0

    while current_start_windows_index < packets_size:
        send_packets_in_window(client_socket, packets, received_ack_packets, current_start_windows_index, window_size)
        start_receiving_acks_with_timeout(client_socket, time_out, received_ack_packets, max_size, window_size)
        last_window_size = current_start_windows_index
        while current_start_windows_index < packets_size and received_ack_packets[current_start_windows_index]:
            current_start_windows_index += 1
        if last_window_size != current_start_windows_index:
            print(f"window is move to index {current_start_windows_index}")

def split_message_to_packets_by_max_size(message, max_size):
    """
    Splits a message into packets, where each packet does not exceed a specified maximum size.
    Arguments:
        message (str): The message to be split into packets.
        max_size (int): The maximum size allowed for each packet.
    Returns:
        list: A list of packets, each containing a portion of the original message, prefixed with its index.
    """
    encoded_message = message.encode()
    results_packets = []
    start_index = 0
    packet_index = 0

    while start_index < len(encoded_message):
        prefix_packet = f"M{packet_index}:"
        available_size = max_size - len(prefix_packet.encode("utf-8"))
        if available_size <= 0:
            print("No available size")
            break
        chunk = encoded_message[start_index: start_index + available_size]
        results_packets.append(f"{prefix_packet}{chunk.decode()}")
        start_index += len(chunk)
        packet_index += 1

    return results_packets

def read_input_from_file():
    """
       Reads message details from a file and extracts relevant information.
       The function opens a predefined file (FILE_NAME) in read mode and processes its content
       to extract the following details:
       - Message: Extracted from a line starting with "message:" and stripped of quotes.
       - Window size: Extracted from a line starting with "window_size:" and converted to an integer.
       - Timeout: Extracted from a line starting with "timeout:" and converted to an integer.
    """
    with open(FILE_NAME, 'r') as file:
        with open(FILE_NAME, 'r') as file:
            lines = file.readlines()
            message = ""
            window_size = 0
            timeout = 0
            for line in lines:
                if "message:" in line:
                    message = line.split(":")[1].strip().strip('"')
                elif "window_size:" in line:
                    window_size = int(line.split(":")[1].strip())
                elif "timeout:" in line:
                    timeout = int(line.split(":")[1].strip())
            return message, window_size, timeout

def read_input_from_user():
    """
    Prompts the user to enter message details and returns the input values.

    The function collects the following information from the user:
    - A message string.
    - The window size (number of messages) as an integer.
    - The timeout value (in seconds) as an integer.
    """
    message = input("Enter the message: ")
    window_size = int(input("Enter the window size (number of messages): "))
    timeout = int(input("Enter the timeout (in seconds): "))
    return message, window_size, timeout


def get_client_message():
    """
     Displays a menu to the client to choose an input method and returns the corresponding request message.
        This function prompts the client with two options:
        1. To provide data manually via input.
        2. To provide data via a file.
            - If the client enters "1",  returns a message to request the data via input.
            - If the client enters "2",  returns a message to request the data from file.
    """
    print("Choose one option:")
    print("1. Please provide data from Input")
    print("2. Please provide data from File")
    choice = input("Enter your choice (1 or 2): ").strip()
    if choice == "1":
        return "Please provide data from Input"
    elif choice == "2":
        return "Please provide data from File"

def start_client():
    """
       Initiates the client-side communication with the server.
       1. Establishes a TCP connection to the server.
       2. Sends the client's message to the server.
       3. Receives the maximum allowed message size from the server.
       4. Determines the input source (file or user input) and reads the message.
       5. Splits the message into packets based on the maximum size.
       6. Sends the packets using the sliding window technique, handling timeouts and acknowledgments.
       7. Closes the connection after all messages are sent and acknowledged.
       """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((SERVER_IP, PORT))
        print(f"Connected to the server at {SERVER_IP}:{PORT}")

        # Decide File Or Input #
        client_message = get_client_message()
        client_socket.sendall(client_message.encode('utf-8'))
        max_size = int(client_socket.recv(BUFFER_SIZE).decode('utf-8').strip())

        print(f"Received maximum message size: {max_size} bytes")
        if "File" in client_message:
            message, window_size, timeout = read_input_from_file()
        else:
            message, window_size, timeout = read_input_from_user()
        # End  Decide File Or Input #
        packets = split_message_to_packets_by_max_size(message, max_size)
        send_in_sliding_window_method(client_socket, packets, window_size, timeout, max_size)
        print(f"Finishing sending all messages + gets all acks back")
        client_socket.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    start_client()
