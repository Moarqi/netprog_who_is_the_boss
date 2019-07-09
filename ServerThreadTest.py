from unittest import TestCase, main
from unittest.mock import patch, PropertyMock
from ServerThread import ServerThread
import arrow as arr


class ServerThreadTest(TestCase):

    def setUp(self):
        self.thread = ServerThread(None, 1000, 100)

    def test_process_recieved_data(self):
        ip = "1.1.1.1"
        data = "[INFO] 1002 12345"

        expected_server_dict = {
            f"{ip}": {
                "1002": {
                    "score": 12345.0,
                    "updated": True
                }
            }
        }

        self.thread.process_recieved_data(data, ip)
        self.assertDictEqual(
            self.thread.running_servers,
            expected_server_dict
        )

        data = "[INFO] 1008 11"

        expected_server_dict = {
            f"{ip}": {
                "1002": {
                    "score": 12345.0,
                    "updated": True
                },
                "1008": {
                    "score": 11,
                    "updated": True
                }
            }
        }

        self.thread.process_recieved_data(data, ip)
        self.assertDictEqual(
            self.thread.running_servers,
            expected_server_dict
        )

        ip =  "192.168.0.5"
        data = "[INFO] 1002 12345"

        expected_server_dict[ip] = {
            "1002": {
                "score": 12345.0,
                "updated": True
            }
        }

        self.thread.process_recieved_data(data, ip)
        self.assertDictEqual(
            self.thread.running_servers,
            expected_server_dict
        )


    def test_handle_server_list(self):
        self.thread.update_required = True
        self.thread.slave_script_running = False
        self.thread.master_script_running = True
        self.thread.running_servers = {
            "127.0.0.1": {
                "1004": {
                    "score": 1.0,
                    "updated": True
                }
            },
            "192.168.0.5": {
                "1002": {
                    "score": 12345.0,
                    "updated": True
                }
            }
        }

        self.thread.handle_server_list()

        self.assertEqual(self.thread.slave_script_running, True)
        self.assertEqual(self.thread.master_script_running, False)


    def test_handle_server_list_edge_case(self):
        self.thread.update_required = True
        self.thread.slave_script_running = False
        self.thread.master_script_running = True
        self.thread.running_servers = {
            "127.0.0.1": {
                "1004": {
                    "score": 100.0,
                    "updated": True
                }
            },
            "192.168.0.5": {
                "1002": {
                    "score": 100.0,
                    "updated": True
                }
            }
        }

        # mock arrow now to not update score with runtime
        current_time = arr.now()
        with patch('arrow.now') as mock_arr_now:
            mock_arr_now.return_value = current_time
            self.thread.handle_server_list()

        self.assertEqual(self.thread.slave_script_running, False)
        self.assertEqual(self.thread.master_script_running, True)


    def tearDown(self):
        self.thread.kill_all_child_processes()
        return super().tearDown()


if __name__ == '__main__':
    main()


