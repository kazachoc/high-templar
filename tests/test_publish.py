import json
from .testapp.app import app
from chimeracub.test import TestCase, Client, MockWebSocket, room_ride, room_car
from greenlet import greenlet

subscribe_ride = {
    'requestId': 'a',
    'type': 'subscribe',
    'room': room_ride,
}
subscribe_car = {
    'requestId': 'b',
    'type': 'subscribe',
    'room': room_car,
}
publish_ride = {
    'requestId': 'a',
    'type': 'publish',
    'data': [{
        'id': 1,
        'driver': 2,
    }]
}


class TestPublish(TestCase):
    def setUp(self):
        self.client = Client(app)

    def test_incoming_trigger_gets_published(self):
        ws1 = MockWebSocket()
        ws1.mock_incoming_message(json.dumps(subscribe_ride))
        ws2 = MockWebSocket()
        ws2.mock_incoming_message(json.dumps(subscribe_ride))
        ws2.mock_incoming_message(json.dumps(subscribe_car))

        # hub = self.client.app.hub
        g1 = greenlet(self.client.open_connection)
        g1.switch(ws1)
        g2 = greenlet(self.client.open_connection)
        g2.switch(ws2)

        # Mock incoming ride trigger
        self.client.flask_test_client.post(
            '/trigger/',
            content_type='application/json',
            data=json.dumps({
                'rooms': [room_ride],
                'data': [{
                    'id': 1,
                    'driver': 2,
                }]
            }))

        # The first outgoing message is the allowed_rooms listing
        # The second one is about the successful subscribe
        # The third is the actual publish
        self.assertEqual(3, len(ws1.outgoing_messages))
        self.assertEqual(json.dumps(publish_ride), ws1.outgoing_messages[2])
        # ws2 has 2 subscribe success events
        self.assertEqual(4, len(ws2.outgoing_messages))
        self.assertEqual(json.dumps(publish_ride), ws2.outgoing_messages[3])

        ws2.close()

        self.client.flask_test_client.post(
            '/trigger/',
            content_type='application/json',
            data=json.dumps({
                'rooms': [room_ride],
                'data': [{
                    'id': 1,
                    'driver': 2,
                }]
            }))

        self.assertEqual(4, len(ws1.outgoing_messages))
        self.assertEqual(json.dumps(publish_ride), ws1.outgoing_messages[3])
