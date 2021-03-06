# -*- coding: utf-8 -*-

import logging

from odoo import api, models, fields
from odoo.addons.phone_validation.tools import phone_validation
from odoo.tools import html2plaintext, plaintext2html

from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID
from odoo.exceptions import MissingError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    """ 
    邮件线程模型被任何需要作为讨论主题的模型所继承，消息可以附加在讨论主题上。
    公共方法的前缀是``message```以避免与将从此类继承的模型的方法发生名称冲突。

  
    ``mail.thread``定义用于处理和显示通信历史记录的字段。
    ``mail.thread``还管理继承类的跟随者。所有功能和预期行为都由管理 mail.thread. 
    Widgets是为7.0及以下版本的Odoo设计的。

    实现任何方法都不需要继承类，因为默认实现适用于任何模型。
    但是，在处理传入电子邮件时，通常至少重写``message_new``和``message_update``方法（调用``super``），以便在创建和更新线程时添加特定于模型的行为。

    选项:
        - _mail_flat_thread: 
            如果设置为True，则所有没有parent_id的邮件将自动附加到发布在源上的第一条邮件。
            如果设置为False，则使用线程显示Chatter，并且不会自动设置parent_id。

    MailThread特性可以通过上下文键进行某种程度的控制 :

     - ``mail_create_nosubscribe``: 在创建或消息发布时，不要向记录线程订阅uid
     - ``mail_create_nolog``: 在创建时，不要记录自动的'<Document>created'消息
     - ``mail_notrack``: 在创建和写入时，不要执行值跟踪创建消息
     - ``tracking_disable``: 在创建和写入时，不执行邮件线程功能（自动订阅、跟踪、发布…）
     - ``mail_notify_force_send``: 如果要发送的电子邮件通知少于50个，请直接发送，而不是使用队列；默认情况下为True
    """

    _inherit = "mail.thread"

    # ------------------------------------------------------
    # 增加、查询、修改、删除
    # CRUD
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 模型/CRUD助手
    # MODELS / CRUD HELPERS
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 包装和工具
    # WRAPPERS AND TOOLS
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 追踪/记录
    # TRACKING / LOG
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 邮件网关
    # MAIL GATEWAY
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 收件人管理工具
    # RECIPIENTS MANAGEMENT TOOLS
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 消息发布API
    # MESSAGE POST API
    # ------------------------------------------------------

    @api.returns("mail.message", lambda value: value.id)
    def message_post(
        self,
        *,
        body="",
        subject=None,
        message_type="notification",
        email_from=None,
        author_id=None,
        parent_id=False,
        subtype_xmlid=None,
        subtype_id=False,
        partner_ids=None,
        channel_ids=None,
        attachments=None,
        attachment_ids=None,
        add_sign=True,
        record_name=False,
        **kwargs
    ):
        """ 
        在现有线程中发布新消息，并返回新的mail.message ID。 
        :param str body: 邮件正文，通常是原始HTML，将被清理消毒
        :param str subject: 消息的主题 
        :param str message_type: 请参阅mail_message.message_type字段。 可以是user_notification以外的任何内容，保留给message_notify 
        :param int parent_id: 处理线程队列
        :param int subtype_id: 消息的subtype_id，主要用于关注者机制 
        :param list(int) partner_ids: partner_ids通知 
        :param list(int) channel_ids: channel_ids通知 
        :param list(tuple(str,str), tuple(str,str, dict) or int) attachments : 以``(name,content)``或 ``(name,content, info)`` 形式的附件元组列表，其中content不是base64编码的 
        :param list id attachment_ids: 链接到此消息的现有附件列表 
            - 只能由聊天设定 
            - 附加到mail.compose.message（0）的附件对象将被附加到相关文档。 
        额外的关键字参数将用作新mail.message记录的默认列值。 
        :return int: ID of newly created mail.message
        """
        self.ensure_one()  # 应始终记录在记录上，如果没有记录，请使用message_notify
        # 从通知附加值中拆分消息附加值
        msg_kwargs = dict(
            (key, val)
            for key, val in kwargs.items()
            if key in self.env["mail.message"]._fields
        )
        notif_kwargs = dict(
            (key, val) for key, val in kwargs.items() if key not in msg_kwargs
        )

        if (
            self._name == "mail.thread"
            or not self.id
            or message_type == "user_notification"
        ):
            raise ValueError(
                "message_post should only be call to post message on record. Use message_notify instead"
            )

        if "model" in msg_kwargs or "res_id" in msg_kwargs:
            raise ValueError(
                "message_post doesn't support model and res_id parameters anymore. Please call message_post on record."
            )
        if "subtype" in kwargs:
            raise ValueError(
                "message_post doesn't support subtype parameter anymore. Please give a valid subtype_id or subtype_xmlid value instead."
            )

        self = self._fallback_lang()  # 立即将lang添加到上下文中，因为在以后的各种流程中它将很有用。

        # 显式访问权限检查，因为display_name计算为sudo。
        self.check_access_rights("read")
        self.check_access_rule("read")
        record_name = record_name or self.display_name

        partner_ids = set(partner_ids or [])
        channel_ids = set(channel_ids or [])

        if any(not isinstance(pc_id, int) for pc_id in partner_ids | channel_ids):
            raise ValueError(
                "message_post partner_ids and channel_ids must be integer list, not commands"
            )

        # if self.wxwork_id:
        #     print("message_post", self.wxwork_id)
        # else:
        # 查找邮件的作者
        author_id, email_from = self._message_compute_author(
            author_id, email_from, raise_exception=True
        )

        if subtype_xmlid:
            subtype_id = self.env["ir.model.data"].xmlid_to_res_id(subtype_xmlid)
        if not subtype_id:
            subtype_id = self.env["ir.model.data"].xmlid_to_res_id("mail_mt_note")

        # 根据要求自动订阅收件人
        if self._context.get("mail_post_autofollow") and partner_ids:
            self.message_subscribe(list(partner_ids))

        MailMessage_sudo = self.env["mail.message"].sudo()
        if self._mail_flat_thread and not parent_id:
            parent_message = MailMessage_sudo.search(
                [
                    ("res_id", "=", self.id),
                    ("model", "=", self._name),
                    ("message_type", "!=", "user_notification"),
                ],
                order="id ASC",
                limit=1,
            )
            # parent_message在sudo中搜索性能，仅用于id。
            # 请注意，使用sudo我们将使消息与内部子类型匹配。
            parent_id = parent_message.id if parent_message else False
        elif parent_id:
            old_parent_id = parent_id
            parent_message = MailMessage_sudo.search(
                [("id", "=", parent_id), ("parent_id", "!=", False)], limit=1
            )
            # avoid loops when finding ancestors
            processed_list = []
            if parent_message:
                new_parent_id = parent_message.parent_id and parent_message.parent_id.id
                while new_parent_id and new_parent_id not in processed_list:
                    processed_list.append(new_parent_id)
                    parent_message = parent_message.parent_id
                parent_id = parent_message.id

        values = dict(msg_kwargs)
        values.update(
            {
                "author_id": author_id,
                "email_from": email_from,
                "model": self._name,
                "res_id": self.id,
                "body": body,
                "subject": subject or False,
                "message_type": message_type,
                "parent_id": parent_id,
                "subtype_id": subtype_id,
                "partner_ids": partner_ids,
                "channel_ids": channel_ids,
                "add_sign": add_sign,
                "record_name": record_name,
            }
        )
        attachments = attachments or []
        attachment_ids = attachment_ids or []
        attachement_values = self._message_post_process_attachments(
            attachments, attachment_ids, values
        )
        values.update(attachement_values)  # attachement_ids, [body]

        new_message = self._message_create(values)

        # 如有必要，设置主附件字段
        self._message_set_main_attachment_id(values["attachment_ids"])

        if (
            values["author_id"]
            and values["message_type"] != "notification"
            and not self._context.get("mail_create_nosubscribe")
        ):
            if (
                self.env["res.partner"].browse(values["author_id"]).active
            ):  # 我们不想将odoobot / inactive添加为关注者
                self._message_subscribe([values["author_id"]])

        self._message_post_after_hook(new_message, values)
        self._notify_thread(new_message, values, **notif_kwargs)
        return new_message

    # ------------------------------------------------------
    # 消息发布工具
    # MESSAGE POST TOOLS
    # ------------------------------------------------------

    def _message_compute_author(
        self, author_id=None, email_from=None, raise_exception=True
    ):
        """ 
        计算消息的作者信息的工具方法。目的是确保发送电子邮件时，作者/当前用户/电子邮件地址之间的最大一致性。
        """
        if author_id is None:
            if email_from:
                author = self._mail_find_partner_from_emails([email_from])[0]
            else:
                author = self.env.user.partner_id
                email_from = author.email_formatted
            author_id = author.id

        if email_from is None:
            if author_id:
                author = self.env["res.partner"].browse(author_id)
                email_from = author.email_formatted

        # 没有作者电子邮件的超级用户模式->可能是公共用户；无论如何，我们不想崩溃
        if not email_from and not self.env.su and raise_exception:
            raise exceptions.UserError(
                _("Unable to log message, please configure the sender's email address.")
            )

        return author_id, email_from

    # ------------------------------------------------------
    # 通知API
    # NOTIFICATION API
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 关注者API
    # FOLLOWERS API
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 控制器
    # CONTROLLERS
    # ------------------------------------------------------
