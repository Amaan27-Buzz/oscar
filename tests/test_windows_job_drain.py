import ctypes
import unittest
from ctypes import wintypes
from unittest.mock import MagicMock

from oscar.windows_process import ProcessIds, WindowsJob


class WindowsJobDrainTests(unittest.TestCase):
    def job(self, wait_result=0):
        job = object.__new__(WindowsJob)
        job.handle = 100
        job.kernel = MagicMock()

        def ids(handle, kind, pointer, size, returned):
            record = ctypes.cast(pointer, ctypes.POINTER(ProcessIds)).contents
            record.count = 2
            record.ids[0], record.ids[1] = 12, 13
            return True

        def owned(process, handle, pointer):
            ctypes.cast(pointer, ctypes.POINTER(wintypes.BOOL)).contents.value = process == 12
            return True

        job.kernel.QueryInformationJobObject.side_effect = ids
        job.kernel.OpenProcess.side_effect = lambda rights, inherited, pid: pid
        job.kernel.IsProcessInJob.side_effect = owned
        job.kernel.WaitForSingleObject.return_value = wait_result
        return job

    def test_close_terminates_only_job_and_waits_for_confirmed_owned_process(self):
        job = self.job()
        job.close()
        job.kernel.TerminateJobObject.assert_called_once_with(100, 1)
        self.assertEqual(1, job.kernel.WaitForSingleObject.call_count)
        process, timeout = job.kernel.WaitForSingleObject.call_args.args
        self.assertEqual(12, process)
        self.assertTrue(0 <= timeout <= 3000)
        self.assertEqual(
            [12, 13, 100], [call.args[0] for call in job.kernel.CloseHandle.call_args_list]
        )
        self.assertIsNone(job.handle)

    def test_drain_timeout_is_bounded_and_still_releases_owned_handles(self):
        job = self.job(258)
        with self.assertRaisesRegex(OSError, "drain deadline"):
            job.close()
        self.assertIsNone(job.handle)
        job.kernel.CloseHandle.assert_any_call(100)
        job.close()
        job.kernel.TerminateJobObject.assert_called_once()

    def test_already_closed_job_does_not_touch_processes(self):
        job = self.job()
        job.handle = None
        job.close()
        job.kernel.TerminateJobObject.assert_not_called()
        job.kernel.OpenProcess.assert_not_called()


if __name__ == "__main__":
    unittest.main()
