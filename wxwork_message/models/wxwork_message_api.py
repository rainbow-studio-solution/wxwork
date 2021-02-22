# -*- coding: utf-8 -*-

import logging
from odoo import api, models, _

from odoo.addons.wxwork_api.api.corp_api import CorpApi, CORP_API_TYPE
from odoo.addons.wxwork_api.api.abstract_api import ApiException
from odoo.addons.wxwork_api.api.error_code import Errcode

_logger = logging.getLogger(__name__)


class WxWorkMessageApi(models.AbstractModel):
    _name = "wxwork.message.api"
    _description = "Enterprise WeChat Message API"

    def build_message(
        self,
        msgtype,
        toall=None,
        touser=None,
        toparty=None,
        totag=None,
        subject=None,
        media_id=None,
        description=None,
        author_id=None,
        body_html=None,
        body_text=None,
        safe=None,
        enable_id_trans=None,
        enable_duplicate_check=None,
        duplicate_check_interval=None,
    ):
        """
        构建消息
        :msgtype: 消息类型，根据消息类型来构建消息内容
        :toall: 发送给全体人员
        :touser: 指定接收消息的成员，成员ID列表（多个接收者用‘|’分隔，最多支持1000个）。
                          特殊情况：指定为”@all”，则向该企业应用的全部成员发送
        :toparty: 指定接收消息的部门，部门ID列表，多个接收者用‘|’分隔，最多支持100个。
                           当touser为”@all”时忽略本参数
        :totag: 指定接收消息的标签，标签ID列表，多个接收者用‘|’分隔，最多支持100个。
                         当touser为”@all”时忽略本参数  
        :subject: 标题 ，不同消息类型，长度限制不一样 
        :media_id: media_id, 可以通过素材管理接口获得
        :body_html: 图文消息的内容，支持html标签，不超过666 K个字节，仅用于图文消息（mpnews）
        :body_text: 非图文消息的内容，不同消息类型，长度限制不一样 
        :safe: 表示是否是保密消息，0表示可对外分享，1表示不能分享且内容显示水印，默认为0   
        :enable_id_trans: 表示是否开启id转译，0表示否，1表示是，默认0。仅第三方应用需要用到，企业自建应用可以忽略。 
        :enable_duplicate_check: 表示是否开启重复消息检查，0表示否，1表示是，默认0
        :duplicate_check_interval: 表示是否重复消息检查的时间间隔，默认1800s，最大不超过4小时

        """

        messages_content = self.get_messages_content(
            msgtype, description, author_id, body_html, body_text, subject, media_id
        )
        messages_options = self.get_messages_options(
            msgtype,
            safe,
            enable_id_trans,
            enable_duplicate_check,
            duplicate_check_interval,
        )
        sys_params = self.env["ir.config_parameter"].sudo()
        agentid = sys_params.get_param("wxwork.message_agentid")

        messages = {}
        messages = {
            "touser": "@all" if toall else touser,
            "toparty": "" if toall else toparty,
            "totag": "" if toall else totag,
            "msgtype": msgtype,
            "agentid": agentid,
        }
        messages.update(messages_content)
        messages.update(messages_options)
        return messages

    def send_by_api(self, message_):
        # print(params)
        sys_params = self.env["ir.config_parameter"].sudo()
        corpid = sys_params.get_param("wxwork.corpid")
        agentid = sys_params.get_param("wxwork.message_agentid")
        secret = sys_params.get_param("wxwork.message_secret")
        debug = sys_params.get_param("wxwork.debug_enabled")
        wxapi = CorpApi(corpid, secret)

        try:
            response = wxapi.httpCall(CORP_API_TYPE["MESSAGE_SEND"], message_)
            return response.get("errcode")
        except ApiException as e:
            _logger.exception(
                _(
                    "Send Error , error: %s",
                    (str(e.errCode), Errcode.getErrcode(e.errCode), e.errMsg),
                )
            )
            if debug:
                print(
                    _(
                        "Send Error , error: %s",
                        (str(e.errCode), Errcode.getErrcode(e.errCode), e.errMsg),
                    )
                )

    @api.model
    def send_message(self, message):
        """
        发送一条企业微信消息 到多个人员
        """
        return self.send_by_api(message)

    @api.model
    def _send_message_batch(self, messages):
        """
        批量模式发送企业微信消息
        """
        params = {
            "messages": messages,
        }
        return self._wxwork_message_send_api(params)

    def get_messages_content(
        self,
        msgtype,
        description=None,
        author_id=None,
        body_html=None,
        body_text=None,
        subject=None,
        media_id=None,
    ):
        messages_content = {}
        if msgtype == "text":
            # 文本消息
            messages_content = {
                "text": body_text,
            }
        if msgtype == "mpnews":
            # 图文消息（mpnews）
            messages_content = {
                "mpnews": {
                    "articles": [
                        {
                            "title": subject,
                            "thumb_media_id": media_id,
                            "author": author_id.display_name,
                            "content": body_html,
                            "digest": description,
                        }
                    ]
                },
            }
        if msgtype == "markdown":
            # markdown消息
            messages_content = {
                "content": body_text,
            }

        return messages_content

    def get_messages_options(
        self,
        msgtype,
        safe=None,
        enable_id_trans=None,
        enable_duplicate_check=None,
        duplicate_check_interval=None,
    ):
        messages_options = {
            "safe": safe,
            "enable_id_trans": enable_id_trans,
            "enable_duplicate_check": enable_duplicate_check,
            "duplicate_check_interval": duplicate_check_interval,
        }

        if msgtype == "markdown":
            # markdown消息
            del messages_options[safe]
            del messages_options[enable_id_trans]

        return messages_options
