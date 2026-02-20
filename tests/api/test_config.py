import unittest

from apps.api.config import APIServerConfig, load_api_server_config_from_env


class APIServerConfigTest(unittest.TestCase):
    def test_defaults_when_env_missing(self):
        config = load_api_server_config_from_env({})
        self.assertEqual(config, APIServerConfig())

    def test_parses_valid_env_values(self):
        config = load_api_server_config_from_env(
            {
                "TPP_API_HOST": "0.0.0.0",
                "TPP_API_PORT": "9001",
                "TPP_API_CORS_ENABLED": "false",
                "TPP_API_CORS_ALLOWED_ORIGINS": "https://app.example.com, https://admin.example.com",
                "TPP_API_LOG_LEVEL": "info",
            }
        )
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 9001)
        self.assertEqual(config.cors_enabled, False)
        self.assertEqual(
            config.cors_allowed_origins,
            ("https://app.example.com", "https://admin.example.com"),
        )
        self.assertEqual(config.log_level, "INFO")

    def test_invalid_values_fall_back_to_defaults(self):
        config = load_api_server_config_from_env(
            {
                "TPP_API_PORT": "99999",
                "TPP_API_CORS_ENABLED": "not-a-bool",
                "TPP_API_LOG_LEVEL": "verbose",
            }
        )
        self.assertEqual(config.port, 8000)
        self.assertEqual(config.cors_enabled, True)
        self.assertEqual(config.log_level, "SILENT")


if __name__ == "__main__":
    unittest.main()
