"""
Flow Rule Timeout Manager - POX Controller
Project: SDN Mininet - Orange Problem

Features:
- Learning switch behavior
- Installs flows with idle + hard timeout
- Logs flow lifecycle (install + expiry)
- Deterministic behavior for testing/viva
"""

from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
import time

log = core.getLogger()

# ---- TIMEOUT SETTINGS ----
IDLE_TIMEOUT = 10    # expires if no traffic for 10 sec
HARD_TIMEOUT = 30    # expires after 30 sec no matter what
# --------------------------


class TimeoutFlowManager(object):

    def __init__(self, connection):
        self.connection = connection
        self.mac_to_port = {}
        self.flow_install_times = {}

        connection.addListeners(self)
        log.info("Switch connected: %s", dpidToStr(connection.dpid))

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        dpid = dpidToStr(event.connection.dpid)
        in_port = event.port

        src = str(packet.src)
        dst = str(packet.dst)

        # Learn source MAC -> incoming port
        self.mac_to_port[src] = in_port

        log.info("[PacketIn] %s | %s -> %s | in_port=%s",
                 dpid, src, dst, in_port)

        if dst in self.mac_to_port:
            out_port = self.mac_to_port[dst]

            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, in_port)
            msg.command = of.OFPFC_ADD
            msg.idle_timeout = IDLE_TIMEOUT
            msg.hard_timeout = HARD_TIMEOUT
            msg.flags = of.OFPFF_SEND_FLOW_REM
            msg.priority = 1
            msg.actions.append(of.ofp_action_output(port=out_port))
            msg.data = event.ofp

            event.connection.send(msg)

            flow_key = (src, dst)
            self.flow_install_times[flow_key] = time.time()

            log.info("[FlowInstalled] %s -> %s | out_port=%s | idle=%ss | hard=%ss",
                     src, dst, out_port, IDLE_TIMEOUT, HARD_TIMEOUT)

        else:
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            msg.data = event.ofp
            msg.in_port = in_port
            event.connection.send(msg)

            log.info("[Flood] dst=%s unknown -> flooding", dst)

    def _handle_FlowRemoved(self, event):
        reason_map = {
            of.OFPRR_IDLE_TIMEOUT: "IDLE_TIMEOUT",
            of.OFPRR_HARD_TIMEOUT: "HARD_TIMEOUT",
            of.OFPRR_DELETE: "MANUAL_DELETE"
        }

        reason = reason_map.get(event.ofp.reason, "UNKNOWN")

        log.info("=" * 60)
        log.info("FLOW RULE REMOVED")
        log.info("Reason       : %s", reason)
        log.info("Match        : %s", event.ofp.match)
        log.info("Duration     : %s sec", event.ofp.duration_sec)
        log.info("Packets sent : %s", event.ofp.packet_count)
        log.info("Bytes sent   : %s", event.ofp.byte_count)
        log.info("=" * 60)


class TimeoutManagerLauncher(object):

    def __init__(self):
        core.openflow.addListeners(self)

    def _handle_ConnectionUp(self, event):
        log.info("New switch connected -> starting Timeout Manager")
        TimeoutFlowManager(event.connection)


def launch():
    log.info("Flow Rule Timeout Manager starting...")
    log.info("Settings: idle_timeout=%ss | hard_timeout=%ss",
             IDLE_TIMEOUT, HARD_TIMEOUT)
    TimeoutManagerLauncher()
