{
    "DnsDpi": {
        "processor_type": "x86",
        "os": "Linux",
        "os_flavor": "Ubuntu",
        "os_flavor_version": "9.10",
        "software": "python",
        "inline": true,
        "affinity" : false,
        "placement" : "middle",
        "bidirection" : true,
        "stateful": false,
        "triggers": [
            "BadDomainEvent",
            "MultipleBadDomainRequestEvent",
            "DNSPacketSizeEvent",
            "DNSRequestExceedEvent",
            "IllegalDNSServer"
        ]
    }
}
