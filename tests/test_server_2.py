# import unittest

# from server import app
# import json

# class BasicTestCase(unittest.TestCase):
#     def test_home(self):
#       tester = app.test_client(self)
#       response = tester.post(
#         '/publish',
#         data=json.dumps(
#           {
#             'format':'edf',
#             'stream-identifier': 'test-id',
#             'description': 'this is a test stream',
#             'tags': ['tag1', 'tag2']
#           }
#         ),
#         content_type='application/json'
#       )
#       self.assertEqual(response.status_code, 200)
      
#       data = json.loads(response.get_data(as_text=True))

#       self.assertEqual(response.data, b'Hello World!')
      
#     # def test_other(self):
#     #     tester = app.test_client(self)
#     #     response = tester.get('a', content_type='html/text')
#     #     self.assertEqual(response.status_code, 404)
#     #     self.assertTrue(b'does not exist' in response.data)
        
# if __name__ == '__main__':
#     unittest.main()