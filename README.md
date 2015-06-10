This is a command-line tool for interacting with CloudFlare accounts.

Here's a demo of linking your account, and then adding and editing a domain:

    $ alias flare='python3 -m flare'

    $ flare -a username email@example.com apikeydf545e821dac3c82e33ef356fa51a84
    Account example, email=email@example.com
    Zones:
     - example.com
    Stored!

    $ flare example.com dns -l
    Type  Name      Location         SSL TTL  Pri Cloud
    ----- --------- ---------------- --- ---- --- -----
    A     @         172.28.47.50     on  auto     on
    A     www       172.28.47.50     on  auto     on
    CNAME something elsewhere.com    on  auto     off
    MX    @         mx2.zohomail.com off auto 20  can't
    MX    @         mx.zohomail.com  off auto 10  can't

    $ flare example.com dns -a --name testbed --location 172.31.146.114
    Added record.
    Type Name    Location       SSL TTL  Pri Cloud
    ---- ------- -------------- --- ---- --- -----
    A    testbed 172.31.146.114 on  auto     off

    $ flare example.com dns -l
    Type  Name      Location         SSL TTL  Pri Cloud
    ----- --------- ---------------- --- ---- --- -----
    A     @         172.28.47.50     on  auto     on
    A     testbed   172.31.146.114   on  auto     off
    A     www       172.28.47.50     on  auto     on
    CNAME something elsewhere.com    on  auto     off
    MX    @         mx2.zohomail.com off auto 20  can't
    MX    @         mx.zohomail.com  off auto 10  can't

    $ flare example.com dns -e testbed --cloud on
    Updated 1 records.
    Type Name    Location       SSL TTL  Pri Cloud
    ---- ------- -------------- --- ---- --- -----
    A    testbed 172.31.146.114 on  auto     on

    $ flare example.com level help
    Current level: Low
    New level: I'm under attack!
