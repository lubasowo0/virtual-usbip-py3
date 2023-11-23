from construct import *
import socket

USBIPOpHeader = Struct(
    "version" / Short,
    "command" / Short,
    "status" / Int,
)

USBIPDevice = Struct(
    "path" / Padded(256, CString("ascii")),
    "busid" / Padded(32, CString("ascii")),
    "busnum" / Int,
    "devnum" / Int,
    "speed" / Int,
    "idVendor" / Short,
    "idProduct" / Short,
    "bcdDevice" / Short,
    "bDeviceClass" / Byte,
    "bDeviceSubClass" / Byte,
    "bDeviceProtocol" / Byte,
    "bConfigurationValue" / Const(1, Byte),
    "bNumConfigurations" / Const(1, Byte),
    "bNumInterfaces" / Byte,
)

USBIPInterface = Struct(
    "bInterfaceClass" / Byte,
    "bInterfaceSubClass" / Byte,
    "bInterfaceProtocol" / Byte,
    Padding(1),
)

USBIPOpReqDevlist = Struct()

USBIPOpRepDevlist = Struct(
    "version" / Default(Short, 0x111),
    "command" / Const(0x5, Short),
    "status" / Int,
    "num_devices" / Const(1, Int),
    "device" / USBIPDevice,
    "interfaces" / Array(this.device.bNumInterfaces, USBIPInterface),
)

USBIPOpReqImport = Struct(
    "busid" / Padded(32, CString("ascii"))
)

USBIPOpRepImport = Struct(
    "version" / Default(Short, 0x111),
    "command" / Const(0x3, Short),
    "status" / Int,
    "device" / If(this.status == 0, USBIPDevice)
)

UsbSetup = Struct(
    "bmRequestType" / Byte,
    "bRequest" / Byte,
    "wValue" / Int16ul,
    "wIndex" / Int16ul,
    "wLength" / Int16ul,
)

USBIPHeader = Struct(
    "command" / Int,
    "seqnum" / Int,
    "devid" / Int,
    "direction" / Int,
    "ep" / Int,
)

USBIPCmdSubmit = Struct(
    "transfer_flags" / Int,
    "transfer_buffer_length" / Int,
    "start_frame" / Int,
    "number_of_packets" / Int,
    "interval" / Int,
    "setup" / UsbSetup,
    #buffer read at runtime
)

USBIPRetSubmit = Struct(
    "command" / Const(0x3, Int),
    "seqnum" / Int,
    "devid" / Const(0, Int),
    "direction" / Const(0, Int),
    "ep" / Const(0, Int),

    "status" / Int32sb,
    "actual_length" / Int,
    "start_frame" / Const(0, Int),
    "number_of_packets" / Const(0xffffffff, Int),
    "error_count" / Const(0, Int),
    Padding(8),
    #buffer written at runtime
)

USBIPCmdUnlink = Struct(
    "unlink_seqnum" / Int,
    Padding(24),
)

USBIPRetUnlink = Struct(
    "command" / Const(0x4, Int),
    "seqnum" / Int,
    "devid" / Const(0, Int),
    "direction" / Const(0, Int),
    "ep" / Const(0, Int),

    "status" / Int32sb,
    Padding(24),
)


usb_device_descriptor = Struct(
    "bLength" / Const(18, Byte),
    "bDescriptorType" / Const(0x1, Byte),
    "bcdUSB" / Int16ul,
    "bDeviceClass" / Byte,
    "bDeviceSubClass" / Byte,
    "bDeviceProtocol" / Byte,
    "bMaxPacketSize0" / Byte,
    "idVendor" / Int16ul,
    "idProduct" / Int16ul,
    "bcdDevice" / Int16ul,
    "iManufacturer" / Byte,
    "iProduct" / Byte,
    "iSerialNumber" / Byte,
    "bNumConfigurations" / Const(1, Byte),
)

usb_configuration_descriptor = Struct(
    "bLength" / Const(9, Byte),
    "bDescriptorType" / Const(0x2, Byte),
    "wTotalLength" / Int16ul,
    "bNumInterfaces" / Byte,
    "bConfigurationValue" / Const(1, Byte),
    "iConfiguration" / Byte,
    "bmAttributes" / Byte,
    "bMaxPower" / Byte,
)

usb_interface_descriptor = Struct(
    "bLength" / Const(9, Byte),
    "bDescriptorType" / Const(0x4, Byte),
    "bInterfaceNumber" / Byte,
    "bAlternateSetting" / Byte,
    "bNumEndpoints" / Byte,
    "bInterfaceClass" / Byte,
    "bInterfaceSubClass" / Byte,
    "bInterfaceProtocol" / Byte,
    "iInterface" / Byte,
)

usb_endpoint_descriptor = Struct(
    "bLength" / Const(7, Byte),
    "bDescriptorType" / Const(0x5, Byte),
    "bEndpointAddress" / Byte,
    "bmAttributes" / Byte,
    "wMaxPacketSize" / Int16ul,
    "bInterval" / Byte,
)

usb_hid_descriptor = Struct(
    "bLength" / Const(9, Byte),
    "bDescriptorType" / Const(0x21, Byte),
    "bcdHID" / Int16ul,
    "bCountryCode" / Byte,
    "bNumDescriptors" / Byte,
    "bDescriptorType2" / Byte,
    "wDescriptorLength" / Int16ul,
)

class Device:
    def handle_urb(self, urb):
        if urb.ep != 0:
            self.handle_irq(urb)
            return

        req_type = (urb.setup.bmRequestType >> 5) & 0x3
        req = urb.setup.bRequest
        if req_type == 0:
            if req == 0x6:
                self.handle_get_descriptor(urb)
            elif req == 0x9: #set configuartion
                cfg_val = urb.setup.wValue & 0xff
                if cfg_val == 1:
                    urb.respond(0)
                else:
                    urb.respond(-32)
            else:
                print(f"Unhandled bmreqtype {urb.setup.bmRequestType} req {hex(req)}")
                urb.respond(-32)
        else:
            self.handle_control(urb)

    def handle_get_descriptor(self, urb):
        desc_type = urb.setup.wValue >> 8
        desc_index = urb.setup.wValue & 0xff
        wlen = urb.setup.wLength

        if desc_type == 1: #device
            res = usb_device_descriptor.build(self.descriptor)
            res = res[:wlen]
            urb.respond(0, res)
        elif desc_type == 2: #configuartion
            res = b''
            descriptors = {0x4: usb_interface_descriptor, 0x5: usb_endpoint_descriptor, 0x21: usb_hid_descriptor}
            for iface in self.interfaces:
                for desc in iface:
                    res += descriptors[desc["bDescriptorType"]].build(desc)
            res = usb_configuration_descriptor.build(self.configuration | {"wTotalLength": len(res)+9}) + res
            res = res[:wlen]
            urb.respond(0, res)
        elif desc_type == 3: #string
            if wlen < 4:
                urb.respond(-32)
                return
            if desc_index == 0:
                res = Byte.build(4) + Byte.build(0x3) + Int16ul.build(0x0409)
                urb.respond(0, res)
            else:
                if desc_index not in self.strings.keys():
                    urb.respond(-32)
                    return
                res = self.strings[desc_index].encode("utf-16le")
                res = Byte.build(len(res) + 2) + Byte.build(0x3) + res
                res = res[:wlen]
                urb.respond(0, res)
        elif desc_type == 6: #qualifier
            urb.respond(-32)
        elif desc_type == 0x22: #hid
            iface = urb.setup.wIndex & 0xff
            if not hasattr(self, 'hid_descriptors') or iface not in self.hid_descriptors.keys():
                urb.respond(-32)
                return
            hid_desc = self.hid_descriptors[iface]
            if wlen < len(hid_desc):
                urb.respond(-32)
                return
            urb.respond(0, bytes(hid_desc))
        else:
            print("Unhandled descriptor type", desc_type)
            urb.respond(-32)

class Urb:
    def __init__(self, conn, seqnum, direction, ep, setup, data=None):
        self.conn = conn
        self.seqnum = seqnum
        self.direction = direction
        self.ep = ep
        self.setup = setup
        self.data = data

        self.responded = False

    def respond(self, status, data=None):
        assert self.responded == False
        if not data or self.direction != 1:
            data = b''

        res = USBIPRetSubmit.build({
            "seqnum": self.seqnum,
            "status": status,
            "actual_length": len(data),
        })

        self.conn.send(res + data)
        self.responded = True

class Unlink:
    ECONNRESET = -104

    def __init__(self, conn, seqnum, unlink_seqnum):
        self.conn = conn
        self.seqnum = seqnum
        self.unlink_seqnum = unlink_seqnum

        self.responded = False

    def respond(self, status):
        assert self.responded == False

        res = USBIPRetUnlink.build({
            "seqnum": self.seqnum,
            "status": status,
        })

        self.conn.send(res)
        self.responded = True

class Server:
    usbip_dev_data = {
            "path": "/sys/devices/pci0000:00/0000:00:01.2/usb1/1-1",
            "busid": "1-1",
            "busnum": 1,
            "devnum": 2,
            "speed": 2,
    }

    def __init__(self, dev):
        self.device = dev

    def handle_devlist(self, header, body):
        dev = self.device
        res = USBIPOpRepDevlist.build({
            "status": 0,
            "device": self.usbip_dev_data | dev.descriptor | dev.configuration,
            "interfaces": [i[0] for i in dev.interfaces]
        })
        self.conn.send(res)

    def handle_import(self, header, body):
        dev = self.device
        if body.busid == self.usbip_dev_data["busid"]:
            res = USBIPOpRepImport.build({
                "status": 0,
                "device": self.usbip_dev_data | dev.descriptor | dev.configuration,
            })
            self.attached = True
        else:
            res = USBIPOpRepImport.build({"status": 1, "device": None})
        self.conn.send(res)

    def run(self, ip='0.0.0.0', port=3240):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((ip, port))
        s.listen()
        self.attached = False
        while 1:
            self.conn, self.addr = s.accept()
            print('Connection address:', self.addr)
            while 1:
                if not self.attached:
                    data = self.conn.recv(USBIPOpHeader.sizeof(), socket.MSG_WAITALL)
                    if len(data) != USBIPOpHeader.sizeof():
                        break
                    header = USBIPOpHeader.parse(data)

                    commands = {0x8003: USBIPOpReqImport, 0x8005: USBIPOpReqDevlist}
                    cmd = commands[header.command]
                    data = self.conn.recv(cmd.sizeof(), socket.MSG_WAITALL)
                    if len(data) != cmd.sizeof():
                        break
                    body = cmd.parse(data)

                    if header.command == 0x8005:
                        self.handle_devlist(header, body)
                    elif header.command == 0x8003:
                        self.handle_import(header, body)
                    else:
                        assert False
                else:
                    data = self.conn.recv(USBIPHeader.sizeof(), socket.MSG_WAITALL)
                    if len(data) != USBIPHeader.sizeof():
                        return
                    header = USBIPHeader.parse(data)

                    commands = {0x1: USBIPCmdSubmit, 0x2: USBIPCmdUnlink}
                    cmd = commands[header.command]
                    data = self.conn.recv(cmd.sizeof(), socket.MSG_WAITALL)
                    if len(data) != cmd.sizeof():
                        return
                    body = cmd.parse(data)

                    if header.command == 0x1:
                        data = None
                        if header.direction == 0:
                            data = self.conn.recv(body.transfer_buffer_length, socket.MSG_WAITALL)
                            if len(data) != body.transfer_buffer_length:
                                return
                        urb = Urb(
                            conn = self.conn,
                            seqnum = header.seqnum,
                            direction = header.direction,
                            ep = header.ep,
                            setup = body.setup,
                            data = data
                            )
                        self.device.handle_urb(urb)
                    elif header.command == 0x2:
                        unlink = Unlink(
                            conn = self.conn,
                            seqnum = header.seqnum,
                            unlink_seqnum = body.unlink_seqnum
                            )
                        self.device.handle_unlink(unlink)
                    else:
                        assert False

            conn.close()
            self.attached = False
        s.close()
