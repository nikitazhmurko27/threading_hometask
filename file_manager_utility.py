import os
import shutil
import logging
from distutils.dir_util import copy_tree
from queue import Queue
from threading import Thread, current_thread, Condition
from time import sleep

logging.basicConfig(filename='logs.log', level=logging.DEBUG)


class FileManagerUtility:
    def __init__(self, operation, from_folder, to_folder, file_mask="", threads_amount=1) -> None:
        self._operation = operation
        self._from_folder = from_folder
        self._to_folder = to_folder
        self._threads_amount = threads_amount
        self._file_mask = file_mask
        self._q = Queue()
        self._cv = Condition()

        logging.info(
            f"Started '{operation}' operation "
            f"from {from_folder} "
            f"to {to_folder} "
            f"in {threads_amount} threads."
        )

    def _is_folder_readable(self, folder: str) -> bool:
        return os.access(fr"{folder}", os.F_OK)

    def _is_folder_writable(self, folder: str) -> bool:
        return os.access(fr"{folder}", os.W_OK)

    def _add_files_to_queue_by_mask(self) -> None:
        if not self._file_mask:
            return

        for file in os.listdir(self._from_folder):
            if not file.endswith(self._file_mask):
                continue
            self._q.put(os.path.join(self._from_folder, file))

        for _ in range(self._threads_amount):
            self._q.put("stop")

    def _create_threads(self) -> list:
        thread_range = self._threads_amount
        if not self._file_mask:
            thread_range = 1

        if self._operation == 'copy':
            return [Thread(target=self._copy, name=f"Thread #{i}") for i in range(thread_range)]
        return [Thread(target=self._move, name=f"Thread #{i}") for i in range(thread_range)]

    def start(self) -> None:
        if not self._is_folder_readable(self._from_folder):
            logging.error(f'Folder "{self._from_folder}" is not readable')
            return
        if not self._is_folder_writable(self._to_folder):
            logging.error(f'Folder "{self._to_folder}" is not writable')
            return

        threads = self._create_threads()
        for t in threads:
            t.start()

        if not self._file_mask:
            self._q.put(self._from_folder)
        else:
            self._add_files_to_queue_by_mask()

        with self._cv:
            self._cv.notify_all()

    def _copy(self,) -> None:
        while True:
            with self._cv:
                # Wait while queue is empty
                while self._q.empty():
                    self._cv.wait()
                try:
                    thread_name = current_thread().getName()

                    # Get data (file path) from queue
                    pathname = self._q.get_nowait()
                    if not self._file_mask:
                        copy_tree(pathname, self._to_folder)
                        logging.info(f":{thread_name} copied folder by {pathname} to {self._to_folder}")
                        break

                    # If get "stop" message then stop thread
                    if pathname == "stop":
                        break

                    shutil.copy(pathname, self._to_folder)
                    logging.info(f":{thread_name} copied {pathname} file to {self._to_folder}")

                except shutil.Error as err:
                    logging.error(err.args[0])
                sleep(0.1)

    def _move(self,) -> None:
        while True:
            with self._cv:
                # Wait while queue is empty
                while self._q.empty():
                    self._cv.wait()
                try:
                    thread_name = current_thread().getName()

                    # Get data (file path) from queue
                    pathname = self._q.get_nowait()
                    if not self._file_mask:
                        shutil.move(pathname, self._to_folder)
                        logging.info(f":{thread_name} moved folder by {pathname} to {self._to_folder}")
                        break

                    # If get "stop" message then stop thread
                    if pathname == "stop":
                        break

                    shutil.move(pathname, self._to_folder)
                    logging.info(f":{thread_name} moved {pathname} file to {self._to_folder}")

                except shutil.Error as err:
                    logging.error(err.args[0])
                sleep(0.1)
