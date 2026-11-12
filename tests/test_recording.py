import unittest

from pathlib import Path
from clipmint_windows.recording import gdigrab_args


class RecordingTests(unittest.TestCase):
    def test_windows_gdigrab_and_even_dimensions(self):
        args = gdigrab_args("ffmpeg.exe", Path("test.mp4"), -100, 220, 651, 481)
        self.assertIn("gdigrab", args)
        self.assertEqual(args[args.index("-offset_x") + 1], "-100")
        self.assertEqual(args[args.index("-video_size") + 1], "650x480")
        self.assertEqual(args[-1], "test.mp4")
        self.assertIn("yuv420p", args)

    def test_rejects_invalid_regions(self):
        with self.assertRaises(ValueError):
            gdigrab_args("ffmpeg", Path("t.mp4"), 0, 0, 0, 100)
        with self.assertRaises(ValueError):
            gdigrab_args("ffmpeg", Path("t.mp4"), 0, 0, 640, 480, fps=0)


if __name__ == "__main__":
    unittest.main()
