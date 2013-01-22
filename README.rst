-------------------------------------
Assembla Ticket Migration Tool - ATMT
-------------------------------------

:Author: Conrado Buhrer
:Contact: conrado@buhrer.net
:Revision: $Revision: 001 $
:Date: $Date: Tue Dec 11 13:27:56 BRST 2012
:Copyright: Copyleft
:Tags: Assembla, Tickets

Requirements
------------

This tool was built and tested on Linux, please use a Linux machine!

Python library requirements are listed in `requirements.txt`, this is usually
fed to pip using ::

    $ pip install -r requirements.txt

Features
--------

- Copies tickets from one Assembla space to another.

Execution
---------

To copy tickets, please execute the following on a Linux machine::

    $ python main.py

License
-------

``atmt`` is licensed under a Apache License v2.0 , see ``LICENSE`` for details.

Authors
-------

Assembla's API for ``atmt`` is based `Tweepy`. This project was realized by
`Conrado Buhrer`_.

.. _`Conrado Buhrer`: http://github.com/conrado
