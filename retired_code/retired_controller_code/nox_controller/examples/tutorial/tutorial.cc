#include "component.hh"
#include "config.h"
#include "packet-in.hh"
#include "flow.hh"
#include "assert.hh"
#include "netinet++/ethernetaddr.hh"
#include "netinet++/ethernet.hh"
#include <boost/shared_array.hpp>
#include <boost/bind.hpp>
#ifdef LOG4CXX_ENABLED
#include <boost/format.hpp>
#include "log4cxx/logger.h"
#else
#include "vlog.hh"
#endif

using namespace std;
using namespace vigil;
using namespace vigil::container;

namespace
{
  static Vlog_module lg("tutorial");
 
  /** Learning switch.
   */
  class tutorial
    : public Component 
  {
  public:
    /** Constructor.
     */
    tutorial(const Context* c, const json_object* node)
      : Component(c) 
    { }
    
    /** Configuration.
     * Add handler for packet-in event.
     */
    void configure(const Configuration*) 
    {
      register_handler<Packet_in_event>
	(boost::bind(&tutorial::handle, this, _1));
    }
    
    /** Just simply install.
     */
    void install() 
    {
      lg.dbg(" Install called ");
    }

    /** Function to setup flow.
     */
    void setup_flow(Flow& flow, datapathid datapath_id , 
		    uint32_t buffer_id, uint16_t out_port)
    {
      ofp_flow_mod* ofm;
      size_t size = sizeof *ofm + sizeof(ofp_action_output);
      boost::shared_array<char> raw_of(new char[size]);
      ofm = (ofp_flow_mod*) raw_of.get();

      ofm->header.version = OFP_VERSION;
      ofm->header.type = OFPT_FLOW_MOD;
      ofm->header.length = htons(size);
      ofm->match.wildcards = htonl(0);
      ofm->match.in_port = htons(flow.in_port);
      ofm->match.dl_vlan = flow.dl_vlan;
      memcpy(ofm->match.dl_src, flow.dl_src.octet, sizeof ofm->match.dl_src);
      memcpy(ofm->match.dl_dst, flow.dl_dst.octet, sizeof ofm->match.dl_dst);
      ofm->match.dl_type = flow.dl_type;
      ofm->match.nw_src = flow.nw_src;
      ofm->match.nw_dst = flow.nw_dst;
      ofm->match.nw_proto = flow.nw_proto;
      ofm->match.tp_src = flow.tp_src;
      ofm->match.tp_dst = flow.tp_dst;
      ofm->command = htons(OFPFC_ADD);
      ofm->buffer_id = htonl(buffer_id);
      ofm->idle_timeout = htons(5);
      ofm->hard_timeout = htons(OFP_FLOW_PERMANENT);
      ofm->priority = htons(OFP_DEFAULT_PRIORITY);
      ofp_action_output& action = *((ofp_action_output*)ofm->actions);
      memset(&action, 0, sizeof(ofp_action_output));
      action.type = htons(OFPAT_OUTPUT);
      action.len = htons(sizeof(ofp_action_output));
      action.max_len = htons(0);
      action.port = htons(out_port);
      send_openflow_command(datapath_id, &ofm->header, true);
    }

    /** Function to handle packets.
     * @param datapath_id datapath id of switch
     * @param in_port port packet is received
     * @param buffer_id buffer id of packet
     * @param source source mac address in host order
     * @param destination destination mac address in host order
     */
    void handle_packet(datapathid datapath_id, uint16_t in_port, uint32_t buffer_id, 
		       uint64_t source, uint64_t destination)
    {
      send_openflow_packet(datapath_id, buffer_id, OFPP_FLOOD,
			   in_port, true);
    }

    /** Packet-on handler.
     */
    Disposition handle(const Event& e)
    {
      const Packet_in_event& pi = assert_cast<const Packet_in_event&>(e);
      uint32_t buffer_id = pi.buffer_id;
      Flow flow(pi.in_port, *pi.get_buffer());

      // drop LLDP packets
      if (flow.dl_type == ethernet::LLDP)
        return CONTINUE;

      // pass handle of unicast packet, else flood
      if (!flow.dl_src.is_multicast())
	handle_packet(pi.datapath_id, pi.in_port, buffer_id, 
		      flow.dl_src.hb_long(), flow.dl_dst.hb_long());
      else
	send_openflow_packet(pi.datapath_id, buffer_id, OFPP_FLOOD,
			     pi.in_port, true);
      
      return CONTINUE;
    }
    
  private:
};

REGISTER_COMPONENT(container::Simple_component_factory<tutorial>,
                   tutorial);

} // unnamed namespace
