"""
Custom Star Topology - 1 switch, 4 hosts
Connects to POX controller running on localhost
"""

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class StarTopology(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        for i in range(1, 5):
            host = self.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
            self.addLink(host, s1)

if __name__ == '__main__':
    setLogLevel('info')

    topo = StarTopology()
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633),
        switch=OVSSwitch
    )

    net.start()
    info("\n*** Topology started. Hosts: h1 h2 h3 h4 connected to s1\n")
    info("*** Try: pingall, h1 ping h2, iperf\n")
    CLI(net)
    net.stop()
