from unittest import TestCase, main
from ServerThread import ServerThread


class ServerThreadTest(TestCase):

    def setUp(self):
        self.thread = ServerThread(None, 1000, 100)

    def test_process_recieved_data(self):
        data = "[INFO] 1002 12345"

        expected_server_dict = {
            "1002": {
                "score": 12345.0,
                "updated": True
            }
        }

        self.thread.process_recieved_data(data)

        self.assertDictEqual(
            self.thread.running_servers,
            expected_server_dict
        )


    def test_handle_server_list(self):
        self.thread.update_required = True
        self.thread.slave_script_running = False
        self.thread.master_script_running = True
        self.thread.running_servers = {
            "1002": {
                "score": 12345.0,
                "updated": True
            },
            "1004": {
                "score": 1.0,
                "updated": True
            }
        }

        self.thread.handle_server_list()

        self.assertEqual(self.thread.slave_script_running, True)
        self.assertEqual(self.thread.master_script_running, False)


    def tearDown(self):
        self.thread.kill_all_child_processes()
        return super().tearDown()


if __name__ == '__main__':
    main()


