from unittest import TestCase, mock

from src.set_cover import validate_file_is_regular

TEST_FILE_NAME = "test-file.txt"


class TestSetCover(TestCase):
    @mock.patch("src.set_cover.Path.is_file")
    def test_validate_file_is_regular_does_not_raise_exception_if_file(self, mock_is_file):
        mock_is_file.return_value = True
        validate_file_is_regular(TEST_FILE_NAME)
        mock_is_file.assert_called_once()

    @mock.patch("src.set_cover.Path.is_file")
    def test_validate_file_is_regular_raises_exception_if_not_file(self, mock_is_file):
        mock_is_file.return_value = False

        with self.assertRaises(Exception) as context:
            validate_file_is_regular(TEST_FILE_NAME)

        mock_is_file.assert_called_once()
        self.assertEqual(f"{TEST_FILE_NAME} not found or not a regular file.", str(context.exception))
