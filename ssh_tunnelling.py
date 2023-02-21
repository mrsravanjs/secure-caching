import sshtunnel
from flask import Flask, request
from pymemcache.client.base import Client

app = Flask(__name__)


def create_tunnel():
    return sshtunnel.SSHTunnelForwarder(
        ('127.0.0.1', 22),
        ssh_username='remote_username',
        ssh_password='remote_password',
        ssh_private_key='path_to_secret',
        remote_bind_address=('127.0.0.1', 11211)
    )


class ConnectionPool:
    def __init__(self):
        self.tunnel = create_tunnel()
        self.tunnel.start()
        self.clients = []

    def get_client(self):
        if len(self.clients) > 0:
            return self.clients.pop()
        else:
            return Client(('127.0.0.1', self.tunnel.local_bind_port))

    def release_client(self, client):
        self.clients.append(client)

    def cleanup(self):
        self.tunnel.stop()


pool = ConnectionPool()


@app.route('/store_data', methods=['POST'])
def store_data():
    client = pool.get_client()
    data = request.get_json()
    client.set(data['name'], data, expire=120)
    pool.release_client(client)
    return {"INSERTION_STATUS": "OK"}


if __name__ == "__main__":
    app.run(port=5000)

