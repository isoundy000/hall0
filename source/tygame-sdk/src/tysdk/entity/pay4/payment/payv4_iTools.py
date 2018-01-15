# -*- coding=utf-8 -*-

import json
import urllib

from payv4_helper import PayHelperV4
from tyframework.context import TyContext
from tysdk.entity.pay.rsacrypto import rsa_decrypto_with_publickey, _verify_with_publickey_pycrypto, iTools_pubkey_str, \
    _iTools_pubkey_py
from tysdk.entity.pay4.decorator.payv4_callback import payv4_callback
from tysdk.entity.pay4.decorator.payv4_order import payv4_order
from tysdk.entity.pay4.payment.payv4_base import PayBaseV4


######################################################################
# iToolscallback过程的主要逻辑实现
# Created by Zhangshibo at 2015/09/09
# Version:2.4.1
######################################################################

class TuYouPayiToolsV4(PayBaseV4):
    @payv4_order('itools')
    def charge_data(cls, mi):
        chargeinfo = cls.get_charge_info(mi)
        chargeinfo['chargeData'] = {'platformOrderId': chargeinfo['platformOrderId']}
        return cls.return_mo(0, chargeInfo=chargeinfo)

    @payv4_callback('/open/ve/pay/itools/callback')
    def doiToolsPayCallback(self, rpath):
        postData = TyContext.RunHttp.get_body_content()
        TyContext.ftlog.debug('TuYouPayiTools->doiToolsPayCallback postData: ', postData)
        paramslist = postData.split('&')
        params = {}
        for k in paramslist:
            paramdata = k.split('=')
            params[paramdata[0]] = paramdata[1]
        TyContext.ftlog.debug('TuYouPayiTools->doiToolsPayCallback postParams: ', params)

        for k in params.keys():
            params[k] = urllib.unquote(params[k])
        TyContext.ftlog.debug('TuYouPayiTools->doiToolsPayCallback postParams_urldecode: ', params)

        pristr = params['notify_data']
        sign = params['sign']
        data = rsa_decrypto_with_publickey(pristr, iTools_pubkey_str, 1)
        TyContext.ftlog.debug('TuYouPayiTools->doiToolsPayCallback iTools callback data: ', data)
        rparam = json.loads(data)
        TyContext.ftlog.debug('TuYouPayiTools->doiToolsPayCallback notify_data: ', rparam)
        try:
            orderPlatformId = rparam['order_id_com']
            amount = rparam['amount']
            account = rparam['account']
            third_orderid = rparam['order_id']
            result = rparam['result']
            user_id = rparam['user_id']
        except:
            TyContext.ftlog.error('TuYouPayiTools->doiToolsPayCallback Get params in iTools callback ERROR!')
            return 'fail'
        if 0 != cmp('success', result):
            TyContext.ftlog.error('TuYouPayiTools->doiToolsPayCallback Charge failed!')
            errormsg = 'user use ' + account + ' charge ' + result
            PayHelperV4.callback_error(orderPlatformId, errormsg, rparam)

        # veriry_result = cls.rsa_verify(data, sign, iTools_pubkey_str)
        veriry_result = _verify_with_publickey_pycrypto(data, sign, _iTools_pubkey_py)
        if not veriry_result:
            TyContext.ftlog.error(
                'TuYouPayiTools->doiToolsPayCallback Verify failed! data: %s, sign: %s, iTools_pubkey_str: %s'
                % (data, sign, iTools_pubkey_str))
            return 'fail'

        rparam['third_orderid'] = third_orderid
        PayHelperV4.callback_ok(orderPlatformId, amount, rparam)
        TyContext.ftlog.debug('TuYouPayiTools->doiToolsPayCallback user %s charge % successed! ' % (user_id, amount))
        return 'success'
