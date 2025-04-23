from unittest import TestCase, mock
from src.set_cover import validate_file_exists

TEST_FILE_NAME = "test-file.txt"

class TestSetCover(TestCase):
    @mock.patch('src.set_cover.Path.exists')
    def test_validate_file_exists_does_not_raise_exception_if_file_exists(self, mock_exists):
        mock_exists.return_value = True
        validate_file_exists(TEST_FILE_NAME)
        mock_exists.assert_called_once()

    @mock.patch('src.set_cover.Path.exists')
    def test_validate_file_exists_raises_exception_if_file_does_not_exist(self, mock_exists):
        mock_exists.return_value = False

        with self.assertRaises(Exception) as context:
            validate_file_exists(TEST_FILE_NAME)

        mock_exists.assert_called_once()
        self.assertEqual(f"No such file {TEST_FILE_NAME}", str(context.exception))
