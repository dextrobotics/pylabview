# -*- coding: utf-8 -*-

""" LabView RSRC file format common classes.

    Classes used in various parts of the RSRC file.
"""

# Copyright (C) 2019 Mefistotelis <mefistotelis@gmail.com>
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


import enum

from hashlib import md5
from io import BytesIO
from types import SimpleNamespace
from ctypes import *

from LVmisc import *
from LVblock import *
import LVconnector

class LVObject:
    def __init__(self, vi, po):
        """ Creates new object.
        """
        self.vi = vi
        self.po = po

    def parseRSRCData(self, bldata):
        """ Parses binary data chunk from RSRC file.

        Receives file-like block data handle positioned at place to read.
        Parses the binary data, filling properties of self.
        """
        pass

    def prepareRSRCData(self, avoid_recompute=False):
        """ Fills binary data chunk for RSRC file which is associated with the connector.

        Must create byte buffer of the whole data for this object.
        """
        data_buf = b''
        return data_buf

    def expectedRSRCSize(self):
        """ Returns data size expected to be returned by prepareRSRCData().
        """
        exp_whole_len = 0
        return exp_whole_len

    def initWithXML(self, obj_elem):
        """ Parses XML branch to fill properties of the object.

        Receives ElementTree branch starting at tag associated with the connector.
        Parses the XML attributes, filling properties of this object.
        """
        pass

    def exportXML(self, obj_elem, fname_base):
        """ Fills XML branch with properties of the object.

        Receives ElementTree branch starting at tag associated with the connector.
        Sets the XML attributes, using properties from this object.
        """
        pass


class LVPath1(LVObject):
    """ Path object ver 1 and 2
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.content = []
        self.ident = b''
        self.tpident = b''

    def parseRSRCData(self, bldata):
        self.ident = bldata.read(4)
        totlen = int.from_bytes(bldata.read(4), byteorder='big', signed=False)
        self.tpident = bldata.read(4) # one of 'unc ', '!pth', 'abs ', 'rel '
        donelen = 4
        self.content = []
        while (donelen < totlen):
            text_len = int.from_bytes(bldata.read(2), byteorder='big', signed=False)
            text_val = bldata.read(text_len)
            self.content.append(text_val)
            donelen += 2+text_len
        if donelen != totlen:
            eprint("{:s}: Warning: LVPath1 has unexpected size, {} != {}"\
              .format(self.vi.src_fname, donelen, totlen))
        pass

    def prepareRSRCData(self, avoid_recompute=False):
        data_buf = bytes(self.ident)[0:4]
        totlen = 4 + sum(2+len(text_val) for text_val in self.content)
        data_buf += int(totlen).to_bytes(4, byteorder='big')
        data_buf += bytes(self.tpident)[0:4]
        for text_val in self.content:
            data_buf += len(text_val).to_bytes(2, byteorder='big')
            data_buf += bytes(text_val)
        return data_buf

    def expectedRSRCSize(self):
        exp_whole_len = 4 + 4 + 4
        exp_whole_len += sum(2+len(text_val) for text_val in self.content)
        return exp_whole_len

    def initWithXML(self, obj_elem):
        self.content = []
        self.ident = getRsrcTypeFromPrettyStr(obj_elem.get("Ident"))
        self.tpident = obj_elem.get("TpIdent").encode(encoding='ascii')
        for i, subelem in enumerate(obj_elem):
            if (subelem.tag == "String"):
                if subelem.text is not None:
                    self.content.append(subelem.text.encode(self.vi.textEncoding))
                else:
                    self.content.append(b'')
            else:
                raise AttributeError("LVPath1 subtree contains unexpected tag")
        pass

    def exportXML(self, obj_elem, fname_base):
        obj_elem.set("Ident",  getPrettyStrFromRsrcType(self.ident))
        obj_elem.set("TpIdent",  self.tpident.decode(encoding='ascii'))
        for text_val in self.content:
            subelem = ET.SubElement(obj_elem,"String")

            pretty_string = text_val.decode(self.vi.textEncoding)
            subelem.text = pretty_string
        pass


class LVPath0(LVObject):
    """ Path object, sometimes used instead of simple file name
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.tpval = 0
        self.content = []
        self.ident = b''

    def parseRSRCData(self, bldata):
        self.ident = bldata.read(4)
        totlen = int.from_bytes(bldata.read(4), byteorder='big', signed=False)
        # seen only 0, though can be 0..3; for non-zero, list of strings is missing (?)
        self.tpval = int.from_bytes(bldata.read(2), byteorder='big', signed=False)
        count = int.from_bytes(bldata.read(2), byteorder='big', signed=False)
        self.content = []
        for i in range(count):
            text_len = int.from_bytes(bldata.read(1), byteorder='big', signed=False)
            text_val = bldata.read(text_len)
            self.content.append(text_val)
        ctlen = 4 + sum(1+len(text_val) for text_val in self.content)
        if ctlen != totlen:
            eprint("{:s}: Warning: LVPath0 has unexpected size, {} != {}"\
              .format(self.vi.src_fname, ctlen, totlen))
        pass

    def prepareRSRCData(self, avoid_recompute=False):
        data_buf = bytes(self.ident)
        totlen = 4 + sum(1+len(text_val) for text_val in self.content)
        data_buf += int(totlen).to_bytes(4, byteorder='big')
        data_buf += int(self.tpval).to_bytes(2, byteorder='big')
        data_buf += len(self.content).to_bytes(2, byteorder='big')
        for text_val in self.content:
            data_buf += len(text_val).to_bytes(1, byteorder='big')
            data_buf += bytes(text_val)
        return data_buf

    def expectedRSRCSize(self):
        exp_whole_len = 4 + 4 + 2 + 2
        exp_whole_len += sum(1+len(text_val) for text_val in self.content)
        return exp_whole_len

    def initWithXML(self, obj_elem):
        self.content = []
        self.ident = getRsrcTypeFromPrettyStr(obj_elem.get("Ident"))
        self.tpval = int(obj_elem.get("TpVal"), 0)
        for i, subelem in enumerate(obj_elem):
            if (subelem.tag == "String"):
                if subelem.text is not None:
                    self.content.append(subelem.text.encode(self.vi.textEncoding))
                else:
                    self.content.append(b'')
            else:
                raise AttributeError("LVPath0 subtree contains unexpected tag")
        pass

    def exportXML(self, obj_elem, fname_base):
        obj_elem.set("Ident",  getPrettyStrFromRsrcType(self.ident))
        obj_elem.set("TpVal",  "{:d}".format(self.tpval))
        for text_val in self.content:
            subelem = ET.SubElement(obj_elem,"String")

            pretty_string = text_val.decode(self.vi.textEncoding)
            subelem.text = pretty_string
        pass


class LVVariant(LVObject):
    """ Object with variant type data
    """
    def __init__(self, index, *args):
        super().__init__(*args)
        self.clients2 = []
        self.varver = 0x0
        self.hasvaritem2 = 0
        self.varitem2 = None
        self.index = index

    def parseRSRCTypeDef(self, bldata, pos):
        bldata.seek(pos)
        obj_type, obj_flags, obj_len = LVconnector.ConnectorObject.parseRSRCDataHeader(bldata)
        if (self.po.verbose > 2):
            print("{:s}: Object {:d} sub {:d}, at 0x{:04x}, type 0x{:02x} flags 0x{:02x} len {:d}"\
              .format(self.vi.src_fname, self.index, len(self.clients2), pos, obj_type, obj_flags, obj_len))
        if obj_len < 4:
            eprint("{:s}: Warning: Object {:d} type 0x{:02x} data size {:d} too small to be valid"\
              .format(self.vi.src_fname, len(self.clients2), obj_type, obj_len))
            obj_type = LVconnector.CONNECTOR_FULL_TYPE.Void
        obj = LVconnector.newConnectorObject(self.vi, -1, obj_flags, obj_type, self.po)
        client = SimpleNamespace()
        client.flags = 0
        client.index = -1
        client.nested = obj
        self.clients2.append(client)
        bldata.seek(pos)
        obj.initWithRSRC(bldata, obj_len)
        return obj.index, obj_len

    def parseRSRCVariant(self, bldata):
        varver = int.from_bytes(bldata.read(4), byteorder='big', signed=False)
        self.varver = varver
        varcount = int.from_bytes(bldata.read(4), byteorder='big', signed=False)
        if varcount > self.po.connector_list_limit:
            eprint("{:s}: Warning: LVVariant {:d} has {:d} clients; truncating"\
              .format(self.vi.src_fname, self.index, varcount))
            varcount = self.po.connector_list_limit
        pos = bldata.tell()
        for i in range(varcount):
            obj_idx, obj_len = self.parseRSRCTypeDef(bldata, pos)
            pos += obj_len
            if obj_len < 4:
                eprint("{:s}: Warning: LVVariant {:d} data size too small for all clients"\
                  .format(self.vi.src_fname, self.index))
                break
        hasvaritem2 = readVariableSizeFieldU2p2(bldata)
        self.hasvaritem2 = hasvaritem2
        self.varitem2 = b''
        if hasvaritem2 != 0:
            self.varitem2 = bldata.read(6)
        pass

    def parseRSRCData(self, bldata):
        self.clients2 = []
        self.varitem2 = None
        self.parseRSRCVariant(bldata)
        pass

    def prepareRSRCData(self, avoid_recompute=False):
        data_buf = int(self.varver).to_bytes(4, byteorder='big')
        varcount = sum(1 for client in self.clients2 if client.index == -1)
        data_buf += int(varcount).to_bytes(4, byteorder='big')
        for client in self.clients2:
            if client.index != -1:
                continue
            client.nested.updateData(avoid_recompute=avoid_recompute)
            data_buf += client.nested.raw_data
        hasvaritem2 = self.hasvaritem2
        data_buf += int(hasvaritem2).to_bytes(2, byteorder='big')
        if hasvaritem2 != 0:
            data_buf += self.varitem2
        return data_buf

    def expectedRSRCSize(self):
        exp_whole_len = 4 + 4
        for client in self.clients2:
            if client.index != -1:
                continue
            exp_whole_len += client.nested.expectedRSRCSize()
        exp_whole_len += 2
        if self.hasvaritem2 != 0:
            exp_whole_len += len(self.varitem2)
        return exp_whole_len

    def initWithXML(self, obj_elem):
        self.varver = int(obj_elem.get("VarVer"), 0)
        self.hasvaritem2 = int(obj_elem.get("HasVarItem2"), 0)
        varitem2 = obj_elem.get("VarItem2")
        if varitem2 is not None:
            self.varitem2 = bytes.fromhex(varitem2)
        for subelem in obj_elem:
            if (subelem.tag == "DataType"):
                obj_idx = int(subelem.get("Index"), 0)
                obj_type = valFromEnumOrIntString(LVconnector.CONNECTOR_FULL_TYPE, subelem.get("Type"))
                obj_flags = importXMLBitfields(LVconnector.CONNECTOR_FLAGS, subelem)
                obj = LVconnector.newConnectorObject(self.vi, obj_idx, obj_flags, obj_type, self.po)
                # Grow the list if needed (the connectors may be in wrong order)
                client = SimpleNamespace()
                client.flags = 0
                client.index = -1
                client.nested = obj
                self.clients2.append(client)
                # Set connector data based on XML properties
                obj.initWithXML(subelem)
            else:
                raise AttributeError("LVVariant subtree contains unexpected tag")
        pass

    def exportXML(self, obj_elem, fname_base):
        obj_elem.tag = "LVVariant"
        obj_elem.set("VarVer", "0x{:08X}".format(self.varver))
        obj_elem.set("HasVarItem2", "{:d}".format(self.hasvaritem2))
        if self.hasvaritem2 != 0:
            obj_elem.set("VarItem2", "{:s}".format(self.varitem2.hex()))
        idx = -1
        for client in self.clients2:
            if client.index != -1:
                continue
            idx += 1
            fname_cli = "{:s}_{:04d}".format(fname_base, idx)
            subelem = ET.SubElement(obj_elem,"DataType")

            subelem.set("Index", str(idx))
            subelem.set("Type", stringFromValEnumOrInt(LVconnector.CONNECTOR_FULL_TYPE, client.nested.otype))

            client.nested.exportXML(subelem, fname_cli)
            client.nested.exportXMLFinish(subelem)
        pass

class OleVariant(LVObject):
    """ OLE object with variant type data
    """
    def __init__(self, index, *args):
        self.vType = 0
        self.vFlags = 0
        self.dimensions = []
        self.vData = []
        super().__init__(*args)

    @staticmethod
    def vTypeToSize(vType):
        vSize = {
            2:  2,
            18: 2,
            3:  4,
            19: 4,
            4:  4,
            5:  8,
            6:  8,
            7:  8,
            10: 4,
            11: 2,
            16: 1,
            17: 1,
            20: 8,
            21: 8,
            0:  0,
        }.get(vType, 0) # The 0 takes value from array
        return vSize

    def parseRSRCVariant(self, bldata):
        flags = int.from_bytes(bldata.read(2), byteorder='big', signed=False)
        self.vType = flags & 0x1FFF
        self.vFlags = flags & ~0x1FFF
        vSize = OleVariant.vTypeToSize(self.vType)
        self.dimensions = []
        self.vData = []
        if (self.vFlags & 0x2000) != 0:
            ndim = int.from_bytes(bldata.read(2), byteorder='big', signed=False)
            totlen = 1
            for i in range(ndim):
                client = SimpleNamespace()
                client.prop1 = int.from_bytes(bldata.read(4), byteorder='big', signed=False)
                client.prop2 = int.from_bytes(bldata.read(4), byteorder='big', signed=False)
                self.dimensions.append(client)
                totlen *= client.prop2
            if ndim == 0: totlen = 0
        else:
            totlen = 1

        if self.vType == 8:
            for i in range(totlen):
                itmlen = int.from_bytes(bldata.read(4), byteorder='big', signed=False)
                client = SimpleNamespace()
                client.data = bldata.read(2*itmlen)
                self.vData.append(client)
        elif self.vType == 12:
            for i in range(totlen):
                # Getting recursive
                client = SimpleNamespace()
                client.obj = LVclasses.OleVariant(0, self.vi, self.po)
                client.obj.parseRSRCData(bldata)
                self.vData.append(client)
        else:
            for i in range(totlen):
                client = SimpleNamespace()
                client.data = bldata.read(vSize)
                self.vData.append(client)
        pass

    def parseRSRCData(self, bldata):
        self.parseRSRCVariant(bldata)
        pass

