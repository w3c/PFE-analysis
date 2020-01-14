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

# Mobile 2G

MOBILE_2G_SLOWEST = simulation.NetworkModel("mobile_2g_slowest",
                                            rtt=10000,
                                            bandwidth_up=4,
                                            bandwidth_down=4)

MOBILE_2G_SLOW = simulation.NetworkModel("mobile_2g_slow",
                                         rtt=4500,
                                         bandwidth_up=6,
                                         bandwidth_down=6)

MOBILE_2G_MEDIAN = simulation.NetworkModel("mobile_2g_median",
                                           rtt=2750,
                                           bandwidth_up=9,
                                           bandwidth_down=9)

MOBILE_2G_FAST = simulation.NetworkModel("mobile_2g_fast",
                                         rtt=1500,
                                         bandwidth_up=19,
                                         bandwidth_down=19)

MOBILE_2G_FASTEST = simulation.NetworkModel("mobile_2g_fastest",
                                            rtt=125,
                                            bandwidth_up=200,
                                            bandwidth_down=200)

# Mobile 3G

MOBILE_3G_SLOWEST = simulation.NetworkModel("mobile_3g_slowest",
                                            rtt=2750,
                                            bandwidth_up=13,
                                            bandwidth_down=13)

MOBILE_3G_SLOW = simulation.NetworkModel("mobile_3g_slow",
                                         rtt=550,
                                         bandwidth_up=50,
                                         bandwidth_down=50)

MOBILE_3G_MEDIAN = simulation.NetworkModel("mobile_3g_median",
                                           rtt=300,
                                           bandwidth_up=156,
                                           bandwidth_down=156)

MOBILE_3G_FAST = simulation.NetworkModel("mobile_3g_fast",
                                         rtt=175,
                                         bandwidth_up=219,
                                         bandwidth_down=219)

MOBILE_3G_FASTEST = simulation.NetworkModel("mobile_3g_fastest",
                                            rtt=115,
                                            bandwidth_up=750,
                                            bandwidth_down=750)

# Mobile 4G

MOBILE_4G_SLOWEST = simulation.NetworkModel("mobile_4g_slowest",
                                            rtt=650,
                                            bandwidth_up=47,
                                            bandwidth_down=47)

MOBILE_4G_SLOW = simulation.NetworkModel("mobile_4g_slow",
                                         rtt=225,
                                         bandwidth_up=181,
                                         bandwidth_down=181)

MOBILE_4G_MEDIAN = simulation.NetworkModel("mobile_4g_median",
                                           rtt=150,
                                           bandwidth_up=238,
                                           bandwidth_down=238)

MOBILE_4G_FAST = simulation.NetworkModel("mobile_4g_fast",
                                         rtt=110,
                                         bandwidth_up=750,
                                         bandwidth_down=750)

MOBILE_4G_FASTEST = simulation.NetworkModel("mobile_4g_fastest",
                                            rtt=70,
                                            bandwidth_up=2250,
                                            bandwidth_down=2250)

# Mobile WiFI

MOBILE_WIFI_SLOWEST = simulation.NetworkModel("mobile_wifi_slowest",
                                              rtt=500,
                                              bandwidth_up=100,
                                              bandwidth_down=100)

MOBILE_WIFI_SLOW = simulation.NetworkModel("mobile_wifi_slow",
                                           rtt=170,
                                           bandwidth_up=200,
                                           bandwidth_down=200)

MOBILE_WIFI_MEDIAN = simulation.NetworkModel("mobile_wifi_median",
                                             rtt=115,
                                             bandwidth_up=563,
                                             bandwidth_down=563)

MOBILE_WIFI_FAST = simulation.NetworkModel("mobile_wifi_fast",
                                           rtt=65,
                                           bandwidth_up=1250,
                                           bandwidth_down=1250)

MOBILE_WIFI_FASTEST = simulation.NetworkModel("mobile_wifi_fastest",
                                              rtt=35,
                                              bandwidth_up=3438,
                                              bandwidth_down=3438)

# Desktop

DESKTOP_SLOWEST = simulation.NetworkModel("desktop_slowest",
                                          rtt=350,
                                          bandwidth_up=125,
                                          bandwidth_down=125)

DESKTOP_SLOW = simulation.NetworkModel("desktop_slow",
                                       rtt=150,
                                       bandwidth_up=313,
                                       bandwidth_down=313)

DESKTOP_MEDIAN = simulation.NetworkModel("desktop_median",
                                         rtt=80,
                                         bandwidth_up=938,
                                         bandwidth_down=938)

DESKTOP_FAST = simulation.NetworkModel("desktop_fast",
                                       rtt=50,
                                       bandwidth_up=2188,
                                       bandwidth_down=2188)

DESKTOP_FASTEST = simulation.NetworkModel("desktop_fastest",
                                          rtt=20,
                                          bandwidth_up=7500,
                                          bandwidth_down=7500)
