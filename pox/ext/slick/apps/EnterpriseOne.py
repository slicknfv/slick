#
# This is the policy for the Data Center Network
# Internet-GW  WOC -> Firewall -> IDS -> Server
#
#
# Internet-GW  WOC -> Firewall -> IDS -> AntiVirus -> CPE -> Client
#                       G          G         G
#
#    WOC = Compress -> Encrypt -> Encapsulate
#    WOC = Decapsulate -> Decrypt -> Uncompress
# But assuming a trasnparent WOC we can say
#    WOC = Compress(payload) -> Encrypt(payload)
#    WOC = Decrypt(Payload) -> Decompress(Paoyload)
# 
# An enterprise policy to support Remote Users and Remote offices. Such that incoming 
# traffic from Remote Users and offices is first Decrypted and Decompressed.
# Then it passed through Stateful Firewall -> IDS -> Antivirus -> S
# IG->  Decrypt -> Decompress -> Firewall -> IDS -> LB -> Server
#       E       ->     L      ->   G      ->  E  -> E   -> Destination
#IG <-  Encrypt <- Compress   <- Firewall <- IDS <- Server
#       E      <-    G       <-  G       <-  E
#
# Slick Policy:
# Incoming
# IG -> Decrypt -> Firewall -> Decompress -> IDS -> LB ->  Server
#        E           G            L           E      E
#  Outgoing
# IG <- Encrypt <- Firewall <-  Compress <- IDS <- Server
#        E           G            G          E
#
# Assumption: 
#  Encrypt only encrypts payload after transport layer.
#  Compress only compress payload after transport layer.
#  Firewall is a stateful firewall.
#  LB is application layer 
#  ID is application layer.
#
# Here layers are different. If all the elements worked on the same set of bit ranges and we
# have compressed pattern matching in IDS we can rearrnage the layers like this:
# Incoming
# IG -> Decrypt -> Firewall -> IDS -> LB ->  Decompress -> Server
#        E           G          E      E           L        E
#  Outgoing
# IG <- Encrypt <- Firewall <-  IDS <- Compress <- Server
#        E           G            G       G
# 
# Let's say we want to employ certain set of functions on a given flow. We specifiy the bit ranges
# for each element instnace that it operates on.
# Based ont the bit ranges we re-arrange the elements in the chain using LEG but we first apply i
# consolidate heuristics on all allowed combinations.
#
from slick.Application import Application

class EnterpriseOne(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )
        self.eds = [ ]

    def init(self):
        # Start the first Logger:
        parameters = [{"file_name":"/tmp/Encrypt_log"}, {"file_name":"/tmp/StatefulFirewall_log"}, {"file_name":"/tmp/IDS_log"}, {"file_name":"/tmp/LoadBalancer_log"}]
        controller_params = [{}, {}, {}, {}]
        flow = self.make_wildcard_flow()
        # lets try all the ICMP traffic.
        flow['nw_proto'] = 1

        #self.eds = self.apply_elem( flow, ["crypto_nic", "StatefulFirewall", "Decompress", "IDS", "LoadBalancer"], parameters ) 
        self.eds = self.apply_elem( flow, ["Encrypt", "StatefulFirewall", "IDS","LoadBalancer"], parameters ,controller_params) 
        if(self.check_elems_installed(self.eds)):
            self.installed = True
            print self.__class__.__name__, " application created elements with descs:", self.eds
        else:
            print "Failed to install the ", self.__class__.__name__ ," application."

