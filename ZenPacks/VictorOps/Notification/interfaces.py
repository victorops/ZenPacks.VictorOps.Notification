#//==========================================================================//
#//          Copyright 2014-2015 VictorOps, Inc. All Rights Reserved         //
#//                                                                          //
#//                 PROPRIETARY AND CONFIDENTIAL INFORMATION                 //
#// The information contained herein is the proprietary and confidential     //
#// property of VictorOps, Inc. and may not be used, distributed, modified,  //
#// disclosed or reproduced without the express written permission of        //
#// VictorOps, Inc.                                                          //
#//==========================================================================//

import Globals

from Products.Zuul.form import schema
from Products.Zuul.utils import ZuulMessageFactory as _t
from Products.Zuul.interfaces import IInfo

class IVictorOpsEnqueueContentInfo(IInfo):

    api_key = schema.TextLine(
        title       = _t(u'API Key'),
        description = _t(u'Your VictorOps key for the Zenoss integration.'),
    )

    routing_key = schema.TextLine(
        title       = _t(u'Routing Key'),
        description = _t(u'Used by VictorOps to route the incident to the appropriate team.'),
        default = u''
    )

    monitor_name = schema.TextLine(
        title       = _t(u'Monitor Name'),
        description = _t(u'Used by VictorOps to uniquely identify this Zenoss host.'),
        default = u''
    )

    additional_settings = schema.TextLine(
        title       = _t(u'Additional settings'),
        description = _t(u'Advanced settings. Contact VictorOps for more information.'),
        default = u''
    )
