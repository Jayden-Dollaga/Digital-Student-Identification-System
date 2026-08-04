import unittest
from types import SimpleNamespace
from unittest.mock import patch


class TestVidPidNormalization(unittest.TestCase):
    def test_get_default_com_port_prefers_known_vidpid(self):
        # Create a fake port object with known VID:PID (1a86:7523)
        fake_port = SimpleNamespace(device='COM_TEST', description='USB Serial CP210x', vid=0x1a86, pid=0x7523)

        import config

        with patch.object(config, 'list_ports') as mocked_list_ports:
            mocked_list_ports.comports.return_value = [fake_port]
            result = config.get_default_com_port('COM_FALLBACK')
            # Should return the device name from the discovered port
            self.assertEqual(result, 'COM_TEST')

    def test_device_discovery_score_recognizes_vidpid(self):
        fake_port = SimpleNamespace(device='COM_A', description='USB Serial', vid=0x10c4, pid=0xea60)
        import core.device_discovery as dd

        # Score should be positive and include known VID:PID bonus
        score = dd._score_port_info(fake_port)
        self.assertGreaterEqual(score, 140)


if __name__ == '__main__':
    unittest.main()
