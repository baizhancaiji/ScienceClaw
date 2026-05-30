import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mcp.crypto import decrypt_secret, encrypt_secret, mask_secret  # noqa: E402


class MCPCryptoTests(unittest.TestCase):
    def test_encrypt_decrypt_round_trip(self):
        encrypted = encrypt_secret("secret-token", "test-key")

        self.assertNotEqual("secret-token", encrypted)
        self.assertTrue(encrypted.startswith("v1:"))
        self.assertEqual("secret-token", decrypt_secret(encrypted, "test-key"))

    def test_encrypt_uses_random_nonce(self):
        first = encrypt_secret("secret-token", "test-key")
        second = encrypt_secret("secret-token", "test-key")

        self.assertNotEqual(first, second)
        self.assertEqual("secret-token", decrypt_secret(first, "test-key"))
        self.assertEqual("secret-token", decrypt_secret(second, "test-key"))

    def test_empty_values_are_stable(self):
        self.assertEqual("", encrypt_secret("", "test-key"))
        self.assertEqual("", encrypt_secret(None, "test-key"))
        self.assertEqual("", decrypt_secret("", "test-key"))
        self.assertEqual("", decrypt_secret(None, "test-key"))
        self.assertEqual("", mask_secret(""))
        self.assertEqual("", mask_secret(None))

    def test_missing_key_is_rejected_for_non_empty_values(self):
        with self.assertRaises(ValueError):
            encrypt_secret("secret-token", "")
        with self.assertRaises(ValueError):
            decrypt_secret("v1:invalid", "")

    def test_bad_key_and_bad_ciphertext_are_rejected(self):
        encrypted = encrypt_secret("secret-token", "test-key")

        with self.assertRaises(ValueError):
            decrypt_secret(encrypted, "other-key")
        with self.assertRaises(ValueError):
            decrypt_secret("not-v1-data", "test-key")
        with self.assertRaises(ValueError):
            decrypt_secret("v1:bad-payload", "test-key")

    def test_mask_secret_does_not_expose_short_values(self):
        self.assertEqual("***", mask_secret("abc"))
        self.assertEqual("********oken", mask_secret("secret-token"))


if __name__ == "__main__":
    unittest.main()
