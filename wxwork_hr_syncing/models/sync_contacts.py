# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from threading import Thread
from .sync_image import SyncImage

_logger = logging.getLogger(__name__)


class SyncTask(object):
    """
    同步HR任务
    """

    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.debug = self.kwargs["debug"]
        self.sync_hr = self.kwargs["sync_hr"]
        self.department = self.kwargs["department"]
        self.department_category = self.kwargs["department_category"]
        self.employee = self.kwargs["employee"]
        self.employee_category = self.kwargs["employee_category"]

    def run(self):
        if self.debug:
            _logger.info(_("Start syncing Enterprise WeChat Contact"))
        if self.sync_hr:
            threads = []

            task_name_list = [
                _("Enterprise WeChat picture synchronization"),
                _("Enterprise WeChat department synchronization"),
                _("Enterprise WeChat department tag synchronization"),
                _("Enterprise WeChat employee synchronization"),
                _("Enterprise WeChat employee tag synchronization"),
            ]
            task_func_list = [
                SyncImage(self.kwargs).run,
                self.department.sync_department,
                self.department_category.sync_department_tags,
                self.employee.sync_employee,
                self.employee_category.sync_employee_tags,
            ]
            times = []
            results = []
            statuses = {}
            for i in range(len(task_name_list)):
                thread_task = SyncTaskThread(task_func_list[i], task_name_list[i])
                threads.append(thread_task)
            for i in range(len(task_name_list)):
                threads[i].start()
            for i in range(len(task_name_list)):
                threads[i].join()

            for t in threads:
                if t.is_alive():
                    pass
                else:
                    time, status, result = t.result
                    statuses.update(status)
                    times.append(time)
                    results.append(
                        _("%s, time spent: " "%s seconds") % (result, round(time, 3))
                    )

            results = "\n".join(results)
            if self.debug:
                _logger.info(
                    _(
                        "End sync Enterprise WeChat Contact, total time spent: %s seconds"
                    )
                    % sum(times)
                )

            return sum(times), statuses, results
        else:
            if self.debug:
                # _logger.warning(
                #     _(
                #         "The synchronization is terminated, the current setting does not allow synchronization from enterprise WeChat to odoo"
                #     )
                # )
                _logger.warning(
                    "The synchronization is terminated, the current setting does not allow synchronization from enterprise WeChat to odoo"
                )


class SyncTaskThread(Thread):
    def __init__(self, func, name=""):
        Thread.__init__(self)
        self.name = name
        self.func = func
        self.result = self.func()

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None
