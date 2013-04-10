ctf
===

CTF for HacSoc's CTF event

Things required for a service for this thing:
    1)  Needs to have some kind of vulnerability
    2)  Needs to have a script (separate from service) which supports the following commands:
        i)      'put <host> <secret>':  Plants a secret in the app, returns 0 if success and 1 if fail
        ii)     'get <host> <secret>':  Ensures that a secret X is still in the app
        iii)    'test <host>':  Ensures that host is to spec.

Anything else is FINE.

Still to be done:  implement getting new problems from server, write more problems.
