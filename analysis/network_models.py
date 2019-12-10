"""Provides a set of network models.

A network model is defined as the estimated round trip time, upstream bandwidth,
and downstream bandwidth. This module defines several different models that
attempt to estimate the behaviour of networks in use by users.
"""

from analysis import simulation

# Estimated size of a http request header in bytes for a HTTP2 request using HPACK.
#
# Based on observing request header sizes for sample requests to a fonts CDN.
#
# This estimate is the steady state size, the size of an average request after
# several previous requests have been made and the header dictionary has been
# populated.
ESTIMATED_HTTP_REQUEST_HEADER_SIZE = 35

# Estimated size of a http response header in bytes for a HTTP2 response using HPACK.
ESTIMATED_HTTP_RESPONSE_HEADER_SIZE = 35

# TODO(garretrieger): populate with some real network models.
BROADBAND = simulation.NetworkModel(
    "broadband",
    rtt=20,  # 40 ms
    bandwidth_up=1250,  # 10 mbps
    bandwidth_down=6250)  # 50 mbps

DIALUP = simulation.NetworkModel(
    "dialup",
    rtt=200,  # 200 ms
    bandwidth_up=7,  # 56 kbps
    bandwidth_down=7)  # 56 kbps
