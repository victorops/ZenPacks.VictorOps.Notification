#//==========================================================================//
#//          Copyright 2014-2017 VictorOps, Inc. All Rights Reserved         //
#//                                                                          //
#//                 PROPRIETARY AND CONFIDENTIAL INFORMATION                 //
#// The information contained herein is the proprietary and confidential     //
#// property of VictorOps, Inc. and may not be used, distributed, modified,  //
#// disclosed or reproduced without the express written permission of        //
#// VictorOps, Inc.                                                          //
#//==========================================================================//
import json
import logging
import urllib2
import requests
from time import time

from ZenPacks.VictorOps.Notification.interfaces import \
    IVictorOpsEnqueueContentInfo
from zope.interface import implements

import Globals
from Products.ZenModel.actions import (ActionExecutionException, IActionBase,
                                       _signalToContextDict)
from Products.ZenModel.interfaces import IAction
from Products.ZenUtils.guid.guid import GUIDManager
from zenoss.protocols.protobufs.zep_pb2 import (SEVERITY_ERROR,
                                                SEVERITY_WARNING,
                                                STATUS_ACKNOWLEDGED)

log = logging.getLogger("zen.VictorOps.actions")

class VictorOpsEnqueueAction(IActionBase):
    implements(IAction)

    log.info("Initializing VictorOps")

    id = 'victorops_enqueue'
    name = 'VictorOps Alert'
    actionContentInfo = IVictorOpsEnqueueContentInfo
    shouldExecuteInBatch = False

    def __init__(self):
        log.info("VictorOps Init")
        super(VictorOpsEnqueueAction, self).__init__()

    def setupAction(self, dmd):
        log.info("VictorOps Setup Action")
        self.guidManager = GUIDManager(dmd)
        self.dmd = dmd

    def execute(self, notification, signal):
        log.info('---------------------------------------------------------------------')
        log.info("Signal: %s" % signal)
        self.setupAction(notification.dmd)

        data = _signalToContextDict(signal, self.options.get('zopeurl'), notification, self.guidManager)
        log.debug(data)

        eventSummary = data['eventSummary']
        evt = data['evt']
        api_key = notification.content['api_key']
        routing_key = notification.content['routing_key']
        base_url = "https://alert.victorops.com/integrations/generic/20131114/alert/%s" % api_key
        api_url = base_url + "/%s" % routing_key if (routing_key) else base_url

        alertDetails = dict()
        alertDetails['monitoring_tool'] = 'zenoss'
        alertDetails['timestamp'] = int(time())
        alertDetails['zen_status'] = eventSummary.status
        alertDetails['zen_uuid'] = eventSummary.uuid
        alertDetails['zen_component'] = evt.component
        alertDetails['zen_severity'] = evt.severity
        alertDetails['ack_user'] = evt.ownerid
        alertDetails['ack_msg'] = evt.clearid
        alertDetails['state_message'] = evt.summary
        alertDetails['host_name'] = evt.device
        alertDetails['state_start_time'] = eventSummary.status_change_time
        alertDetails['zen_event_class'] = evt.eventClass
        alertDetails['zen_agent'] = eventSummary.agent
        alertDetails['zen_dedup_id'] = evt.dedupid
        alertDetails['zen_event_key'] = eventSummary.event_key
        alertDetails['zen_event_class_key'] = evt.eventClassKey

        if signal.clear:
            alertDetails['message_type'] = 'RECOVERY'
        elif evt.eventState == STATUS_ACKNOWLEDGED:
            alertDetails['message_type'] = 'ACKNOWLEDGEMENT'
        elif evt.severity >= SEVERITY_ERROR:
            alertDetails['message_type'] = 'CRITICAL'
        elif evt.severity == SEVERITY_WARNING:
            alertDetails['message_type'] = 'WARNING'
        else:
            alertDetails['message_type'] = 'INFO'

        eventKey = alertDetails.get('zen_component', alertDetails.get('zen_event_key',''))
        hostName = alertDetails.get('host_name','')

        alertDetails['entity_id'] = '%s|%s|%s' % ( hostName, eventKey, evt.eventClass )
        alertDetails['entity_display_name'] = '%s - %s - %s' % ( hostName, eventKey, evt.eventClass )

        alertDetails['VO_ORGANIZATION_KEY'] = notification.content['api_key']
        alertDetails['VO_ROUTING_KEY'] = notification.content['routing_key']
        alertDetails['monitor_name'] = notification.content.get('monitor_name', '')

        headers = {'Content-Type': 'application/json'}
        body = json.dumps(alertDetails)
        req = urllib2.Request(url=api_url, data=body, headers={'Content-Type': 'application/json'})
        log.debug(body)

        try:
            r = requests.post(url=api_url, data=body, headers={'Content-Type': 'application/json'})
        except requests.exceptions.RequestException as e:
            err = "Failed to send alert to VictorOps: %s" % e
            log.warn(err)
            raise ActionExecutionException(err)

    def updateContent(self, content=None, data=None):
        content['api_key'] = data.get('api_key')
        content['routing_key'] = data.get('routing_key')
        content['monitor_name'] = data.get('monitor_name')
        content['additional_settings'] = data.get('additional_settings')
