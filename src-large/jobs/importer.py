"""Import of partner catalogues."""

import pickle

from lxml import etree


def load_partner_xml(payload: bytes):

    parser = etree.XMLParser(resolve_entities=True, no_network=False)
    return etree.fromstring(payload, parser)


def restore_settings(blob: bytes):

    return pickle.loads(blob)
