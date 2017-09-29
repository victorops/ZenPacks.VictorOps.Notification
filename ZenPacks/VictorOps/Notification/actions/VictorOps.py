#//==========================================================================//
#//          Copyright 2014-2017 VictorOps, Inc. All Rights Reserved         //
#//                                                                          //
#//                 PROPRIETARY AND CONFIDENTIAL INFORMATION                 //
#// The information contained herein is the proprietary and confidential     //
#// property of VictorOps, Inc. and may not be used, distributed, modified,  //
#// disclosed or reproduced without the express written permission of        //
#// VictorOps, Inc.                                                          //
#//==========================================================================//
import os
import re
from time import time, strftime
import tempfile
import json
import logging
import Globals
from zope.interface import implements
from Products.ZenUtils.guid.guid import GUIDManager
from Products.ZenModel.interfaces import IAction
from Products.ZenModel.actions import IActionBase, ActionExecutionException, _signalToContextDict

from ZenPacks.VictorOps.Notification.lib.VictorOps import sendVOAlert

from zenoss.protocols.protobufs.zep_pb2 import (
    SEVERITY_CLEAR, SEVERITY_INFO, SEVERITY_DEBUG,
    SEVERITY_WARNING, SEVERITY_ERROR, SEVERITY_CRITICAL,
    STATUS_NEW, STATUS_ACKNOWLEDGED, STATUS_SUPPRESSED, STATUS_CLOSED,
    STATUS_CLEARED, STATUS_DROPPED, STATUS_AGED
)
# SEVERITY_CLEAR = 0;
# SEVERITY_DEBUG = 1;
# SEVERITY_INFO = 2;
# SEVERITY_WARNING = 3;
# SEVERITY_ERROR = 4;
# SEVERITY_CRITICAL = 5;
# STATUS_NEW = 0;
# STATUS_ACKNOWLEDGED = 1;
# STATUS_SUPPRESSED = 2;
# STATUS_CLOSED = 3; // Closed by the user.
# STATUS_CLEARED = 4; // Closed by a matching clear event.
# STATUS_DROPPED = 5; // Dropped via a transform.
# STATUS_AGED = 6; // Closed via automatic aging.

from ZenPacks.VictorOps.Notification.interfaces import IVictorOpsEnqueueContentInfo

log = logging.getLogger("zen.victorops.actions")

def parseKVP(p):
    a = p.partition('=')
    return a[0], a[2]

class VictorOpsEnqueueAction(IActionBase):
    implements(IAction)

    id = 'victorops_enqueue'
    name = 'VictorOps Alert'
    actionContentInfo = IVictorOpsEnqueueContentInfo
    shouldExecuteInBatch = False

    def setupAction(self, dmd):
        self.guidManager = GUIDManager(dmd)

    def execute(self, notification, signal):
        log.debug('---------------------------------------------------------------------')
        log.debug(signal)

        data = _signalToContextDict(signal, '', notification, self.guidManager)
        log.debug(data)
        eventSummary = data['eventSummary']
        evt = data['evt']

        # Early bail out if it looks like this incident has been acked/resolved via VictorOps
        for note in eventSummary.notes:
            if signal.clear and re.match("^RECOVER.*\(via VictorOps\)$", note.message):
                log.info('Not forwarding recovery that originated at VictorOps: %s', note.message)
                return
            if evt.eventState == STATUS_ACKNOWLEDGED and re.match("^ACKNOWLEDGE.*\(via VictorOps\)$", note.message):
                log.info('Not forwarding acknowledgement that originated at VictorOps: %s', note.message)
                return

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

        sendVOAlert(alertDetails)
        log.info(json.dumps(alertDetails))

    def updateContent(self, content=None, data=None):
        content['api_key'] = data.get('api_key')
        content['routing_key'] = data.get('routing_key')
        content['monitor_name'] = data.get('monitor_name')
        content['additional_settings'] = data.get('additional_settings')
