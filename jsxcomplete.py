# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
import os
import json
import tempfile
import subprocess


# https://gist.github.com/1027906
def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.

    Backported from Python 2.7 as it's implemented as pure python on stdlib.

    >>> check_output(['/usr/bin/python', '--version'])
    Python 2.6.2
    """
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        error = subprocess.CalledProcessError(retcode, cmd)
        error.output = output
        raise error
    return output


def system(command):
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return check_output(command, startupinfo=startupinfo)


def get_completions(view, settings):
    temp = tempfile.mktemp()
    try:
        with open(temp, 'w') as f:
            f.write(view.substr(sublime.Region(0, view.size())))

        jsx = settings.get('jsx_complete_command')
        if jsx is None:
            jsx = 'jsx.cmd' if os.name == 'nt' else 'jsx'

        row, col = view.rowcol(view.sel()[0].a)
        command = [
            jsx,
            '--input-filename', view.file_name(),
            '--complete', (str(row + 1) + ':' + str(col + 1)),
            temp
            ]

        try:
            ret = system(command)
            return json.loads(ret)
        except subprocess.CalledProcessError:
            return []
    finally:
        try:
            os.unlink(temp)
        except IOError:
            pass


class JsxCompleteListener(sublime_plugin.EventListener):
    def __init__(self):
        self.settings = sublime.load_settings('JSXComplete.sublime-settings')

    def on_query_completions(self, view, prefix, locations):
        if not view.file_name().endswith('.jsx'):
            return []
        words = get_completions(view, self.settings)
        words = [(w['word'], w['word']) for w in words]
        return words
