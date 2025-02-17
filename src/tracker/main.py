from tracker.tracker import Tracker
import socket

def get_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


tracker = Tracker()
tracker.start_tracker(host=get_ip())