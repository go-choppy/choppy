# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import os
import logging
import shutil
import psutil
import signal
from datetime import datetime
from random import Random as _Random
import _thread
_allocate_lock = _thread.allocate_lock
_once_lock = _allocate_lock()
_name_sequence = None


def get_copyright(site_author='choppy'):
    year = datetime.now().year
    copyright = 'Copyright &copy; {} {}, ' \
                'Maintained by the <a href="http://choppy.3steps.cn">' \
                'Choppy Community</a>.'.format(year, site_author.title())
    return copyright


def copy_and_overwrite(from_path, to_path, is_file=False, ignore_errors=True, ask=False):
    if ask:
        answer = ''
        while answer.upper() not in ("YES", "NO", "Y", "N"):
            try:
                answer = raw_input("Remove %s, Enter Yes/No: " % to_path)  # noqa: python2
            except Exception:
                answer = input("Remove %s, Enter Yes/No: " % to_path)  # noqa: python3

            answer = answer.upper()
            if answer == "YES" or answer == "Y":
                ignore_errors = True
            elif answer == "NO" or answer == "N":
                ignore_errors = False
            else:
                print("Please enter Yes/No.")

    if ignore_errors:
        if os.path.isfile(to_path):
            os.remove(to_path)

        if os.path.isdir(to_path):
            shutil.rmtree(to_path)

    if is_file and os.path.isfile(from_path):
        parent_dir = os.path.dirname(to_path)
        # Force to make directory when parent directory doesn't exist
        os.makedirs(parent_dir, exist_ok=True)
        shutil.copy2(from_path, to_path)
    elif os.path.isdir(from_path):
        shutil.copytree(from_path, to_path)


class ReportTheme:
    def __init__(self):
        pass

    @classmethod
    def get_theme_lst(cls):
        theme_lst = ('mkdocs', 'readthedocs', 'material', 'cinder')
        return theme_lst


def print_obj(string):
    try:  # For Python2.7
        print(unicode(string).encode('utf8'))
    except NameError:  # For Python3
        print(string)


def clean_tmp_dir(tmp_dir):
    # Clean temp directory
    shutil.rmtree(tmp_dir, ignore_errors=True)


class _RandomNameSequence:
    """An instance of _RandomNameSequence generates an endless
    sequence of unpredictable strings which can safely be incorporated
    into file names.  Each string is six characters long.  Multiple
    threads can safely use the same instance at the same time.
    _RandomNameSequence is an iterator."""

    characters = ("abcdefghijklmnopqrstuvwxyz" +  # noqa
                  "ABCDEFGHIJKLMNOPQRSTUVWXYZ" +  # noqa
                  "0123456789_")

    def __init__(self):
        self.mutex = _allocate_lock()
        self.normcase = os.path.normcase

    @property
    def rng(self):
        cur_pid = os.getpid()
        if cur_pid != getattr(self, '_rng_pid', None):
            self._rng = _Random()
            self._rng_pid = cur_pid
        return self._rng

    def __iter__(self):
        return self

    def next(self):
        m = self.mutex
        c = self.characters
        choose = self.rng.choice

        m.acquire()
        try:
            letters = [choose(c) for dummy in "123456"]
        finally:
            m.release()

        return self.normcase(''.join(letters))


def get_candidate_name():
    """Common setup sequence for all user-callable interfaces."""

    global _name_sequence
    if _name_sequence is None:
        _once_lock.acquire()
        try:
            if _name_sequence is None:
                _name_sequence = _RandomNameSequence()
        finally:
            _once_lock.release()
    return _name_sequence.next()


class Process:
    def __init__(self):
        self.logger = logging.getLogger('choppy.utils.Process')

    def get_process(self, process_id):
        try:
            p = psutil.Process(process_id)
            return p
        except psutil.NoSuchProcess:
            self.logger.warning('No such process: %s' % process_id)
            return None

    def clean_processs(self):
        process_id = os.getpid()
        process = self.get_process(process_id)
        if process:
            self.kill_proc_tree(process_id)

    def kill_proc_tree(self, pid, sig=signal.SIGTERM, include_parent=False,
                       timeout=3, on_terminate=None):
        """Kill a process tree (including grandchildren) with signal
        "sig" and return a (gone, still_alive) tuple.
        "on_terminate", if specified, is a callabck function which is
        called as soon as a child terminates.
        """
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        if include_parent:
            children.append(parent)
        children_pids = [child.pid for child in children]
        self.logger.info('Kill process: %s and all children %s' % (pid, children_pids))
        try:
            for p in children:
                p.send_signal(sig)
            gone, alive = psutil.wait_procs(children, timeout=timeout,
                                            callback=on_terminate)
            return (gone, alive)
        except Exception as err:
            self.logger.debug('Kill all processes: %s' % str(err))
            return (None, None)


def clean_temp_files():
    mk_media_extension_temp = '/tmp/choppy-media-extension'
    choppy_temp = '/tmp/choppy'
    shutil.rmtree(choppy_temp, ignore_errors=True)
    shutil.rmtree(mk_media_extension_temp, ignore_errors=True)
