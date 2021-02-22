# -*- coding: utf-8 -*-

import datetime
import logging
import threading
from odoo import _, api, fields, models
from odoo import tools
from odoo.exceptions import UserError
from odoo.addons.wxwork_api.api.corp_api import CorpApi, CORP_API_TYPE

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    API_TO_MESSAGE_STATE = {
        "success": "sent",
        "invaliduser": "Invalid user",
        "invalidparty": "Invalid Department",
        "invalidtag": "Invalid Tag",
        "other": "Other",
    }
    msgtype = fields.Char(string="Message type",)
    media_id = fields.Char(string="Media file id",)
    message_to_all = fields.Boolean("To all members",)
    message_to_user = fields.Char(string="To User",)
    message_to_party = fields.Char(string="To Departments",)
    message_to_tag = fields.Char(string="To Tags",)
    body_text = fields.Text("Text Contents",)

    safe = fields.Selection(
        [
            ("0", "Shareable"),
            ("1", "Cannot share and content shows watermark"),
            ("2", "Only share within the company "),
        ],
        string="Secret message",
        required=True,
        default="1",
        readonly=True,
        help="表示是否是保密消息，0表示可对外分享，1表示不能分享且内容显示水印，2表示仅限在企业内分享，默认为0；注意仅mpnews类型的消息支持safe值为2，其他消息类型不支持",
    )

    enable_id_trans = fields.Boolean(
        string="Turn on id translation", help="表示是否开启id转译，0表示否，1表示是，默认0", default=False
    )
    enable_duplicate_check = fields.Boolean(
        string="Turn on duplicate message checking",
        help="表示是否开启重复消息检查，0表示否，1表示是，默认0",
        default=False,
    )
    duplicate_check_interval = fields.Integer(
        string="Time interval for repeated message checking",
        help="表示是否重复消息检查的时间间隔，默认1800s，最大不超过4小时",
        default="1800",
    )

    @api.model
    def process_email_queue(self, ids=None):
        """
        立即发送排队的消息，在每条消息发送后提交-这不是事务性的，不应在另一个事务中调用！ 

        :param list ids: 要发送的电子邮件ID的可选列表。 如果通过，则不执行搜索，而是使用这些ID。 
        :param dict context: 如果上下文中存在“过滤器”键，则此值将用作附加过滤器，以进一步限制要发送的传出消息（默认情况下，所有“传出”消息都已发送）。 
        """
        filters = [
            "&",
            ("state", "=", "outgoing"),
            "|",
            ("scheduled_date", "<", datetime.datetime.now()),
            ("scheduled_date", "=", False),
        ]
        if "filters" in self._context:
            filters.extend(self._context["filters"])
        # TODO: make limit configurable
        filtered_ids = self.search(filters, limit=10000).ids
        if not ids:
            ids = filtered_ids
        else:
            ids = list(set(filtered_ids) & set(ids))
        ids.sort()

        res = None
        try:
            # 自动提交（测试模式除外）
            auto_commit = not getattr(threading.currentThread(), "testing", False)
            if self.notification_type == "wxwork":
                res = self.browse(ids).send_wxwork_message(auto_commit=auto_commit)
            else:
                res = self.browse(ids).send(auto_commit=auto_commit)
        except Exception:
            _logger.exception(_("Failed processing mail queue"))
        return res

    def _postprocess_sent_wxwork_message(
        self, success_pids, failure_reason=False, failure_type=None
    ):
        """
        成功发送``mail``后，请执行所有必要的后处理，包括如果已设置邮件的auto_delete标志，则将其及其附件完全删除。
        被子类覆盖，以实现额外的后处理行为。 

        :return: True
        """
        notif_mails_ids = [mail.id for mail in self if mail.notification]
        if notif_mails_ids:
            notifications = self.env["mail.notification"].search(
                [
                    ("notification_type", "=", "wxwork"),
                    ("mail_id", "in", notif_mails_ids),
                    ("notification_status", "not in", ("sent", "canceled")),
                ]
            )
            if notifications:
                # 查找所有链接到失败的通知
                failed = self.env["mail.notification"]
                if failure_type:
                    failed = notifications.filtered(
                        lambda notif: notif.res_partner_id not in success_pids
                    )
                (notifications - failed).sudo().write(
                    {
                        "notification_status": "sent",
                        "failure_type": "",
                        "failure_reason": "",
                    }
                )
                if failed:
                    failed.sudo().write(
                        {
                            "notification_status": "exception",
                            "failure_type": failure_type,
                            "failure_reason": failure_reason,
                        }
                    )
                    messages = notifications.mapped("mail_message_id").filtered(
                        lambda m: m.is_thread_message()
                    )
                    # TDE TODO: 通知基于消息而不是基于通知的通知，以减少通知数量可能会很棒
                    messages._notify_message_notification_update()  # 通知用户我们失败了
            if not failure_type or failure_type == "RECIPIENT":  # 如果还有另一个错误，我们要保留邮件。
                mail_to_delete_ids = [mail.id for mail in self if mail.auto_delete]
                self.browse(mail_to_delete_ids).sudo().unlink()

        return True

    # ------------------------------------------------------
    # 消息格式、工具和发送机制
    # ------------------------------------------------------
    def _send_wxwork_prepare_values(self, partner=None):
        """
        根据合作伙伴返回有关特定电子邮件值的字典，或者对整个邮件都是通用的。对于特定电子邮件值取决于对伙伴的字典，或者对mail.email_to给出的整个收件人来说都是通用的。 

        :param Model partner: 具体的收件人合作伙伴 
        """
        self.ensure_one()
        body_html = self._send_prepare_body()
        # body_alternative = tools.html2plaintext(body_html)
        if partner:
            email_to = [
                tools.formataddr((partner.name or "False", partner.email or "False"))
            ]
            message_to_user = [
                tools.formataddr(
                    (partner.name or "False", partner.message_to_user or "False")
                )
            ]
        else:
            email_to = tools.email_split_and_format(self.email_to)
            message_to_user = tools.email_split_and_format(self.message_to_user)
        res = {
            # "subject": subject,
            "body_html": body_html,
            # "message_to_user": message_to_user,
        }

        return res

    def send_wxwork_message(self, auto_commit=False, raise_exception=False):
        """
        立即发送选定的电子邮件，而忽略它们的当前状态（除非已被重新发送，否则不应传递已发送的电子邮件）。
成功发送的电子邮件被标记为“已发送”，而失败发送的电子邮件被标记为“例外”，并且相应的错误邮件将输出到服务器日志中。
        :param bool auto_commit：发送每封邮件后是否强制提交邮件状态（仅用于调度程序处理）；
                 在正常发送绝对不能为True（默认值：False） 
        :param bool raise_exception：如果电子邮件发送过程失败，是否引发异常 
        :return: True
        """

        sys_params = self.env["ir.config_parameter"].sudo()
        corpid = sys_params.get_param("wxwork.corpid")
        secret = sys_params.get_param("wxwork.message_secret")
        message_agentid = sys_params.get_param("wxwork.message_agentid")

        if "xxxxxxxxxxxxxxxxxx" in corpid or corpid is None or corpid is False:
            raise UserError(_("Please fill in the company ID"))
        elif (
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" in secret
            or secret is None
            or secret is False
        ):
            raise UserError(
                _("Please fill in the application secret of the message push")
            )
        elif (
            "0000000" in message_agentid
            or message_agentid is None
            or message_agentid is False
        ):
            raise UserError(_("Please fill in the application ID of the message push"))
        else:
            for batch_ids in self._split_by_server():
                # TODO 待处理多公司-企业微信互联功能

                self.browse(batch_ids)._send_wxwork_message(
                    auto_commit=auto_commit, raise_exception=raise_exception,
                )
                _logger.info(
                    _("Sent batch %s messages"), len(batch_ids),
                )

    def _send_wxwork_message(
        self, auto_commit=False, raise_exception=False,
    ):
        # print("发送消息")
        IrWxWorkMessageApi = self.env["wxwork.message.api"]
        for mail_id in self.ids:
            mail = self.browse(mail_id)
            if mail.state != "outgoing":
                if mail.state != "exception" and mail.auto_delete:
                    mail.sudo().unlink()
                continue

            msg = IrWxWorkMessageApi.build_message(
                msgtype=mail.msgtype,
                toall=mail.message_to_all,
                touser=mail.message_to_user,
                toparty=mail.message_to_party,
                totag=mail.message_to_tag,
                subject=mail.subject,
                media_id=mail.media_id,
                description=mail.description,
                author_id=mail.author_id,
                body_html=mail.body_html,
                body_text=mail.body_text,
                safe=mail.safe,
                enable_id_trans=mail.enable_id_trans,
                enable_duplicate_check=mail.enable_duplicate_check,
                duplicate_check_interval=mail.duplicate_check_interval,
            )
            print("_send_wxwork_message", msg)

        return True
