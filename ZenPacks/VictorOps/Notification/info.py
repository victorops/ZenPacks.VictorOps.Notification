#//==========================================================================//
#//          Copyright 2014-2017 VictorOps, Inc. All Rights Reserved         //
#//                                                                          //
#//                 PROPRIETARY AND CONFIDENTIAL INFORMATION                 //
#// The information contained herein is the proprietary and confidential     //
#// property of VictorOps, Inc. and may not be used, distributed, modified,  //
#// disclosed or reproduced without the express written permission of        //
#// VictorOps, Inc.                                                          //
#//==========================================================================//
import Globals

from zope.interface import implements

from Products.Zuul.infos import InfoBase
from Products.Zuul.infos.actions import (CommandActionContentInfo, ActionFieldProperty)

from ZenPacks.VictorOps.Notification.interfaces import IVictorOpsEnqueueContentInfo

class VictorOpsEnqueueContentInfo(InfoBase):
    implements(IVictorOpsEnqueueContentInfo)

    api_key = ActionFieldProperty(IVictorOpsEnqueueContentInfo, 'api_key')
    routing_key = ActionFieldProperty(IVictorOpsEnqueueContentInfo, 'routing_key')
    monitor_name = ActionFieldProperty(IVictorOpsEnqueueContentInfo, 'monitor_name')
    additional_settings = ActionFieldProperty(IVictorOpsEnqueueContentInfo, 'additional_settings')

